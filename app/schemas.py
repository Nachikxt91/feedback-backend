from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class RatingEnum(int, Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

class FeedbackCreate(BaseModel):
    rating: RatingEnum = Field(..., description="Rating from 1 to 5")
    review: str = Field(..., min_length=10, max_length=1000, description="User review text")
    
    @field_validator('review')
    @classmethod
    def review_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Review cannot be empty or only whitespace")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rating": 5,
                "review": "Great service! Really impressed with the quality."
            }
        }
    )

class FeedbackResponse(BaseModel):
    id: str = Field(..., alias="_id")
    rating: int
    review: str
    ai_response: str
    created_at: datetime
    
    model_config = ConfigDict(populate_by_name=True)

class AdminFeedbackResponse(FeedbackResponse):
    ai_summary: Optional[str] = None
    ai_actions: Optional[str] = None
    sentiment: Optional[str] = None

class AnalyticsResponse(BaseModel):
    total_feedback: int
    average_rating: float
    rating_distribution: dict[int, int]
    latest_submission: Optional[datetime]
    sentiment_breakdown: dict[str, int]
