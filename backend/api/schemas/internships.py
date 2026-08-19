from __future__ import annotations

import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from backend.api.schemas.companies import CompanySummary
from backend.models.internship import InternshipCategory


class InternshipSort(str, enum.Enum):
    """Controlled list of allowed sort options - never raw user-supplied order-by.

    POSTED_DATE_DESC orders by the source's own posting date (when the
    company said the role went live). FIRST_SEEN_DESC orders by
    `first_seen_at` - when this aggregator first discovered the listing,
    which is not the same thing (see Internship.first_seen_at) and is
    the more honest signal when a source doesn't provide a posting date.
    """

    POSTED_DATE_DESC = "posted_date_desc"
    LAST_SEEN_DESC = "last_seen_desc"
    FIRST_SEEN_DESC = "first_seen_desc"
    COMPANY_NAME_ASC = "company_name_asc"
    TITLE_ASC = "title_asc"


class InternshipOut(BaseModel):
    """Full public internship representation, used for list and detail responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company: CompanySummary
    title: str
    description: str | None
    category: InternshipCategory
    location: str | None
    employment_type: str
    application_url: str
    source_url: str
    posted_date: date | None
    application_deadline: date | None
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool


class InternshipBrief(BaseModel):
    """Trimmed internship representation nested inside a company detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: InternshipCategory
    location: str | None
    employment_type: str
    application_url: str
    posted_date: date | None
    first_seen_at: datetime
    is_active: bool


class InternshipListResponse(BaseModel):
    items: list[InternshipOut]
    total: int
    page: int
    page_size: int


# CompanyDetail.internships references InternshipBrief by forward ref
# (companies.py can't import this module directly - the reverse import
# already runs the other way, above). Resolve it now that InternshipBrief exists.
from backend.api.schemas.companies import CompanyDetail  # noqa: E402

CompanyDetail.model_rebuild()
