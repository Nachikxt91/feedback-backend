"""Admin router — tenant-scoped dashboard endpoints.
All routes require JWT auth and are scoped to the authenticated company."""

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
import logging

from ..schemas import AdminFeedbackResponse, AnalyticsResponse, InsightResponse
from ..services.feedback_service import FeedbackService
from ..services.company_service import CompanyService
from ..services.insight_service import InsightService
from ..database import get_database
from ..dependencies import get_current_company

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/feedbacks",
    response_model=list[AdminFeedbackResponse],
    description="Get all feedbacks for this company with optional filters",
)
async def get_all_feedbacks(
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    category: Optional[str] = Query(None, description="Filter by category"),
    product: Optional[str] = Query(None, description="Filter by product"),
    search: Optional[str] = Query(None, description="Search in review text"),
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = FeedbackService(db)
    return await service.get_all_feedback(
        company_id=company["_id"],
        limit=limit,
        skip=skip,
        sentiment=sentiment,
        category=category,
        product=product,
        search=search,
    )


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    description="Get analytics dashboard data for this company",
)
async def get_analytics(
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = FeedbackService(db)
    return await service.get_analytics(company["_id"])


@router.get(
    "/insights",
    response_model=InsightResponse,
    description="Get AI-generated aggregated insights (cached, or generate fresh)",
)
async def get_insights(
    refresh: bool = Query(False, description="Force regenerate insights"),
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = InsightService(db)

    if not refresh:
        cached = await service.get_cached_insights(company["_id"])
        if cached:
            return InsightResponse(**cached)

    # Generate fresh insights
    company_svc = CompanyService(db)
    ctx = await company_svc.get_company_context(company["_id"])
    result = await service.generate_insights(company["_id"], ctx)
    return InsightResponse(**result)


@router.post(
    "/process-pending",
    description="Trigger background processing for unprocessed reviews",
)
async def process_pending(
    background_tasks: BackgroundTasks,
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    company_svc = CompanyService(db)
    ctx = await company_svc.get_company_context(company["_id"])
    feedback_svc = FeedbackService(db)
    background_tasks.add_task(
        feedback_svc.enrich_unprocessed, company["_id"], ctx, batch_size=20
    )
    return {"message": "Background processing started for pending reviews"}
