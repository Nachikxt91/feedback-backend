"""Import service — parse CSV and PDF files into review documents.
No external queue needed; uses FastAPI BackgroundTasks."""

import csv
import io
import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.feedbacks = db.feedbacks

    async def import_csv(self, company_id: str, file_content: bytes) -> dict:
        """Parse a CSV file and insert reviews.
        Expected columns: review (required), rating (optional), product (optional)
        Returns summary of the import."""
        errors: list[str] = []
        inserted = 0
        total = 0

        try:
            text = file_content.decode("utf-8-sig")  # handles BOM
            reader = csv.DictReader(io.StringIO(text))

            # Normalise column names to lowercase
            docs_to_insert: list[dict] = []

            for row_num, row in enumerate(reader, start=2):  # header is row 1
                total += 1
                # Normalise keys
                norm = {k.strip().lower(): v.strip() for k, v in row.items() if k}

                review_text = norm.get("review") or norm.get("review_text") or norm.get("feedback") or ""
                if len(review_text.strip()) < 10:
                    errors.append(f"Row {row_num}: review too short or missing")
                    continue

                rating_raw = norm.get("rating") or norm.get("stars")
                rating: Optional[int] = None
                if rating_raw:
                    try:
                        rating = int(float(rating_raw))
                        if rating < 1 or rating > 5:
                            rating = None
                    except ValueError:
                        pass

                product = norm.get("product") or norm.get("product_name") or None

                docs_to_insert.append({
                    "company_id": ObjectId(company_id),
                    "review": review_text.strip(),
                    "rating": rating,
                    "product": product,
                    "category": None,
                    "ai_response": None,
                    "ai_summary": None,
                    "ai_actions": None,
                    "sentiment": None,
                    "source": "import_csv",
                    "processed": False,
                    "created_at": datetime.utcnow(),
                })

            if docs_to_insert:
                result = await self.feedbacks.insert_many(docs_to_insert)
                inserted = len(result.inserted_ids)

        except UnicodeDecodeError:
            errors.append("File is not valid UTF-8 text")
        except Exception as e:
            logger.error(f"CSV import error: {e}")
            errors.append(f"Unexpected error: {str(e)}")

        return {
            "total_reviews": total,
            "queued": inserted,
            "failed": total - inserted,
            "errors": errors[:20],  # cap error list
            "message": f"Imported {inserted}/{total} reviews" if total else "No reviews found in file",
        }

    async def import_pdf(self, company_id: str, file_content: bytes) -> dict:
        """Extract text from PDF and split into individual reviews.
        Each paragraph ≥ 10 chars is treated as a separate review."""
        errors: list[str] = []
        inserted = 0

        try:
            import pdfplumber

            pdf_file = io.BytesIO(file_content)
            all_text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"

            if not all_text.strip():
                return {
                    "total_reviews": 0,
                    "queued": 0,
                    "failed": 0,
                    "errors": ["No text could be extracted from the PDF"],
                    "message": "PDF appears to be empty or image-only",
                }

            # Split on double newlines or numbered patterns
            import re
            paragraphs = re.split(r'\n{2,}|\n(?=\d+[\.\)]\s)', all_text)
            reviews = [p.strip() for p in paragraphs if len(p.strip()) >= 10]

            total = len(reviews)
            docs_to_insert = []
            for review_text in reviews:
                docs_to_insert.append({
                    "company_id": ObjectId(company_id),
                    "review": review_text[:2000],  # cap length
                    "rating": None,
                    "product": None,
                    "category": None,
                    "ai_response": None,
                    "ai_summary": None,
                    "ai_actions": None,
                    "sentiment": None,
                    "source": "import_pdf",
                    "processed": False,
                    "created_at": datetime.utcnow(),
                })

            if docs_to_insert:
                result = await self.feedbacks.insert_many(docs_to_insert)
                inserted = len(result.inserted_ids)

        except ImportError:
            errors.append("PDF processing library not available")
        except Exception as e:
            logger.error(f"PDF import error: {e}")
            errors.append(f"PDF parsing error: {str(e)}")

        total = inserted + len(errors)
        return {
            "total_reviews": total,
            "queued": inserted,
            "failed": total - inserted,
            "errors": errors[:20],
            "message": f"Extracted and imported {inserted} reviews from PDF",
        }
