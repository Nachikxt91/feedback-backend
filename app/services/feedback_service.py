"""Feedback service — multi-tenant, uses FastAPI BackgroundTasks instead of Celery.
All queries are scoped to company_id. AI enrichment runs in background."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from typing import Optional
import logging

from ..schemas import ReviewSubmit, ReviewResponse, AdminFeedbackResponse, AnalyticsResponse
from .llm_service import LLMService
from ..utils.exceptions import DatabaseError, LLMServiceError

logger = logging.getLogger(__name__)


class FeedbackService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.feedbacks
        self.llm = LLMService()

    # ── Public review submission ────────────────────────────────────

    async def create_review(
        self,
        company_id: str,
        review_data: ReviewSubmit,
        company_context: dict | None = None,
    ) -> ReviewResponse:
        """Submit a public review. AI response is generated inline (fast).
        Heavy enrichment (summary, actions, sentiment, category) happens in background."""
        try:
            # Quick AI response for the reviewer (inline — user sees it immediately)
            ai_response = await self.llm.generate_user_response(
                review=review_data.review,
                rating=review_data.rating,
                ctx=company_context,
            )

            document = {
                "company_id": ObjectId(company_id),
                "review": review_data.review,
                "rating": review_data.rating,
                "product": review_data.product,
                "category": None,  # set by background enrichment
                "ai_response": ai_response,
                "ai_summary": None,
                "ai_actions": None,
                "sentiment": None,
                "source": "web",
                "processed": False,
                "created_at": datetime.utcnow(),
            }

            result = await self.collection.insert_one(document)
            doc_id = str(result.inserted_id)

            logger.info(f"Review created: {doc_id} for company {company_id}")
            return ReviewResponse(
                id=doc_id,
                ai_response=ai_response,
                created_at=document["created_at"],
            )

        except LLMServiceError:
            raise
        except Exception as e:
            logger.error(f"Error creating review: {e}")
            raise DatabaseError("Failed to save review")

    # ── Background enrichment (called via BackgroundTasks) ──────────

    async def enrich_feedback(self, feedback_id: str, company_context: dict | None = None):
        """Run heavy AI analysis on a single feedback. Called as a background task."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(feedback_id)})
            if not doc or doc.get("processed"):
                return

            review = doc["review"]
            rating = doc.get("rating")

            # Run all AI calls concurrently
            results = await asyncio.gather(
                self.llm.generate_summary(review, rating, company_context),
                self.llm.generate_action_items(review, rating, company_context),
                self.llm.analyze_sentiment(review),
                self.llm.categorize_review(review, company_context),
                return_exceptions=True,
            )

            summary = results[0] if not isinstance(results[0], Exception) else "Error generating summary"
            actions = results[1] if not isinstance(results[1], Exception) else "Error generating actions"
            sentiment = results[2] if not isinstance(results[2], Exception) else "Unknown"
            category = results[3] if not isinstance(results[3], Exception) else "General"

            await self.collection.update_one(
                {"_id": ObjectId(feedback_id)},
                {
                    "$set": {
                        "ai_summary": summary,
                        "ai_actions": actions,
                        "sentiment": sentiment,
                        "category": category,
                        "processed": True,
                        "processed_at": datetime.utcnow(),
                    }
                },
            )
            logger.info(f"Enriched feedback {feedback_id} | Sentiment: {sentiment} | Category: {category}")

        except Exception as e:
            logger.error(f"Background enrichment failed for {feedback_id}: {e}")

    async def enrich_unprocessed(self, company_id: str, company_context: dict | None = None, batch_size: int = 10):
        """Process all unprocessed feedbacks for a company (e.g., after import).
        Runs in background — processes in batches to stay within Groq rate limits."""
        cursor = self.collection.find(
            {"company_id": ObjectId(company_id), "processed": False}
        ).limit(batch_size)
        docs = await cursor.to_list(length=batch_size)

        for doc in docs:
            await self.enrich_feedback(str(doc["_id"]), company_context)
            await asyncio.sleep(0.5)  # respect rate limits on free tier

    # ── Admin: list feedbacks (tenant-scoped) ──────────────────────

    async def get_all_feedback(
        self,
        company_id: str,
        limit: int = 100,
        skip: int = 0,
        sentiment: Optional[str] = None,
        category: Optional[str] = None,
        product: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[AdminFeedbackResponse]:
        """Fetch feedbacks for a company with optional filters."""
        try:
            query: dict = {"company_id": ObjectId(company_id)}
            if sentiment:
                query["sentiment"] = sentiment
            if category:
                query["category"] = category
            if product:
                query["product"] = product
            if search:
                query["review"] = {"$regex": search, "$options": "i"}

            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit)
            )
            feedbacks = await cursor.to_list(length=limit)

            results = []
            for fb in feedbacks:
                fb["_id"] = str(fb["_id"])
                fb.pop("company_id", None)
                results.append(AdminFeedbackResponse(**fb))
            return results

        except Exception as e:
            logger.error(f"Error fetching feedbacks: {e}")
            raise DatabaseError("Failed to fetch feedbacks")

    # ── Admin: analytics (tenant-scoped) ───────────────────────────

    async def get_analytics(self, company_id: str) -> AnalyticsResponse:
        """Aggregated analytics for a single company."""
        try:
            cid = ObjectId(company_id)
            pipeline = [
                {"$match": {"company_id": cid}},
                {
                    "$facet": {
                        "total": [{"$count": "count"}],
                        "avg_rating": [
                            {"$match": {"rating": {"$ne": None}}},
                            {"$group": {"_id": None, "avg": {"$avg": "$rating"}}},
                        ],
                        "rating_dist": [
                            {"$match": {"rating": {"$ne": None}}},
                            {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
                            {"$sort": {"_id": 1}},
                        ],
                        "sentiment": [
                            {"$match": {"sentiment": {"$ne": None}}},
                            {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}},
                        ],
                        "categories": [
                            {"$match": {"category": {"$ne": None}}},
                            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                        ],
                        "products": [
                            {"$match": {"product": {"$ne": None}}},
                            {"$group": {"_id": "$product", "count": {"$sum": 1}}},
                        ],
                        "latest": [
                            {"$sort": {"created_at": -1}},
                            {"$limit": 1},
                            {"$project": {"created_at": 1}},
                        ],
                        "processed_count": [
                            {"$match": {"processed": True}},
                            {"$count": "count"},
                        ],
                        "pending_count": [
                            {"$match": {"processed": False}},
                            {"$count": "count"},
                        ],
                    }
                },
            ]

            result = await self.collection.aggregate(pipeline).to_list(1)
            data = result[0] if result else {}

            total = data.get("total", [{}])[0].get("count", 0) if data.get("total") else 0
            processed = data.get("processed_count", [{}])[0].get("count", 0) if data.get("processed_count") else 0
            pending = data.get("pending_count", [{}])[0].get("count", 0) if data.get("pending_count") else 0

            return AnalyticsResponse(
                total_feedback=total,
                average_rating=round(data["avg_rating"][0]["avg"], 2) if data.get("avg_rating") else None,
                rating_distribution={
                    str(item["_id"]): item["count"] for item in data.get("rating_dist", [])
                },
                sentiment_breakdown={
                    item["_id"]: item["count"] for item in data.get("sentiment", []) if item["_id"]
                },
                category_distribution={
                    item["_id"]: item["count"] for item in data.get("categories", []) if item["_id"]
                },
                product_distribution={
                    item["_id"]: item["count"] for item in data.get("products", []) if item["_id"]
                },
                latest_submission=data["latest"][0]["created_at"] if data.get("latest") else None,
                processing_stats={
                    "processed": processed,
                    "pending": pending,
                    "total": total,
                },
            )

        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            raise DatabaseError("Failed to generate analytics")
