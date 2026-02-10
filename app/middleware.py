"""Rate limiting middleware for the feedback API"""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict[str, list[datetime]] = defaultdict(list)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, ip: str):
        """Remove requests older than 1 minute"""
        cutoff = datetime.now() - timedelta(minutes=1)
        self.request_counts[ip] = [
            dt for dt in self.request_counts[ip] if dt > cutoff
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/", "/docs", "/openapi.json", "/api/health"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        self._cleanup_old_requests(client_ip)
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait a minute before trying again."
            )
        
        # Record this request
        self.request_counts[client_ip].append(datetime.now())
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        response = await call_next(request)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        return response
