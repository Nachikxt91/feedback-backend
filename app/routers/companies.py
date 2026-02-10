"""Company router — profile management, settings, API key regeneration."""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from ..schemas import CompanyProfile, CompanyUpdate
from ..services.company_service import CompanyService
from ..database import get_database
from ..dependencies import get_current_company

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Company"])


@router.get(
    "/me",
    response_model=CompanyProfile,
    description="Get current company profile",
)
async def get_profile(
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = CompanyService(db)
    return await service.get_profile(company["_id"])


@router.put(
    "/me",
    response_model=CompanyProfile,
    description="Update company profile (name, description, industry, products)",
)
async def update_profile(
    update_data: CompanyUpdate,
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = CompanyService(db)
    return await service.update_profile(
        company["_id"], update_data.model_dump(exclude_unset=True)
    )


@router.post(
    "/me/regenerate-key",
    description="Generate a new API key (invalidates the old one)",
)
async def regenerate_api_key(
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    service = CompanyService(db)
    new_key = await service.regenerate_api_key(company["_id"])
    return {"api_key": new_key, "message": "API key regenerated. Update your review links."}
