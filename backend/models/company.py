from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.internship import Internship


class Company(Base):
    """A company whose career site is monitored for internship postings."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    career_url: Mapped[str] = mapped_column(Text, nullable=False)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Free-text (not a DB enum - the set of industries is expected to grow
    # organically as companies are added, unlike the fixed internship
    # category taxonomy). Nullable since not-yet-backfilled rows may not
    # have it yet; scrapers set it on every run (see BaseScraper).
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    internships: Mapped[list["Internship"]] = relationship(back_populates="company")

    def __repr__(self) -> str:
        return f"<Company id={self.id} slug={self.slug!r}>"
