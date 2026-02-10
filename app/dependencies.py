"""Shared FastAPI dependencies — JWT auth, company resolution."""

from fastapi import Depends, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from .services.auth_service import AuthService, decode_access_token
from .database import get_database
from .utils.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)


async def get_current_company(
    authorization: str = Header(..., description="Bearer <JWT token>"),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """Extract and validate JWT from Authorization header.
    Returns the full company document (without password_hash)."""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Authorization header must start with 'Bearer '")

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)  # raises UnauthorizedError on failure
    company_id = payload["sub"]

    service = AuthService(db)
    company = await service.get_company_by_id(company_id)
    if not company:
        raise UnauthorizedError("Company not found or deleted")

    return company
