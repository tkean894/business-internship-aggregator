from __future__ import annotations

from backend.models import Internship, SavedInternship
from tests.conftest import make_test_user


def _any_internship_id(db_session) -> int:
    return db_session.query(Internship.id).first()[0]


def test_authenticated_user_can_save_and_unsave(db_session, api_client):
    user = make_test_user(db_session, "save-a")
    internship_id = _any_internship_id(db_session)
    client = api_client(user)

    resp = client.post(f"/internships/{internship_id}/save")
    assert resp.status_code == 201
    assert db_session.query(SavedInternship).filter_by(user_id=user.id, internship_id=internship_id).count() == 1

    resp = client.delete(f"/internships/{internship_id}/save")
    assert resp.status_code == 204
    assert db_session.query(SavedInternship).filter_by(user_id=user.id, internship_id=internship_id).count() == 0


def test_duplicate_save_does_not_create_duplicate_rows(db_session, api_client):
    user = make_test_user(db_session, "save-b")
    internship_id = _any_internship_id(db_session)
    client = api_client(user)

    assert client.post(f"/internships/{internship_id}/save").status_code == 201
    assert client.post(f"/internships/{internship_id}/save").status_code == 201  # idempotent, not an error
    assert db_session.query(SavedInternship).filter_by(user_id=user.id, internship_id=internship_id).count() == 1


def test_unsave_something_never_saved_is_safe(db_session, api_client):
    user = make_test_user(db_session, "save-c")
    internship_id = _any_internship_id(db_session)
    client = api_client(user)

    resp = client.delete(f"/internships/{internship_id}/save")
    assert resp.status_code == 204  # not an error, per spec


def test_saving_a_nonexistent_internship_returns_404(db_session, api_client):
    user = make_test_user(db_session, "save-d")
    client = api_client(user)

    resp = client.post("/internships/999999999/save")
    assert resp.status_code == 404


def test_saving_requires_authentication(db_session, api_client):
    internship_id = _any_internship_id(db_session)
    client = api_client(None)

    resp = client.post(f"/internships/{internship_id}/save")
    assert resp.status_code == 401


def test_user_a_cannot_see_user_b_saved_internships(db_session, api_client):
    user_a = make_test_user(db_session, "save-e-a")
    user_b = make_test_user(db_session, "save-e-b")
    internship_id = _any_internship_id(db_session)

    api_client(user_a).post(f"/internships/{internship_id}/save")

    resp_b = api_client(user_b).get("/me/saved")
    assert resp_b.status_code == 200
    assert resp_b.json()["total"] == 0

    resp_a = api_client(user_a).get("/me/saved")
    assert resp_a.json()["total"] == 1


def test_is_saved_field_reflects_actual_state(db_session, api_client):
    user = make_test_user(db_session, "save-f")
    internship_id = _any_internship_id(db_session)
    client = api_client(user)

    detail = client.get(f"/internships/{internship_id}").json()
    assert detail["is_saved"] is False

    client.post(f"/internships/{internship_id}/save")
    detail = client.get(f"/internships/{internship_id}").json()
    assert detail["is_saved"] is True


def test_anonymous_user_sees_is_saved_false_not_an_error(db_session, api_client):
    internship_id = _any_internship_id(db_session)
    client = api_client(None)

    resp = client.get(f"/internships/{internship_id}")
    assert resp.status_code == 200
    assert resp.json()["is_saved"] is False


def test_anonymous_browsing_still_works(db_session, api_client):
    client = api_client(None)
    assert client.get("/internships").status_code == 200
    assert client.get("/companies").status_code == 200
