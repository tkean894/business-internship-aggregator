from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.internship import Internship
    from backend.models.user import User


class NotificationFrequency(str, enum.Enum):
    """How often a user wants matched/lifecycle events emailed to them.
    Generating a NotificationEvent (eligibility) is separate from
    actually sending it - frequency only controls the send/digest
    cadence, not whether eligibility is tracked (see NotificationEvent).
    """

    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    OFF = "off"


class NotificationPreference(Base):
    """One row per user, controlling whether/how/what they're notified
    about. `categories`/`industries`/`locations` are plain string
    arrays (not DB enums) validated against InternshipCategory etc. at
    the API layer - an empty array means "no filter on this dimension"
    (matches everything), not "matches nothing".
    """

    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    frequency: Mapped[NotificationFrequency] = mapped_column(
        Enum(
            NotificationFrequency,
            name="notification_frequency",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=NotificationFrequency.OFF,
        server_default=NotificationFrequency.OFF.value,
    )
    categories: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list, server_default="{}")
    industries: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list, server_default="{}")
    locations: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list, server_default="{}")
    # Only ever set when a digest actually goes out (frequency=daily/weekly),
    # so the notification job can tell whether enough time has passed since
    # the last send - never touched for immediate-frequency users.
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="notification_preference")

    def __repr__(self) -> str:
        return f"<NotificationPreference user_id={self.user_id} frequency={self.frequency}>"


class NotificationEventType(str, enum.Enum):
    NEW_MATCH = "new_match"
    SAVED_INTERNSHIP_INACTIVE = "saved_internship_inactive"


class NotificationEventStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationEvent(Base):
    """One row per (user, internship, reason) that ever became eligible
    for a notification - this table IS the idempotency mechanism (Phase
    9, Step 8/10). The unique constraint below means a second attempt to
    generate the same event (e.g. a re-run of the scraper workflow) is a
    guaranteed no-op at the database level, not something the
    application has to remember to check for itself.
    """

    __tablename__ = "notification_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    internship_id: Mapped[int] = mapped_column(ForeignKey("internships.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(
            NotificationEventType,
            name="notification_event_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    status: Mapped[NotificationEventStatus] = mapped_column(
        Enum(
            NotificationEventStatus,
            name="notification_event_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=NotificationEventStatus.PENDING,
        server_default=NotificationEventStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Truncated exception message only, never a full traceback or
    # anything that could contain the email provider's API key.
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship()
    internship: Mapped["Internship"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "internship_id", "event_type", name="uq_notification_events_user_internship_type"),
    )

    def __repr__(self) -> str:
        return f"<NotificationEvent user_id={self.user_id} internship_id={self.internship_id} type={self.event_type} status={self.status}>"
