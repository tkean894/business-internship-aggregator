from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.company import Company


class InternshipCategory(str, enum.Enum):
    """Fixed MVP category list. Backed by a Postgres ENUM (internship_category)."""

    PRODUCT_MANAGEMENT = "Product Management"
    BUSINESS_ANALYTICS = "Business Analytics"
    FINANCE = "Finance"
    ACCOUNTING = "Accounting"
    CONSULTING = "Consulting"
    MARKETING = "Marketing"
    OPERATIONS = "Operations"
    SUPPLY_CHAIN = "Supply Chain"
    STRATEGY = "Strategy"
    HUMAN_RESOURCES = "Human Resources"
    SALES = "Sales"
    REAL_ESTATE = "Real Estate"
    OTHER = "Other"


class Internship(Base):
    """A single internship posting, scoped to one company."""

    __tablename__ = "internships"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[InternshipCategory] = mapped_column(
        Enum(
            InternshipCategory,
            name="internship_category",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=InternshipCategory.OTHER,
        server_default=InternshipCategory.OTHER.value,
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Internship", server_default="Internship"
    )
    application_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    application_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # See database/schema.sql "Deduplication Strategy" for why this key
    # is company + normalized(title) + normalized(location), not a raw URL.
    dedupe_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    company: Mapped["Company"] = relationship(back_populates="internships")

    def __repr__(self) -> str:
        return f"<Internship id={self.id} title={self.title!r} company_id={self.company_id}>"
