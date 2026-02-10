"""Insight service — generates aggregated AI insights from recent reviews.
Uses the LLM with full company context. No external queue needed."""

from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from .llm_service import LLMService
from ..utils.exceptions import DatabaseError, LLMServiceError

logger = logging.getLogger(__name__)


class InsightService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.feedbacks = db.feedbacks
        self.insights = db.insights
        self.llm = LLMService()

    async def generate_insights(self, company_id: str, company_context: dict, limit: int = 50) -> dict:
        """Analyse the most recent N reviews and produce aggregated insights.
        Result is cached in the 'insights' collection."""

        # Fetch recent processed reviews
        cursor = self.feedbacks.find(
            {"company_id": ObjectId(company_id), "processed": True}
        ).sort("created_at", -1).limit(limit)
        reviews = await cursor.to_list(length=limit)

        if not reviews:
            return {
                "company_id": company_id,
                "top_issues": [],
                "top_praises": [],
                "product_breakdown": {},
                "priority_actions": [],
                "overall_summary": "No processed reviews available yet.",
                "generated_at": datetime.utcnow(),
                "review_count_analyzed": 0,
            }

        # Build a condensed review block for the LLM
        review_block = ""
        for i, r in enumerate(reviews, 1):
            rating_str = f"Rating: {r.get('rating', 'N/A')}/5" if r.get("rating") else "No rating"
            product_str = f" | Product: {r['product']}" if r.get("product") else ""
            sentiment_str = f" | Sentiment: {r.get('sentiment', 'Unknown')}"
            review_block += f"{i}. [{rating_str}{product_str}{sentiment_str}] {r['review'][:300]}\n"

        # Build the aggregated insight prompt
        products_str = ", ".join(company_context.get("products", [])) or "Not specified"
        prompt = f"""You are a senior business analyst. Analyze the following customer reviews for a company and produce structured insights.

=== COMPANY CONTEXT ===
Company: {company_context['company_name']}
Industry: {company_context['industry']}
Description: {company_context['company_description']}
Products: {products_str}

=== RECENT REVIEWS ({len(reviews)} total) ===
{review_block}

=== TASK ===
Produce a JSON object with these exact keys:
{{
  "top_issues": ["issue1", "issue2", "issue3"],
  "top_praises": ["praise1", "praise2", "praise3"],
  "product_breakdown": {{"product_name": {{"positive": 0, "negative": 0, "key_feedback": "..."}}}},
  "priority_actions": ["action1", "action2", "action3"],
  "overall_summary": "2-3 sentence summary of the feedback landscape"
}}

Rules:
- Be specific to THIS company and industry, not generic
- Reference actual products mentioned in reviews
- Actions must be concrete and implementable
- Respond with ONLY the JSON object, no markdown or explanation"""

        try:
            raw = await self.llm._call_llm(prompt, temperature=0.3)

            # Parse JSON from LLM response
            import json
            # Strip markdown code fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()

            parsed = json.loads(clean)

        except (json.JSONDecodeError, LLMServiceError) as e:
            logger.error(f"Insight generation failed: {e}")
            parsed = {
                "top_issues": ["Unable to generate insights at this time"],
                "top_praises": [],
                "product_breakdown": {},
                "priority_actions": ["Retry insight generation later"],
                "overall_summary": "Insight generation encountered an error. Please try again.",
            }

        insight_doc = {
            "company_id": company_id,
            "top_issues": parsed.get("top_issues", []),
            "top_praises": parsed.get("top_praises", []),
            "product_breakdown": parsed.get("product_breakdown", {}),
            "priority_actions": parsed.get("priority_actions", []),
            "overall_summary": parsed.get("overall_summary", ""),
            "generated_at": datetime.utcnow(),
            "review_count_analyzed": len(reviews),
        }

        # Cache in DB (upsert per company)
        await self.insights.update_one(
            {"company_id": company_id},
            {"$set": insight_doc},
            upsert=True,
        )

        return insight_doc

    async def get_cached_insights(self, company_id: str) -> dict | None:
        """Return previously generated insights if available."""
        doc = await self.insights.find_one({"company_id": company_id})
        if doc:
            doc.pop("_id", None)
        return doc
