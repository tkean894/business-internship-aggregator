from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager

from backend.api.auth import get_current_user
from backend.api.dependencies import get_db
from backend.api.schemas.users import (
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    SavedInternshipListResponse,
    SavedInternshipOut,
    UserOut,
)
from backend.models import Internship, NotificationPreference, SavedInternship, User

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserOut, summary="Get the current authenticated user")
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.get("/saved", response_model=SavedInternshipListResponse, summary="List the current user's saved internships")
def list_saved_internships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedInternshipListResponse:
    stmt = (
        select(SavedInternship)
        .join(SavedInternship.internship)
        .join(Internship.company)
        .options(contains_eager(SavedInternship.internship).contains_eager(Internship.company))
        .where(SavedInternship.user_id == current_user.id)
        .order_by(SavedInternship.created_at.desc())
    )
    saved = db.scalars(stmt).unique().all()
    items = []
    for row in saved:
        out = SavedInternshipOut.model_validate(row)
        # Every internship on this page belongs to the current user by
        # definition (it's their saved list) - always true, no extra query.
        out.internship = out.internship.model_copy(update={"is_saved": True})
        items.append(out)
    return SavedInternshipListResponse(items=items, total=len(items))


def _get_or_create_preference(db: Session, user: User) -> NotificationPreference:
    pref = db.query(NotificationPreference).filter_by(user_id=user.id).one_or_none()
    if pref is None:
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.get(
    "/notification-preferences",
    response_model=NotificationPreferenceOut,
    summary="Get the current user's notification preferences",
)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceOut:
    return NotificationPreferenceOut.model_validate(_get_or_create_preference(db, current_user))


@router.put(
    "/notification-preferences",
    response_model=NotificationPreferenceOut,
    summary="Update the current user's notification preferences",
)
def update_notification_preferences(
    update: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPreferenceOut:
    pref = _get_or_create_preference(db, current_user)
    changes = update.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if field == "categories" and value is not None:
            value = [c.value if hasattr(c, "value") else c for c in value]
        setattr(pref, field, value)
    db.commit()
    db.refresh(pref)
    return NotificationPreferenceOut.model_validate(pref)
