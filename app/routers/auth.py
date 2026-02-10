"""Auth router — company registration and login.
Passwords are bcrypt-hashed and stored in MongoDB. JWT tokens for sessions."""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from ..schemas import CompanyRegister, CompanyLogin, TokenResponse
from ..services.auth_service import AuthService
from ..database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    description="Register a new company and receive JWT + API key",
)
async def register(
    data: CompanyRegister,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = AuthService(db)
    company = await service.register_company(data.model_dump())

    # Auto-login: return token immediately
    login_result = await service.authenticate(data.email, data.password)
    return TokenResponse(**login_result)


@router.post(
    "/login",
    response_model=TokenResponse,
    description="Login with email + password, receive JWT",
)
async def login(
    data: CompanyLogin,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = AuthService(db)
    result = await service.authenticate(data.email, data.password)
    return TokenResponse(**result)
