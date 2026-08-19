from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas.internships import InternshipOut
from backend.models.internship import InternshipCategory
from backend.models.notification import NotificationFrequency


class UserOut(BaseModel):
    """Public-safe user representation - never the Clerk user ID
    (internal identifier, no reason to expose it) or anything
    authentication-related."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class SavedInternshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship: InternshipOut
    created_at: datetime


class SavedInternshipListResponse(BaseModel):
    items: list[SavedInternshipOut]
    total: int


MAX_LOCATION_PREFERENCES = 20


class NotificationPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_enabled: bool
    frequency: NotificationFrequency
    categories: list[InternshipCategory]
    industries: list[str]
    locations: list[str]
    updated_at: datetime


class NotificationPreferenceUpdate(BaseModel):
    """All fields optional - a PUT only needs to send what it's changing;
    unset fields keep their current stored value (see routes/me.py)."""

    email_enabled: bool | None = None
    frequency: NotificationFrequency | None = None
    categories: list[InternshipCategory] | None = None
    industries: list[str] | None = Field(default=None, max_length=50)
    locations: list[str] | None = Field(default=None, max_length=MAX_LOCATION_PREFERENCES)
