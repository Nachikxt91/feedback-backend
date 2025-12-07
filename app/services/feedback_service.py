from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from typing import Optional
import logging
from ..schemas import FeedbackCreate, FeedbackResponse, AdminFeedbackResponse, AnalyticsResponse
from .llm_service import llm_service
from ..utils.exceptions import DatabaseError, LLMServiceError

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.feedbacks
    
    async def create_feedback(self, feedback_data: FeedbackCreate) -> FeedbackResponse:
        """Create new feedback with AI response"""
        try:
            # Generate AI response for user
            ai_response = await llm_service.generate_user_response(
                feedback_data.rating, 
                feedback_data.review
            )
            
            # Prepare document
            document = {
                "rating": feedback_data.rating,
                "review": feedback_data.review,
                "ai_response": ai_response,
                "created_at": datetime.utcnow(),
                "processed": False
            }
            
            # Insert to database
            result = await self.collection.insert_one(document)
            document["_id"] = str(result.inserted_id)
            
            logger.info(f"✅ Feedback created: {document['_id']}")
            return FeedbackResponse(**document)
            
        except LLMServiceError as e:
            logger.error(f"LLM service error: {e}")
            raise
        except Exception as e:
            logger.error(f"Database error creating feedback: {e}")
            raise DatabaseError("Failed to save feedback")
    
    async def get_all_feedback(self, limit: int = 100, skip: int = 0) -> list[AdminFeedbackResponse]:
        """Get all feedback with admin enrichments"""
        try:
            cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
            feedbacks = await cursor.to_list(length=limit)
            
            enriched_feedbacks = []
            for feedback in feedbacks:
                # Process unprocessed feedback
                if not feedback.get("processed", False):
                    await self._enrich_feedback(feedback)
                
                feedback["_id"] = str(feedback["_id"])
                enriched_feedbacks.append(AdminFeedbackResponse(**feedback))
            
            return enriched_feedbacks
            
        except Exception as e:
            logger.error(f"Error fetching feedbacks: {e}")
            raise DatabaseError("Failed to fetch feedbacks")
    
    async def _enrich_feedback(self, feedback: dict):
        """Enrich feedback with AI analysis"""
        try:
            # Generate summary, actions, and sentiment
            summary, actions, sentiment = await asyncio.gather(
                llm_service.generate_summary(feedback["rating"], feedback["review"]),
                llm_service.generate_action_items(feedback["rating"], feedback["review"]),
                llm_service.analyze_sentiment(feedback["review"]),
                return_exceptions=True
            )
            
            # Update document
            await self.collection.update_one(
                {"_id": feedback["_id"]},
                {
                    "$set": {
                        "ai_summary": summary if not isinstance(summary, Exception) else "Error generating summary",
                        "ai_actions": actions if not isinstance(actions, Exception) else "Error generating actions",
                        "sentiment": sentiment if not isinstance(sentiment, Exception) else "Unknown",
                        "processed": True,
                        "processed_at": datetime.utcnow()
                    }
                }
            )
            
            # Update local object
            feedback.update({
                "ai_summary": summary,
                "ai_actions": actions,
                "sentiment": sentiment,
                "processed": True
            })
            
            logger.info(f"✅ Enriched feedback: {feedback['_id']}")
            
        except Exception as e:
            logger.error(f"Error enriching feedback: {e}")
    
    async def get_analytics(self) -> AnalyticsResponse:
        """Generate analytics dashboard data"""
        try:
            pipeline = [
                {
                    "$facet": {
                        "total": [{"$count": "count"}],
                        "avg_rating": [{"$group": {"_id": None, "avg": {"$avg": "$rating"}}}],
                        "distribution": [
                            {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
                            {"$sort": {"_id": 1}}
                        ],
                        "sentiment": [
                            {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
                        ],
                        "latest": [
                            {"$sort": {"created_at": -1}},
                            {"$limit": 1},
                            {"$project": {"created_at": 1}}
                        ]
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(1)
            data = result[0]
            
            return AnalyticsResponse(
                total_feedback=data["total"][0]["count"] if data["total"] else 0,
                average_rating=round(data["avg_rating"][0]["avg"], 2) if data["avg_rating"] else 0.0,
                rating_distribution={item["_id"]: item["count"] for item in data["distribution"]},
                latest_submission=data["latest"][0]["created_at"] if data["latest"] else None,
                sentiment_breakdown={item["_id"]: item["count"] for item in data["sentiment"] if item["_id"]}
            )
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            raise DatabaseError("Failed to generate analytics")

import asyncio
