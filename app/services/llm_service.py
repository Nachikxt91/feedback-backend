"""LLM service — context-aware AI analysis using company profile.
Every prompt injects company name, description, industry, and products
so insights are domain-specific, never generic."""

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from ..config import settings
from ..utils.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


def _build_company_block(ctx: dict | None) -> str:
    """Format company context for prompt injection."""
    if not ctx:
        return ""
    products = ", ".join(ctx.get("products", [])) or "Not specified"
    return f"""
=== COMPANY CONTEXT ===
Company: {ctx.get('company_name', 'Unknown')}
Industry: {ctx.get('industry', 'Unknown')}
Description: {ctx.get('company_description', 'N/A')}
Products/Services: {products}
=======================
"""


class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Internal method with retry logic"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise LLMServiceError(f"Failed to generate response: {str(e)}")

    # ── Public review response (shown to the end-user) ──────────────

    async def generate_user_response(
        self, review: str, rating: int | None = None, ctx: dict | None = None
    ) -> str:
        """Generate friendly response for the reviewer."""
        company_block = _build_company_block(ctx)
        rating_line = f"Rating: {rating}/5\n" if rating else ""

        prompt = f"""You are a professional customer service representative for a company.
{company_block}
A customer wrote the following review:
{rating_line}Review: "{review}"

Respond warmly and professionally in 2-3 sentences.
- If the review is positive: Thank them and encourage continued engagement
- If the review is mixed: Acknowledge feedback and show willingness to improve
- If the review is negative: Apologize and show commitment to addressing concerns
- Reference the company or its products/industry where appropriate

Response:"""
        return await self._call_llm(prompt, temperature=0.7)

    # ── Admin enrichment: summary ───────────────────────────────────

    async def generate_summary(
        self, review: str, rating: int | None = None, ctx: dict | None = None
    ) -> str:
        """Generate concise summary for admin dashboard."""
        company_block = _build_company_block(ctx)
        rating_line = f"Rating: {rating}/5\n" if rating else ""

        prompt = f"""Summarize this customer feedback in ONE sentence.
{company_block}
{rating_line}Review: {review}

Summary:"""
        return await self._call_llm(prompt, temperature=0.3)

    # ── Admin enrichment: action items ──────────────────────────────

    async def generate_action_items(
        self, review: str, rating: int | None = None, ctx: dict | None = None
    ) -> str:
        """Generate actionable recommendations based on review + company context."""
        company_block = _build_company_block(ctx)
        rating_line = f"Rating: {rating}/5\n" if rating else ""

        prompt = f"""Based on this customer feedback, suggest 2-3 specific, actionable steps the business should take.
{company_block}
{rating_line}Review: {review}

The actions MUST be specific to this company's industry and products.
Format as a numbered list. Be concrete — no generic advice.

Action Items:"""
        return await self._call_llm(prompt, temperature=0.5)

    # ── Admin enrichment: sentiment ─────────────────────────────────

    async def analyze_sentiment(self, review: str) -> str:
        """Classify sentiment. Returns one of: Positive, Negative, Neutral."""
        prompt = f"""Analyze the sentiment of this review. Respond with ONLY one word: Positive, Negative, or Neutral.

Review: {review}

Sentiment:"""
        sentiment = await self._call_llm(prompt, temperature=0.1)
        # Normalise
        s = sentiment.strip().rstrip(".").capitalize()
        if s not in ("Positive", "Negative", "Neutral"):
            return "Neutral"
        return s

    # ── Admin enrichment: category ──────────────────────────────────

    async def categorize_review(
        self, review: str, ctx: dict | None = None
    ) -> str:
        """Auto-categorise a review into a theme relevant to the company's domain."""
        company_block = _build_company_block(ctx)

        prompt = f"""Categorize this customer review into ONE short category label (1-3 words).
{company_block}
Review: "{review}"

Examples of good categories: Pricing, Product Quality, Customer Support, Delivery, UX/Design, Performance, Safety, Feature Request, General Praise, General Complaint.
Choose a category that fits THIS company's industry.

Category:"""
        cat = await self._call_llm(prompt, temperature=0.2)
        return cat.strip().strip('"').strip("'")[:50]


# Singleton — use directly or instantiate per-request
llm_service = LLMService()
