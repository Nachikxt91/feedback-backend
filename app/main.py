from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import os
from .config import settings
from .database import db_manager
from .routers.feedback import router as feedback_router
from .routers.admin import router as admin_router
from .utils.exceptions import FeedbackSystemException, feedback_exception_handler

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting Feedback System API...")
    try:
        await db_manager.connect_to_database()
        logger.info("✅ Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    logger.info("✅ Application started successfully")
    yield
    
    logger.info("🛑 Shutting down application...")
    await db_manager.close_database_connection()
    logger.info("✅ Application shut down gracefully")

app = FastAPI(
    title="Feedback System API",
    version="1.0.0",
    description="Production-grade AI feedback system",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Exception handlers
app.add_exception_handler(FeedbackSystemException, feedback_exception_handler)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )

# Include routers
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Feedback System API v1.0.0",
        "docs": "/docs",
        "health": "/api/feedback/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
