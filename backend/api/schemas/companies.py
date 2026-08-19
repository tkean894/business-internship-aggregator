from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from backend.api.schemas.internships import InternshipBrief


class CompanySummary(BaseModel):
    """Company info nested inside an internship response.

    Includes career_url/website_url (not just id/name/slug) so the
    internship detail page can show company links without a second
    API round trip - the ORM object is already fully loaded via
    contains_eager() in routes/internships.py, so this costs nothing extra.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    career_url: str
    website_url: str | None
    industry: str | None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    career_url: str
    website_url: str | None
    industry: str | None
    is_active: bool
    active_internship_count: int


class CompanyListResponse(BaseModel):
    items: list[CompanyOut]
    total: int


class CompanyDetail(CompanyOut):
    """Company info plus its active internships (see routes/companies.py)."""

    internships: list["InternshipBrief"]
