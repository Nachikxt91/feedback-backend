"""Authentication service — JWT tokens + bcrypt password hashing.
No external services required (no Redis, no Supabase). Passwords stored
hashed in MongoDB. Runs on free tier."""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import secrets
import logging

from ..config import settings
from ..utils.exceptions import UnauthorizedError, DatabaseError

logger = logging.getLogger(__name__)

# Bcrypt password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(company_id: str, email: str) -> str:
    """Create a JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": company_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns payload or raises."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        company_id: str = payload.get("sub")
        if company_id is None:
            raise UnauthorizedError("Invalid token payload")
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise UnauthorizedError("Invalid or expired token")


def generate_api_key() -> str:
    """Generate a unique API key for a company (used in public review links)"""
    return f"rp_{secrets.token_hex(24)}"


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.companies = db.companies

    async def register_company(self, data: dict) -> dict:
        """Register a new company. Returns the created company document."""
        # Check duplicate email
        existing = await self.companies.find_one({"email": data["email"]})
        if existing:
            raise DatabaseError("A company with this email already exists")

        # Build slug
        from slugify import slugify
        base_slug = slugify(data["name"])
        slug = base_slug
        counter = 1
        while await self.companies.find_one({"slug": slug}):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Hash password
        password_hash = hash_password(data["password"])

        company_doc = {
            "name": data["name"],
            "email": data["email"],
            "password_hash": password_hash,
            "description": data["description"],
            "industry": data["industry"],
            "products": data.get("products", []),
            "slug": slug,
            "api_key": generate_api_key(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await self.companies.insert_one(company_doc)
        company_doc["_id"] = str(result.inserted_id)

        # Remove sensitive field
        company_doc.pop("password_hash", None)

        logger.info(f"Company registered: {company_doc['name']} ({company_doc['email']})")
        return company_doc

    async def authenticate(self, email: str, password: str) -> dict:
        """Verify email + password. Returns company doc + JWT token."""
        company = await self.companies.find_one({"email": email})
        if not company:
            raise UnauthorizedError("Invalid email or password")

        if not verify_password(password, company["password_hash"]):
            raise UnauthorizedError("Invalid email or password")

        company_id = str(company["_id"])
        token = create_access_token(company_id, email)

        # Build safe profile (no password_hash)
        profile = {
            "_id": company_id,
            "name": company["name"],
            "email": company["email"],
            "description": company["description"],
            "industry": company["industry"],
            "products": company["products"],
            "slug": company["slug"],
            "api_key": company["api_key"],
            "created_at": company["created_at"].isoformat(),
        }

        return {"access_token": token, "token_type": "bearer", "company": profile}

    async def get_company_by_id(self, company_id: str) -> Optional[dict]:
        """Fetch company by ObjectId string"""
        try:
            company = await self.companies.find_one({"_id": ObjectId(company_id)})
        except Exception:
            return None
        if company:
            company["_id"] = str(company["_id"])
            company.pop("password_hash", None)
        return company

    async def get_company_by_api_key(self, api_key: str) -> Optional[dict]:
        """Fetch company by its public API key"""
        company = await self.companies.find_one({"api_key": api_key})
        if company:
            company["_id"] = str(company["_id"])
            company.pop("password_hash", None)
        return company

    async def get_company_by_slug(self, slug: str) -> Optional[dict]:
        """Fetch company by URL slug"""
        company = await self.companies.find_one({"slug": slug})
        if company:
            company["_id"] = str(company["_id"])
            company.pop("password_hash", None)
        return company
