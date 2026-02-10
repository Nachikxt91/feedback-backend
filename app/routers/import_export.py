"""Import/Export router — CSV/PDF import, CSV/JSON export.
Uses FastAPI BackgroundTasks for AI enrichment after import (no Celery/Redis)."""

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
import csv
import io
import json
import logging

from ..schemas import ImportStatusResponse
from ..services.import_service import ImportService
from ..services.feedback_service import FeedbackService
from ..services.company_service import CompanyService
from ..database import get_database
from ..dependencies import get_current_company
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Import/Export"])


@router.post(
    "/import/csv",
    response_model=ImportStatusResponse,
    description="Import reviews from a CSV file. Columns: review (required), rating, product",
)
async def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    # Validate file type
    if not file.filename.lower().endswith(".csv"):
        return ImportStatusResponse(
            total_reviews=0, queued=0, failed=0,
            errors=["File must be a .csv"], message="Invalid file type",
        )

    # Check file size (free tier friendly)
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        return ImportStatusResponse(
            total_reviews=0, queued=0, failed=0,
            errors=[f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"],
            message="File too large",
        )

    service = ImportService(db)
    result = await service.import_csv(company["_id"], content)

    # Queue background AI enrichment for imported reviews
    if result["queued"] > 0:
        company_svc = CompanyService(db)
        ctx = await company_svc.get_company_context(company["_id"])
        feedback_svc = FeedbackService(db)
        background_tasks.add_task(
            feedback_svc.enrich_unprocessed, company["_id"], ctx, batch_size=20
        )

    return ImportStatusResponse(**result)


@router.post(
    "/import/pdf",
    response_model=ImportStatusResponse,
    description="Import reviews from a PDF file. Each paragraph is treated as a review.",
)
async def import_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if not file.filename.lower().endswith(".pdf"):
        return ImportStatusResponse(
            total_reviews=0, queued=0, failed=0,
            errors=["File must be a .pdf"], message="Invalid file type",
        )

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        return ImportStatusResponse(
            total_reviews=0, queued=0, failed=0,
            errors=[f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"],
            message="File too large",
        )

    service = ImportService(db)
    result = await service.import_pdf(company["_id"], content)

    if result["queued"] > 0:
        company_svc = CompanyService(db)
        ctx = await company_svc.get_company_context(company["_id"])
        feedback_svc = FeedbackService(db)
        background_tasks.add_task(
            feedback_svc.enrich_unprocessed, company["_id"], ctx, batch_size=20
        )

    return ImportStatusResponse(**result)


@router.get(
    "/export/csv",
    description="Export all reviews as CSV",
)
async def export_csv(
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    feedback_svc = FeedbackService(db)
    feedbacks = await feedback_svc.get_all_feedback(company["_id"], limit=5000)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "review", "rating", "product", "category", "sentiment",
                     "ai_summary", "ai_actions", "source", "created_at"],
    )
    writer.writeheader()
    for fb in feedbacks:
        writer.writerow({
            "id": fb.id,
            "review": fb.review,
            "rating": fb.rating,
            "product": fb.product,
            "category": fb.category,
            "sentiment": fb.sentiment,
            "ai_summary": fb.ai_summary,
            "ai_actions": fb.ai_actions,
            "source": fb.source,
            "created_at": fb.created_at.isoformat(),
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reviews_export.csv"},
    )


@router.get(
    "/export/json",
    description="Export all reviews as JSON",
)
async def export_json(
    company: dict = Depends(get_current_company),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    feedback_svc = FeedbackService(db)
    feedbacks = await feedback_svc.get_all_feedback(company["_id"], limit=5000)

    data = []
    for fb in feedbacks:
        data.append({
            "id": fb.id,
            "review": fb.review,
            "rating": fb.rating,
            "product": fb.product,
            "category": fb.category,
            "sentiment": fb.sentiment,
            "ai_summary": fb.ai_summary,
            "ai_actions": fb.ai_actions,
            "source": fb.source,
            "created_at": fb.created_at.isoformat(),
        })

    json_str = json.dumps(data, indent=2)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=reviews_export.json"},
    )
