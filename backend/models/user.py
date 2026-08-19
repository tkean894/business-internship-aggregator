from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.notification import NotificationPreference
    from backend.models.saved_internship import SavedInternship


class User(Base):
    """An authenticated application user.

    Credentials (password, sessions, MFA, etc.) are entirely managed by
    Clerk (see backend/api/auth.py) - this table deliberately never
    stores a password or session token, only the provider's user ID and
    the small set of app-specific fields this application actually
    needs (a cached email for composing notifications without an extra
    Clerk API call per send, and our own row's id for foreign keys).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    saved_internships: Mapped[list["SavedInternship"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notification_preference: Mapped["NotificationPreference | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} clerk_user_id={self.clerk_user_id!r}>"
