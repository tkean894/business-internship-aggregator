from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.schemas.companies import CompanyDetail, CompanyListResponse, CompanyOut
from backend.api.schemas.internships import InternshipBrief
from backend.models import Company, Internship

router = APIRouter(prefix="/companies", tags=["companies"])


def _active_internship_count_subquery():
    return (
        select(func.count(Internship.id))
        .where(Internship.company_id == Company.id, Internship.is_active.is_(True))
        .correlate(Company)
        .scalar_subquery()
    )


@router.get("", response_model=CompanyListResponse, summary="List companies")
def list_companies(db: Session = Depends(get_db)) -> CompanyListResponse:
    stmt = select(Company, _active_internship_count_subquery().label("active_internship_count")).order_by(Company.name.asc())
    rows = db.execute(stmt).all()

    items = [
        CompanyOut(
            id=company.id,
            name=company.name,
            slug=company.slug,
            career_url=company.career_url,
            website_url=company.website_url,
            industry=company.industry,
            is_active=company.is_active,
            active_internship_count=count,
        )
        for company, count in rows
    ]
    return CompanyListResponse(items=items, total=len(items))


@router.get("/{company_id}", response_model=CompanyDetail, summary="Get a company and its active internships")
def get_company(company_id: int, db: Session = Depends(get_db)) -> CompanyDetail:
    stmt = select(Company, _active_internship_count_subquery().label("active_internship_count")).where(Company.id == company_id)
    row = db.execute(stmt).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    company, active_internship_count = row

    internships_stmt = (
        select(Internship)
        .where(Internship.company_id == company_id, Internship.is_active.is_(True))
        .order_by(Internship.posted_date.desc().nullslast())
    )
    internships = db.scalars(internships_stmt).all()

    return CompanyDetail(
        id=company.id,
        name=company.name,
        slug=company.slug,
        career_url=company.career_url,
        website_url=company.website_url,
        industry=company.industry,
        is_active=company.is_active,
        active_internship_count=active_internship_count,
        internships=[InternshipBrief.model_validate(i) for i in internships],
    )
