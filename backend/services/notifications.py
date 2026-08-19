"""Notification generation and delivery (Phase 9, Step 8/10).

Invoked as a new step appended to the existing GitHub Actions workflow,
after the scraper runs (`python -m backend.services.notifications`) -
deliberately not a second scheduler or server. Three phases, run in
order:

    scraper (existing)
        v
    generate_new_match_events()          - eligibility, idempotent
    generate_saved_inactive_events()     - eligibility, idempotent
        v
    send_pending_notifications()         - cadence-gated delivery

Idempotency is enforced by the database, not application bookkeeping:
notification_events has a UNIQUE(user_id, internship_id, event_type)
constraint (see the Phase 9 migration), so every insert here uses
Postgres's ON CONFLICT DO NOTHING - a re-run of this whole module
(e.g. a retried GitHub Actions workflow) inserts zero new rows for
anything already generated, by construction rather than by careful
bookkeeping that could drift out of sync.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.models import (
    Company,
    Internship,
    InternshipCategory,
    NotificationEvent,
    NotificationEventStatus,
    NotificationEventType,
    NotificationFrequency,
    NotificationPreference,
    SavedInternship,
    User,
)
from backend.services.email import EmailSendError, send_email

logger = logging.getLogger(__name__)

FREQUENCY_INTERVALS = {
    NotificationFrequency.DAILY: timedelta(days=1),
    NotificationFrequency.WEEKLY: timedelta(days=7),
}


def generate_new_match_events(db: Session) -> int:
    """Register (user, internship) pairs eligible for a "new match"
    notification: the internship is active, was first discovered AFTER
    this user's preferences were created (never retroactively notifying
    about internships that already existed - Phase 9, Step 8), and
    matches every filter dimension the user has set (an empty
    categories/industries/locations list on a preference means "no
    filter on this dimension", not "matches nothing").

    Returns the number of NEW eligibility rows created.
    """
    created = 0
    prefs = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.email_enabled.is_(True),
            NotificationPreference.frequency != NotificationFrequency.OFF,
        )
        .all()
    )

    for pref in prefs:
        stmt = (
            select(Internship.id)
            .join(Internship.company)
            .where(Internship.is_active.is_(True), Internship.first_seen_at > pref.created_at)
        )
        if pref.categories:
            stmt = stmt.where(Internship.category.in_([InternshipCategory(c) for c in pref.categories]))
        if pref.industries:
            stmt = stmt.where(Company.industry.in_(pref.industries))
        if pref.locations:
            stmt = stmt.where(Internship.location.in_(pref.locations))

        for internship_id in db.scalars(stmt).all():
            insert_stmt = (
                pg_insert(NotificationEvent)
                .values(
                    user_id=pref.user_id,
                    internship_id=internship_id,
                    event_type=NotificationEventType.NEW_MATCH.value,
                )
                .on_conflict_do_nothing(index_elements=["user_id", "internship_id", "event_type"])
            )
            created += db.execute(insert_stmt).rowcount

    db.commit()
    return created


def generate_saved_inactive_events(db: Session) -> int:
    """Register a "saved internship went inactive" eligibility row for
    every currently-inactive internship a user has saved. Idempotent
    the same way as above - once generated for a given (user,
    internship), re-running this is a no-op even if the internship
    stays inactive across many future scraper runs.
    """
    stmt = (
        select(SavedInternship.user_id, SavedInternship.internship_id)
        .join(Internship, SavedInternship.internship_id == Internship.id)
        .where(Internship.is_active.is_(False))
    )
    created = 0
    for user_id, internship_id in db.execute(stmt).all():
        insert_stmt = (
            pg_insert(NotificationEvent)
            .values(
                user_id=user_id,
                internship_id=internship_id,
                event_type=NotificationEventType.SAVED_INTERNSHIP_INACTIVE.value,
            )
            .on_conflict_do_nothing(index_elements=["user_id", "internship_id", "event_type"])
        )
        created += db.execute(insert_stmt).rowcount

    db.commit()
    return created


def _is_due(pref: NotificationPreference, now: datetime) -> bool:
    if pref.frequency == NotificationFrequency.IMMEDIATE:
        return True
    interval = FREQUENCY_INTERVALS[pref.frequency]
    return pref.last_notified_at is None or (now - pref.last_notified_at) >= interval


def _subject_for(events: list[NotificationEvent]) -> str:
    new_matches = sum(1 for e in events if e.event_type == NotificationEventType.NEW_MATCH)
    inactive = sum(1 for e in events if e.event_type == NotificationEventType.SAVED_INTERNSHIP_INACTIVE)
    parts = []
    if new_matches:
        parts.append(f"{new_matches} new internship{'s' if new_matches != 1 else ''}")
    if inactive:
        parts.append(f"{inactive} saved internship update{'s' if inactive != 1 else ''}")
    return "Business Internship Aggregator: " + " and ".join(parts)


def _render_digest_html(events: list[NotificationEvent]) -> str:
    new_matches = [e for e in events if e.event_type == NotificationEventType.NEW_MATCH]
    inactive = [e for e in events if e.event_type == NotificationEventType.SAVED_INTERNSHIP_INACTIVE]

    sections = []
    if new_matches:
        items = "".join(
            f"<li><strong>{e.internship.title}</strong> at {e.internship.company.name}"
            f" ({e.internship.location or 'location not specified'})</li>"
            for e in new_matches
        )
        sections.append(f"<h2>New internships matching your preferences</h2><ul>{items}</ul>")
    if inactive:
        items = "".join(
            f"<li><strong>{e.internship.title}</strong> at {e.internship.company.name} is no longer active</li>"
            for e in inactive
        )
        sections.append(f"<h2>Saved internships that closed</h2><ul>{items}</ul>")

    return "<div>" + "".join(sections) + "</div>"


def send_pending_notifications(db: Session) -> dict[str, int]:
    """Deliver (or mark failed) every PENDING event for users whose
    frequency preference says they're due right now. Immediate-frequency
    users are always due; daily/weekly users are due only once enough
    time has passed since `last_notified_at`. A user with notifications
    off or no preference row is skipped entirely - their events stay
    PENDING and become eligible for delivery if they re-enable later.
    """
    now = datetime.now(timezone.utc)
    sent_count = 0
    failed_count = 0

    user_ids = db.scalars(
        select(NotificationEvent.user_id).where(NotificationEvent.status == NotificationEventStatus.PENDING).distinct()
    ).all()

    for user_id in user_ids:
        pref = db.query(NotificationPreference).filter_by(user_id=user_id).one_or_none()
        if pref is None or not pref.email_enabled or pref.frequency == NotificationFrequency.OFF:
            continue
        if not _is_due(pref, now):
            continue

        events = db.query(NotificationEvent).filter_by(user_id=user_id, status=NotificationEventStatus.PENDING).all()
        if not events:
            continue

        user = db.get(User, user_id)
        try:
            send_email(to=user.email, subject=_subject_for(events), html=_render_digest_html(events))
        except EmailSendError as exc:
            for event in events:
                event.status = NotificationEventStatus.FAILED
                event.error_message = str(exc)[:500]
            db.commit()
            failed_count += len(events)
            logger.error("Failed to send notification digest to user_id=%s: %s", user_id, exc)
            continue

        for event in events:
            event.status = NotificationEventStatus.SENT
            event.sent_at = now
        pref.last_notified_at = now
        db.commit()
        sent_count += len(events)

    return {"sent": sent_count, "failed": failed_count}


def run() -> None:
    db = SessionLocal()
    try:
        new_match_count = generate_new_match_events(db)
        logger.info("Generated %d new-match notification event(s)", new_match_count)
        inactive_count = generate_saved_inactive_events(db)
        logger.info("Generated %d saved-inactive notification event(s)", inactive_count)
        result = send_pending_notifications(db)
        logger.info("Sent %d notification(s), %d failed", result["sent"], result["failed"])
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()
