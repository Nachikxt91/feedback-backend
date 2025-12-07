from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from ..config import settings
from ..utils.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

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
    
    async def generate_user_response(self, rating: int, review: str) -> str:
        """Generate friendly response for user"""
        prompt = f"""You are a professional customer service representative.
        
A customer gave a {rating}-star rating and wrote: "{review}"

Respond warmly and professionally in 2-3 sentences. 
- If rating is 4-5: Thank them and encourage continued engagement
- If rating is 3: Acknowledge feedback and show willingness to improve
- If rating is 1-2: Apologize and show commitment to addressing concerns

Response:"""
        
        return await self._call_llm(prompt, temperature=0.7)
    
    async def generate_summary(self, rating: int, review: str) -> str:
        """Generate concise summary for admin"""
        prompt = f"""Summarize this customer feedback in ONE sentence:
        
Rating: {rating}/5
Review: {review}

Summary:"""
        
        return await self._call_llm(prompt, temperature=0.3)
    
    async def generate_action_items(self, rating: int, review: str) -> str:
        """Generate actionable recommendations"""
        prompt = f"""Based on this customer feedback, suggest 2-3 specific, actionable steps the business should take:

Rating: {rating}/5
Review: {review}

Format as numbered list. Be specific and actionable.

Action Items:"""
        
        return await self._call_llm(prompt, temperature=0.5)
    
    async def analyze_sentiment(self, review: str) -> str:
        """Analyze sentiment of review"""
        prompt = f"""Analyze the sentiment of this review. Respond with ONLY one word: Positive, Negative, or Neutral.

Review: {review}

Sentiment:"""
        
        sentiment = await self._call_llm(prompt, temperature=0.1)
        return sentiment.strip().capitalize()

llm_service = LLMService()
