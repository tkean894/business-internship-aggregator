from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from backend.models.internship import InternshipCategory


class NormalizedInternship(BaseModel):
    """Standard internship record every company scraper must produce.

    Downstream code (dedupe key computation, database upsert) only ever
    deals with this shape, regardless of how different each company's
    raw career-site data looks. URLs are kept as plain str rather than
    pydantic's HttpUrl type so they can be written straight to the
    database without a str(...) conversion step.
    """

    title: str
    description: str | None = None
    category: InternshipCategory
    location: str | None = None
    employment_type: str = "Internship"
    application_url: str
    source_url: str
    posted_date: date | None = None
    application_deadline: date | None = None
