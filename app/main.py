from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from .config import settings
from .database import db_manager
from .routers.feedback import router as feedback_router
from .routers.admin import router as admin_router
from .routers.auth import router as auth_router
from .routers.companies import router as company_router
from .routers.import_export import router as import_export_router
from .utils.exceptions import FeedbackSystemException, feedback_exception_handler
from .middleware import RateLimitMiddleware, RequestLoggingMiddleware

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Track startup time for health check
startup_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global startup_time
    logger.info("🚀 Starting ReviewPulse AI API...")
    try:
        await db_manager.connect_to_database()
        logger.info("✅ Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    startup_time = time.time()
    logger.info("✅ Application started successfully")
    yield
    
    logger.info("🛑 Shutting down application...")
    await db_manager.close_database_connection()
    logger.info("✅ Application shut down gracefully")

app = FastAPI(
    title="ReviewPulse AI API",
    version="2.0.0",
    description="Multi-tenant AI-powered feedback analysis platform. "
                "Companies sign up, get a public review link, and receive "
                "AI-driven sentiment analysis & actionable business insights.",
    lifespan=lifespan
)

# Middleware (order matters - first added = last executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(RequestLoggingMiddleware)

# Exception handlers
app.add_exception_handler(FeedbackSystemException, feedback_exception_handler)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )

# ── Routers ─────────────────────────────────────────────────────────
# Auth (public — no JWT required)
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# Company profile management (JWT required)
app.include_router(company_router, prefix="/api/company", tags=["Company"])

# Admin dashboard endpoints (JWT required)
app.include_router(admin_router, prefix="/api", tags=["Admin"])

# Import/Export (JWT required)
app.include_router(import_export_router, prefix="/api", tags=["Import/Export"])

# Public-facing review endpoints (no JWT — uses company slug)
app.include_router(feedback_router, prefix="/api", tags=["Reviews"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "ReviewPulse AI API v2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "auth": "/api/auth/register, /api/auth/login",
            "company": "/api/company/me",
            "admin": "/api/admin/feedbacks, /api/admin/analytics, /api/admin/insights",
            "public_review": "/api/review/{company-slug}",
            "import": "/api/import/csv, /api/import/pdf",
            "export": "/api/export/csv, /api/export/json",
        }
    }

def get_uptime() -> float:
    """Get server uptime in seconds"""
    if startup_time:
        return time.time() - startup_time
    return 0.0

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
