from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FeedbackSystemException(Exception):
    """Base exception for all custom exceptions"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class LLMServiceError(FeedbackSystemException):
    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(message, status_code=503)

class DatabaseError(FeedbackSystemException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)

class RateLimitExceeded(FeedbackSystemException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)

class UnauthorizedError(FeedbackSystemException):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, status_code=401)

async def feedback_exception_handler(request: Request, exc: FeedbackSystemException):
    """Global exception handler"""
    logger.error(f"Error occurred: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "client": request.client.host
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )