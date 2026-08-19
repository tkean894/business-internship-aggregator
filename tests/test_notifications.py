from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

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
)
from backend.services.email import EmailSendError
from backend.services.notifications import (
    generate_new_match_events,
    generate_saved_inactive_events,
    send_pending_notifications,
)
from tests.conftest import make_test_user


# A location no real scraped internship will ever have, so a
# backdated-created_at preference used to test "matches everything
# discovered since I signed up" can't accidentally scoop up real
# production-like data already sitting in the local dev DB.
TEST_LOCATION = "Testville, ZZ"


def _make_internship(db_session, *, slug: str, category, first_seen_at, is_active=True) -> Internship:
    company = db_session.query(Company).filter_by(slug=f"test-{slug}").one_or_none()
    if company is None:
        company = Company(name=f"Test Co {slug}", slug=f"test-{slug}", career_url="https://example.test", industry="Technology")
        db_session.add(company)
        db_session.flush()
    internship = Internship(
        company_id=company.id,
        title=f"{category.value} Intern {slug}",
        category=category,
        location=TEST_LOCATION,
        application_url=f"https://example.test/{slug}",
        source_url=f"https://example.test/{slug}",
        posted_date=date.today(),
        is_active=is_active,
        first_seen_at=first_seen_at,
        last_seen_at=first_seen_at,
        dedupe_key=f"test-dedupe-{slug}",
    )
    db_session.add(internship)
    db_session.commit()
    db_session.refresh(internship)
    return internship


OLD = datetime.now(timezone.utc) - timedelta(days=365)
RECENT = datetime.now(timezone.utc) - timedelta(hours=1)


def test_matching_internship_creates_eligibility_event(db_session):
    user = make_test_user(db_session, "notif-a")
    pref = NotificationPreference(
        user_id=user.id, email_enabled=True, frequency=NotificationFrequency.IMMEDIATE,
        categories=["Finance"], locations=[TEST_LOCATION], created_at=OLD,
    )
    db_session.add(pref)
    db_session.commit()

    internship = _make_internship(db_session, slug="notif-a-1", category=InternshipCategory.FINANCE, first_seen_at=RECENT)

    created = generate_new_match_events(db_session)
    assert created == 1
    event = db_session.query(NotificationEvent).filter_by(user_id=user.id, internship_id=internship.id).one()
    assert event.event_type == NotificationEventType.NEW_MATCH
    assert event.status == NotificationEventStatus.PENDING


def test_non_matching_internship_does_not_create_event(db_session):
    user = make_test_user(db_session, "notif-b")
    pref = NotificationPreference(
        user_id=user.id, email_enabled=True, frequency=NotificationFrequency.IMMEDIATE,
        categories=["Finance"], locations=[TEST_LOCATION], created_at=OLD,
    )
    db_session.add(pref)
    db_session.commit()

    _make_internship(db_session, slug="notif-b-1", category=InternshipCategory.MARKETING, first_seen_at=RECENT)

    created = generate_new_match_events(db_session)
    assert created == 0
    assert db_session.query(NotificationEvent).filter_by(user_id=user.id).count() == 0


def test_internship_older_than_preference_does_not_notify(db_session):
    """Never notify about internships that already existed before the
    preference was created (Phase 9, Step 8)."""
    user = make_test_user(db_session, "notif-c")
    pref_created_at = datetime.now(timezone.utc)
    internship = _make_internship(
        db_session, slug="notif-c-1", category=InternshipCategory.FINANCE, first_seen_at=pref_created_at - timedelta(days=1)
    )
    pref = NotificationPreference(
        user_id=user.id, email_enabled=True, frequency=NotificationFrequency.IMMEDIATE,
        categories=["Finance"], created_at=pref_created_at,
    )
    db_session.add(pref)
    db_session.commit()

    created = generate_new_match_events(db_session)
    assert created == 0


def test_empty_category_filter_matches_everything(db_session):
    user = make_test_user(db_session, "notif-d")
    pref = NotificationPreference(
        user_id=user.id, email_enabled=True, frequency=NotificationFrequency.IMMEDIATE,
        categories=[], locations=[TEST_LOCATION], created_at=OLD,
    )
    db_session.add(pref)
    db_session.commit()

    _make_internship(db_session, slug="notif-d-1", category=InternshipCategory.OTHER, first_seen_at=RECENT)

    created = generate_new_match_events(db_session)
    assert created == 1


def test_disabled_notifications_do_not_generate_events(db_session):
    user = make_test_user(db_session, "notif-e")
    pref = NotificationPreference(
        user_id=user.id, email_enabled=False, frequency=NotificationFrequency.IMMEDIATE,
        categories=[], locations=[TEST_LOCATION], created_at=OLD,
    )
    db_session.add(pref)
    db_session.commit()
    _make_internship(db_session, slug="notif-e-1", category=InternshipCategory.FINANCE, first_seen_at=RECENT)

    assert generate_new_match_events(db_session) == 0


def test_repeated_generation_does_not_duplicate_events(db_session):
    user = make_test_user(db_session, "notif-f")
    pref = NotificationPreference(
        user_id=user.id, email_enabled=True, frequency=NotificationFrequency.IMMEDIATE,
        categories=["Finance"], locations=[TEST_LOCATION], created_at=OLD,
    )
    db_session.add(pref)
    db_session.commit()
    _make_internship(db_session, slug="notif-f-1", category=InternshipCategory.FINANCE, first_seen_at=RECENT)

    first = generate_new_match_events(db_session)
    second = generate_new_match_events(db_session)  # simulates a re-run of the GH Actions workflow
    third = generate_new_match_events(db_session)
    assert first == 1
    assert second == 0
    assert third == 0
    assert db_session.query(NotificationEvent).filter_by(user_id=user.id).count() == 1


