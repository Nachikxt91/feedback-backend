from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from ..schemas import FeedbackCreate, FeedbackResponse
from ..services.feedback_service import FeedbackService
from ..database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Feedback"])

@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=201,
    description="Submit new feedback"
)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> FeedbackResponse:
    service = FeedbackService(db)
    return await service.create_feedback(feedback)

@router.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy", "service": "feedback-api"}
