from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, contains_eager

from backend.api.dependencies import get_db
from backend.api.schemas.internships import InternshipListResponse, InternshipOut, InternshipSort
from backend.models import Company, Internship
from backend.models.internship import InternshipCategory

router = APIRouter(prefix="/internships", tags=["internships"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

_SORT_COLUMNS = {
    InternshipSort.POSTED_DATE_DESC: Internship.posted_date.desc().nullslast(),
    InternshipSort.LAST_SEEN_DESC: Internship.last_seen_at.desc(),
    InternshipSort.FIRST_SEEN_DESC: Internship.first_seen_at.desc(),
    InternshipSort.COMPANY_NAME_ASC: Company.name.asc(),
    InternshipSort.TITLE_ASC: Internship.title.asc(),
}


def _apply_filters(
    stmt: Select,
    *,
    search: str | None,
    category: InternshipCategory | None,
    company: str | None,
    location: str | None,
    industry: str | None,
    active: bool | None,
) -> Select:
    if active is not None:
        stmt = stmt.where(Internship.is_active == active)
    if category is not None:
        stmt = stmt.where(Internship.category == category)
    if company:
        stmt = stmt.where(Company.name.ilike(f"%{company}%"))
    if location:
        stmt = stmt.where(Internship.location.ilike(f"%{location}%"))
    if industry:
        stmt = stmt.where(Company.industry == industry)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Internship.title.ilike(pattern),
                Internship.description.ilike(pattern),
                Internship.location.ilike(pattern),
                Company.name.ilike(pattern),
            )
        )
    return stmt


@router.get("", response_model=InternshipListResponse, summary="List internships")
def list_internships(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, description="Case-insensitive text search across title, description, location, and company name"),
    category: InternshipCategory | None = Query(default=None, description="Filter by exact category"),
    company: str | None = Query(default=None, description="Filter by company name (partial match)"),
    location: str | None = Query(default=None, description="Filter by location (partial match)"),
    industry: str | None = Query(default=None, description="Filter by exact company industry (see GET /companies for available values)"),
    active: bool | None = Query(default=True, description="Filter by active status; defaults to active-only. Pass active=false to see inactive (historical) postings."),
    sort: InternshipSort = Query(default=InternshipSort.POSTED_DATE_DESC, description="Sort order"),
    page: int = Query(default=1, ge=1, description="Page number, starting at 1"),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description=f"Results per page, max {MAX_PAGE_SIZE}"),
) -> InternshipListResponse:
    filter_kwargs = dict(search=search, category=category, company=company, location=location, industry=industry, active=active)

    count_stmt = _apply_filters(select(func.count(Internship.id)).join(Internship.company), **filter_kwargs)
    total = db.scalar(count_stmt) or 0

    data_stmt = (
        select(Internship)
        .join(Internship.company)
        .options(contains_eager(Internship.company))
    )
    data_stmt = _apply_filters(data_stmt, **filter_kwargs)
    data_stmt = data_stmt.order_by(_SORT_COLUMNS[sort], Internship.id.desc())
    data_stmt = data_stmt.offset((page - 1) * page_size).limit(page_size)

    items = db.scalars(data_stmt).unique().all()

    return InternshipListResponse(
        items=[InternshipOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{internship_id}", response_model=InternshipOut, summary="Get a single internship")
def get_internship(internship_id: int, db: Session = Depends(get_db)) -> InternshipOut:
    stmt = (
        select(Internship)
        .join(Internship.company)
        .options(contains_eager(Internship.company))
        .where(Internship.id == internship_id)
    )
    internship = db.scalars(stmt).unique().one_or_none()
    if internship is None:
        raise HTTPException(status_code=404, detail="Internship not found")
    return InternshipOut.model_validate(internship)
