from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.models.base import Base


class ScraperRunStatus(str, enum.Enum):
    """SUCCESS means the scraper's fetch+processing completed without an
    unhandled exception - individual listings can still have been
    skipped/invalid (see error_count) without the run itself failing.
    FAILED means something outside BaseScraper's per-listing isolation
    raised (e.g. the company's API was unreachable after retries)."""

    SUCCESS = "success"
    FAILED = "failed"


class ScraperRun(Base):
    """One row per company scraper invocation - persisted so scraper
    reliability/performance is measurable over time instead of only
    visible in ephemeral logs (Phase 7, Step 8). Not exposed through
    the public API; this is internal operational data."""

    __tablename__ = "scraper_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    scraper_name: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ScraperRunStatus] = mapped_column(
        Enum(
            ScraperRunStatus,
            name="scraper_run_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    raw_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    relevant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    deactivated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Short human-readable summary only (e.g. exception message) - never
    # a full stack trace, and never DATABASE_URL/credentials, which none
    # of BaseScraper's own exception paths ever include in their message.
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ScraperRun id={self.id} company_slug={self.company_slug!r} status={self.status}>"
