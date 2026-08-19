from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, contains_eager

from backend.api.auth import get_current_user, get_current_user_optional
from backend.api.dependencies import get_db
from backend.api.schemas.internships import InternshipListResponse, InternshipOut, InternshipSort
from backend.models import Company, Internship, SavedInternship, User
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


def _saved_internship_ids(db: Session, user: User | None, internship_ids: list[int]) -> set[int]:
    """IDs (from `internship_ids`) the given user has saved. Empty for
    an anonymous request - never an error (Phase 9, Step 4)."""
    if user is None or not internship_ids:
        return set()
    stmt = select(SavedInternship.internship_id).where(
        SavedInternship.user_id == user.id, SavedInternship.internship_id.in_(internship_ids)
    )
    return set(db.scalars(stmt).all())


@router.get("", response_model=InternshipListResponse, summary="List internships")
def list_internships(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
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
    saved_ids = _saved_internship_ids(db, current_user, [item.id for item in items])

    return InternshipListResponse(
        items=[InternshipOut.model_validate(item).model_copy(update={"is_saved": item.id in saved_ids}) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{internship_id}", response_model=InternshipOut, summary="Get a single internship")
def get_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> InternshipOut:
    stmt = (
        select(Internship)
        .join(Internship.company)
        .options(contains_eager(Internship.company))
        .where(Internship.id == internship_id)
    )
    internship = db.scalars(stmt).unique().one_or_none()
    if internship is None:
        raise HTTPException(status_code=404, detail="Internship not found")
    is_saved = internship_id in _saved_internship_ids(db, current_user, [internship_id])
    return InternshipOut.model_validate(internship).model_copy(update={"is_saved": is_saved})


@router.post("/{internship_id}/save", status_code=status.HTTP_201_CREATED, summary="Save an internship")
def save_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    exists = db.scalar(select(Internship.id).where(Internship.id == internship_id))
    if exists is None:
        raise HTTPException(status_code=404, detail="Internship not found")

    # ON CONFLICT DO NOTHING makes a duplicate save a safe no-op at the
    # database level (the uq_saved_internships_user_internship
    # constraint) rather than something the route has to check for
    # itself with a separate SELECT-then-INSERT (which would race under
    # concurrent requests).
    stmt = (
        pg_insert(SavedInternship)
        .values(user_id=current_user.id, internship_id=internship_id)
        .on_conflict_do_nothing(index_elements=["user_id", "internship_id"])
    )
    db.execute(stmt)
    db.commit()
    return {"saved": True}


@router.delete("/{internship_id}/save", status_code=status.HTTP_204_NO_CONTENT, summary="Unsave an internship")
def unsave_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    db.query(SavedInternship).filter_by(user_id=current_user.id, internship_id=internship_id).delete()
    db.commit()
    # Idempotent either way - removing something that was never saved is
    # not an error (Phase 9, Step 4).
    return Response(status_code=status.HTTP_204_NO_CONTENT)
