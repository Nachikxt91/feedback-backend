"""Feedback / Review router — public-facing endpoints.
The public review link uses the company slug (no login required).
Health check and company info endpoints are also here."""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import time

from ..schemas import ReviewSubmit, ReviewResponse, CompanyPublicInfo, HealthResponse
from ..services.feedback_service import FeedbackService
from ..services.auth_service import AuthService
from ..services.company_service import CompanyService
from ..database import get_database
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reviews"])


@router.get(
    "/company/{slug}",
    response_model=CompanyPublicInfo,
    description="Get public company info for the review page (name, products, industry)",
)
async def get_company_info(
    slug: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Public endpoint — returns company name + products so the review form can show them."""
    service = AuthService(db)
    company = await service.get_company_by_slug(slug)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyPublicInfo(
        name=company["name"],
        industry=company["industry"],
        products=company.get("products", []),
        slug=company["slug"],
    )


@router.post(
    "/review/{slug}",
    response_model=ReviewResponse,
    status_code=201,
    description="Submit a public review for a company (no login required)",
)
async def submit_review(
    slug: str,
    review: ReviewSubmit,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Public review endpoint. Anyone with the link can submit."""
    auth_service = AuthService(db)
    company = await auth_service.get_company_by_slug(slug)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Build company context for AI
    company_ctx = {
        "company_name": company["name"],
        "company_description": company["description"],
        "industry": company["industry"],
        "products": company.get("products", []),
    }

    feedback_svc = FeedbackService(db)
    result = await feedback_svc.create_review(
        company_id=company["_id"],
        review_data=review,
        company_context=company_ctx,
    )

    # Queue background enrichment (sentiment, summary, actions, category)
    background_tasks.add_task(
        feedback_svc.enrich_feedback, result.id, company_ctx
    )

    return result


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check():
    from ..main import get_uptime
    return HealthResponse(
        status="healthy",
        service="reviewpulse-api",
        version=settings.APP_VERSION,
        uptime_seconds=get_uptime(),
    )
