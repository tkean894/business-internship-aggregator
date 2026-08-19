from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.internship import Internship
    from backend.models.user import User


class SavedInternship(Base):
    """A user's bookmark of one internship.

    `is_active` on the referenced Internship is intentionally NOT
    mirrored here - saving never copies internship state, so a saved
    internship going inactive is discovered by joining through to the
    live Internship row (see Phase 9 "Saved Internship Lifecycle"),
    never by the save itself going stale.
    """

    __tablename__ = "saved_internships"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    internship_id: Mapped[int] = mapped_column(ForeignKey("internships.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="saved_internships")
    internship: Mapped["Internship"] = relationship()

    __table_args__ = (UniqueConstraint("user_id", "internship_id", name="uq_saved_internships_user_internship"),)

    def __repr__(self) -> str:
        return f"<SavedInternship user_id={self.user_id} internship_id={self.internship_id}>"
