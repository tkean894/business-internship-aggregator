from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.models.internship import InternshipCategory

router = APIRouter(prefix="/categories", tags=["categories"])


class CategoriesResponse(BaseModel):
    categories: list[str]


@router.get("", response_model=CategoriesResponse, summary="List available internship categories")
def list_categories() -> CategoriesResponse:
    # Sourced directly from the InternshipCategory enum (backend/models/internship.py)
    # so this can never drift out of sync with what the database actually stores.
    return CategoriesResponse(categories=[category.value for category in InternshipCategory])
