from __future__ import annotations

from backend.models import NotificationPreference
from tests.conftest import make_test_user


def test_get_preferences_creates_sane_defaults(db_session, api_client):
    user = make_test_user(db_session, "pref-a")
    client = api_client(user)

    resp = client.get("/me/notification-preferences")
    assert resp.status_code == 200
    body = resp.json()
    assert body["frequency"] == "off"
    assert body["categories"] == []


def test_update_preferences_persists(db_session, api_client):
    user = make_test_user(db_session, "pref-b")
    client = api_client(user)

    resp = client.put(
        "/me/notification-preferences",
        json={
            "email_enabled": True,
            "frequency": "daily",
            "categories": ["Finance", "Marketing"],
            "industries": ["Healthcare"],
            "locations": ["Austin, TX"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["frequency"] == "daily"
    assert sorted(body["categories"]) == ["Finance", "Marketing"]
    assert body["industries"] == ["Healthcare"]

    pref = db_session.query(NotificationPreference).filter_by(user_id=user.id).one()
    assert pref.frequency.value == "daily"


def test_partial_update_only_changes_sent_fields(db_session, api_client):
    user = make_test_user(db_session, "pref-c")
    client = api_client(user)

    client.put("/me/notification-preferences", json={"frequency": "weekly", "categories": ["Finance"]})
    resp = client.put("/me/notification-preferences", json={"email_enabled": False})
    body = resp.json()
    assert body["email_enabled"] is False
    assert body["frequency"] == "weekly"  # untouched by the second PUT
    assert body["categories"] == ["Finance"]  # untouched


def test_invalid_frequency_value_is_rejected():
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    resp = client.put("/me/notification-preferences", json={"frequency": "constantly"})
    # No auth override applied here, so this should 401 before validation
    # even runs - confirms the endpoint is protected. A dedicated
    # authenticated 422 check follows below.
    assert resp.status_code == 401


def test_invalid_frequency_value_returns_422_when_authenticated(db_session, api_client):
    user = make_test_user(db_session, "pref-d")
    client = api_client(user)
    resp = client.put("/me/notification-preferences", json={"frequency": "constantly"})
    assert resp.status_code == 422


def test_invalid_category_value_returns_422(db_session, api_client):
    user = make_test_user(db_session, "pref-e")
    client = api_client(user)
    resp = client.put("/me/notification-preferences", json={"categories": ["Not A Real Category"]})
    assert resp.status_code == 422


def test_preferences_require_authentication(api_client):
    client = api_client(None)
    assert client.get("/me/notification-preferences").status_code == 401
    assert client.put("/me/notification-preferences", json={}).status_code == 401


def test_user_isolation_for_preferences(db_session, api_client):
    user_a = make_test_user(db_session, "pref-f-a")
    user_b = make_test_user(db_session, "pref-f-b")

    api_client(user_a).put("/me/notification-preferences", json={"frequency": "daily"})
    body_b = api_client(user_b).get("/me/notification-preferences").json()
    assert body_b["frequency"] == "off"  # user B's own default, unaffected by user A's update
