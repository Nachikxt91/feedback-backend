from fastapi import APIRouter, Depends, HTTPException, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from ..schemas import AdminFeedbackResponse, AnalyticsResponse
from ..services.feedback_service import FeedbackService
from ..database import get_database
from ..config import settings
from ..utils.exceptions import UnauthorizedError

router = APIRouter(prefix="/admin", tags=["Admin"])

async def verify_api_key(x_api_key: str = Header(...)):
    """Dependency for API key authentication"""
    if x_api_key != settings.API_KEY:
        raise UnauthorizedError("Invalid API key")
    return x_api_key

@router.get(
    "/feedbacks",
    response_model=list[AdminFeedbackResponse],
    dependencies=[Depends(verify_api_key)]
)
async def get_all_feedbacks(
    limit: int = 100,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all feedbacks with AI enrichments (Admin only)"""
    service = FeedbackService(db)
    return await service.get_all_feedback(limit=limit, skip=skip)

@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    dependencies=[Depends(verify_api_key)]
)
async def get_analytics(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get analytics dashboard data (Admin only)"""
    service = FeedbackService(db)
    return await service.get_analytics()
