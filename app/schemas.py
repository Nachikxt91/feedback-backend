from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


# ==================== ENUMS ====================

class SentimentEnum(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"
    UNKNOWN = "Unknown"


class ReviewSourceEnum(str, Enum):
    WEB = "web"
    IMPORT_CSV = "import_csv"
    IMPORT_PDF = "import_pdf"


# ==================== AUTH SCHEMAS ====================

class CompanyRegister(BaseModel):
    """Schema for company registration"""
    name: str = Field(..., min_length=2, max_length=200, description="Company name")
    email: str = Field(..., description="Company email for login")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    description: str = Field(..., min_length=20, max_length=2000, description="Detailed company description")
    industry: str = Field(..., min_length=2, max_length=100, description="Industry/domain")
    products: list[str] = Field(default=[], description="List of products/services offered")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Company name cannot be empty")
        return v.strip()

    @field_validator('products')
    @classmethod
    def clean_products(cls, v: list[str]) -> list[str]:
        return [p.strip() for p in v if p.strip()]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Acme Motors",
                "email": "admin@acmemotors.com",
                "password": "securepass123",
                "description": "Acme Motors is a premium automobile company specializing in electric vehicles.",
                "industry": "Automobiles",
                "products": ["Electric Sedan X1", "Hybrid SUV Z5"]
            }
        }
    )


class CompanyLogin(BaseModel):
    """Schema for company login"""
    email: str = Field(..., description="Company email")
    password: str = Field(..., description="Password")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    company: dict


# ==================== COMPANY SCHEMAS ====================

class CompanyProfile(BaseModel):
    """Company profile response"""
    id: str = Field(..., alias="_id")
    name: str
    email: str
    description: str
    industry: str
    products: list[str]
    slug: str
    api_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


class CompanyPublicInfo(BaseModel):
    """Public company info (for review page)"""
    name: str
    industry: str
    products: list[str]
    slug: str


class CompanyUpdate(BaseModel):
    """Schema for updating company profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=2000)
    industry: Optional[str] = Field(None, min_length=2, max_length=100)
    products: Optional[list[str]] = None

    @field_validator('products')
    @classmethod
    def clean_products(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            return [p.strip() for p in v if p.strip()]
        return v


# ==================== REVIEW / FEEDBACK SCHEMAS ====================

class ReviewSubmit(BaseModel):
    """Public review submission (no login required)"""
    review: str = Field(..., min_length=10, max_length=2000, description="Review text")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Optional rating 1-5")
    product: Optional[str] = Field(None, max_length=200, description="Optional product name")

    @field_validator('review')
    @classmethod
    def review_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Review cannot be empty or only whitespace")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "review": "The Electric Sedan X1 has amazing range. Interior could be better.",
                "rating": 4,
                "product": "Electric Sedan X1"
            }
        }
    )


class ReviewResponse(BaseModel):
    """Response after submitting a review"""
    id: str
    ai_response: str
    created_at: datetime


class AdminFeedbackResponse(BaseModel):
    """Full feedback details for admin dashboard"""
    id: str = Field(..., alias="_id")
    rating: Optional[int] = None
    review: str
    product: Optional[str] = None
    category: Optional[str] = None
    ai_response: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_actions: Optional[str] = None
    sentiment: Optional[str] = None
    source: str = "web"
    processed: bool = False
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


# ==================== ANALYTICS SCHEMAS ====================

class AnalyticsResponse(BaseModel):
    """Analytics dashboard data"""
    total_feedback: int
    average_rating: Optional[float] = None
    rating_distribution: dict[str, int]
    category_distribution: dict[str, int]
    product_distribution: dict[str, int]
    sentiment_breakdown: dict[str, int]
    latest_submission: Optional[datetime] = None
    processing_stats: dict[str, int]


# ==================== IMPORT/EXPORT SCHEMAS ====================

class ImportStatusResponse(BaseModel):
    """Status of an import operation"""
    total_reviews: int
    queued: int
    failed: int
    errors: list[str] = []
    message: str


# ==================== INSIGHT SCHEMAS ====================

class InsightResponse(BaseModel):
    """Aggregated AI insights"""
    company_id: str
    top_issues: list[str]
    top_praises: list[str]
    product_breakdown: dict[str, dict]
    priority_actions: list[str]
    overall_summary: str
    generated_at: datetime
    review_count_analyzed: int


# ==================== HEALTH ====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: float