def test_saved_internship_going_inactive_creates_event(db_session):
    user = make_test_user(db_session, "notif-g")
    internship = _make_internship(db_session, slug="notif-g-1", category=InternshipCategory.FINANCE, first_seen_at=OLD, is_active=False)
    db_session.add(SavedInternship(user_id=user.id, internship_id=internship.id))
    db_session.commit()

    created = generate_saved_inactive_events(db_session)
    assert created == 1
    event = db_session.query(NotificationEvent).filter_by(
        user_id=user.id, internship_id=internship.id, event_type=NotificationEventType.SAVED_INTERNSHIP_INACTIVE
    ).one()
    assert event.status == NotificationEventStatus.PENDING


def test_saved_active_internship_does_not_create_inactive_event(db_session):
    user = make_test_user(db_session, "notif-h")
    internship = _make_internship(db_session, slug="notif-h-1", category=InternshipCategory.FINANCE, first_seen_at=OLD, is_active=True)
    db_session.add(SavedInternship(user_id=user.id, internship_id=internship.id))
    db_session.commit()

    assert generate_saved_inactive_events(db_session) == 0


def test_repeated_scraper_execution_does_not_duplicate_inactive_notifications(db_session):
    user = make_test_user(db_session, "notif-i")
    internship = _make_internship(db_session, slug="notif-i-1", category=InternshipCategory.FINANCE, first_seen_at=OLD, is_active=False)
    db_session.add(SavedInternship(user_id=user.id, internship_id=internship.id))
    db_session.commit()

    generate_saved_inactive_events(db_session)
    generate_saved_inactive_events(db_session)  # simulated re-run
    assert db_session.query(NotificationEvent).filter_by(user_id=user.id).count() == 1


def test_send_pending_marks_events_sent_and_records_preference(db_session):
    user = make_test_user(db_session, "notif-j")
    pref = NotificationPreference(user_id=user.id, email_enabled=True, frequency=NotificationFrequency.IMMEDIATE, categories=["Finance"], locations=[TEST_LOCATION], created_at=OLD)
    db_session.add(pref)
    db_session.commit()
    internship = _make_internship(db_session, slug="notif-j-1", category=InternshipCategory.FINANCE, first_seen_at=RECENT)
    generate_new_match_events(db_session)

    with patch("backend.services.notifications.send_email", return_value="msg_123") as mock_send:
        result = send_pending_notifications(db_session)

    assert mock_send.called
    assert result == {"sent": 1, "failed": 0}
    event = db_session.query(NotificationEvent).filter_by(user_id=user.id, internship_id=internship.id).one()
    assert event.status == NotificationEventStatus.SENT
    assert event.sent_at is not None
    db_session.refresh(pref)
    assert pref.last_notified_at is not None


def test_failed_email_marks_events_failed_not_sent(db_session):
    user = make_test_user(db_session, "notif-k")
    pref = NotificationPreference(user_id=user.id, email_enabled=True, frequency=NotificationFrequency.IMMEDIATE, categories=["Finance"], locations=[TEST_LOCATION], created_at=OLD)
    db_session.add(pref)
    db_session.commit()
    internship = _make_internship(db_session, slug="notif-k-1", category=InternshipCategory.FINANCE, first_seen_at=RECENT)
    generate_new_match_events(db_session)

    with patch("backend.services.notifications.send_email", side_effect=EmailSendError("provider down")):
        result = send_pending_notifications(db_session)

    assert result == {"sent": 0, "failed": 1}
    event = db_session.query(NotificationEvent).filter_by(user_id=user.id, internship_id=internship.id).one()
    assert event.status == NotificationEventStatus.FAILED
    assert event.sent_at is None
    assert "provider down" in event.error_message


def test_daily_frequency_user_not_yet_due_is_skipped(db_session):
    user = make_test_user(db_session, "notif-l")
    pref = NotificationPreference(
        user_id=user.id, email_enabled=True, frequency=NotificationFrequency.DAILY,
        categories=["Finance"], locations=[TEST_LOCATION], created_at=OLD, last_notified_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(pref)
    db_session.commit()
    _make_internship(db_session, slug="notif-l-1", category=InternshipCategory.FINANCE, first_seen_at=RECENT)
    generate_new_match_events(db_session)

    with patch("backend.services.notifications.send_email") as mock_send:
        result = send_pending_notifications(db_session)

    assert not mock_send.called
    assert result == {"sent": 0, "failed": 0}


def test_daily_frequency_user_past_due_is_sent(db_session):
    user = make_test_user(db_session, "notif-m")
    pref = NotificationPreference(
        user_id=user.id, email_enabled=True, frequency=NotificationFrequency.DAILY,
        categories=["Finance"], locations=[TEST_LOCATION], created_at=OLD, last_notified_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    db_session.add(pref)
    db_session.commit()
    _make_internship(db_session, slug="notif-m-1", category=InternshipCategory.FINANCE, first_seen_at=RECENT)
    generate_new_match_events(db_session)

    with patch("backend.services.notifications.send_email", return_value="msg_id") as mock_send:
        result = send_pending_notifications(db_session)

    assert mock_send.called
    assert result == {"sent": 1, "failed": 0}
