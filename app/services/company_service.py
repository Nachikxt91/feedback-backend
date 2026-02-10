"""Company profile management service — CRUD operations for company settings."""

from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from ..utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.companies = db.companies

    async def get_profile(self, company_id: str) -> dict:
        """Get full company profile by ID"""
        try:
            company = await self.companies.find_one({"_id": ObjectId(company_id)})
        except Exception as e:
            logger.error(f"Error fetching company: {e}")
            raise DatabaseError("Failed to fetch company profile")

        if not company:
            raise DatabaseError("Company not found")

        company["_id"] = str(company["_id"])
        company.pop("password_hash", None)
        return company

    async def update_profile(self, company_id: str, update_data: dict) -> dict:
        """Update company profile fields (name, description, industry, products)"""
        # Remove None values
        updates = {k: v for k, v in update_data.items() if v is not None}
        if not updates:
            raise DatabaseError("No fields to update")

        updates["updated_at"] = datetime.utcnow()

        # If name changed, update slug too
        if "name" in updates:
            from slugify import slugify
            base_slug = slugify(updates["name"])
            slug = base_slug
            counter = 1
            while True:
                existing = await self.companies.find_one({
                    "slug": slug,
                    "_id": {"$ne": ObjectId(company_id)}
                })
                if not existing:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1
            updates["slug"] = slug

        try:
            result = await self.companies.update_one(
                {"_id": ObjectId(company_id)},
                {"$set": updates}
            )
            if result.modified_count == 0:
                raise DatabaseError("No changes applied")
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error updating company: {e}")
            raise DatabaseError("Failed to update company profile")

        return await self.get_profile(company_id)

    async def regenerate_api_key(self, company_id: str) -> str:
        """Generate a new API key for the company"""
        from .auth_service import generate_api_key
        new_key = generate_api_key()

        try:
            await self.companies.update_one(
                {"_id": ObjectId(company_id)},
                {"$set": {"api_key": new_key, "updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Error regenerating API key: {e}")
            raise DatabaseError("Failed to regenerate API key")

        logger.info(f"API key regenerated for company {company_id}")
        return new_key

    async def get_company_context(self, company_id: str) -> dict:
        """Get company context for AI prompt injection.
        Returns name, description, industry, products — the fields the LLM needs."""
        company = await self.get_profile(company_id)
        return {
            "company_name": company["name"],
            "company_description": company["description"],
            "industry": company["industry"],
            "products": company.get("products", []),
        }
