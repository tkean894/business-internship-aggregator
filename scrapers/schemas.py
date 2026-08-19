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


def validate_normalized_internship(internship: NormalizedInternship) -> list[str]:
    """Data-quality checks applied before a listing is written to the
    database, on top of what pydantic's type system already guarantees
    (e.g. `category` can only ever be a real InternshipCategory member -
    an invalid value already fails at NormalizedInternship construction,
    inside parse_listing()'s existing try/except). Returns a list of
    human-readable problems; an empty list means the listing is safe to
    upsert. Never raises - a malformed listing should be skipped and
    logged, not crash the run (Phase 7, Step 7)."""
    problems: list[str] = []

    if not internship.title or not internship.title.strip():
        problems.append("title is empty")
    elif len(internship.title) > 500:  # matches internships.title VARCHAR(500)
        problems.append(f"title exceeds 500 characters ({len(internship.title)})")

    if not internship.application_url or not internship.application_url.startswith(("http://", "https://")):
        problems.append(f"application_url is not a valid absolute URL: {internship.application_url!r}")

    if not internship.source_url or not internship.source_url.startswith(("http://", "https://")):
        problems.append(f"source_url is not a valid absolute URL: {internship.source_url!r}")

    if internship.posted_date and internship.application_deadline:
        if internship.application_deadline < internship.posted_date:
            problems.append(
                f"application_deadline ({internship.application_deadline}) is before "
                f"posted_date ({internship.posted_date})"
            )

    return problems
