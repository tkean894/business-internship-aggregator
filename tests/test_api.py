"""API-level tests for the internships/companies endpoints, run against
the local dev database via FastAPI's TestClient (Phase 8, Step 24) -
covers the new `industry` filter and `first_seen_desc` sort alongside
existing filters/pagination/empty results, using whatever real data is
currently in the local dev DB rather than a separate fixture dataset."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_categories_endpoint_includes_new_categories():
    resp = client.get("/categories")
    assert resp.status_code == 200
    categories = resp.json()["categories"]
    assert "Sales" in categories
    assert "Real Estate" in categories


def test_companies_endpoint_includes_industry_field():
    resp = client.get("/companies")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0
    assert "industry" in items[0]


def test_internships_industry_filter_only_returns_matching_companies():
    resp = client.get("/internships", params={"industry": "Insurance", "page_size": 100})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0  # local dev DB has Insurance-industry companies as of Phase 8
    for item in data["items"]:
        assert item["company"]["industry"] == "Insurance"
    unfiltered = client.get("/internships", params={"page_size": 1}).json()["total"]
    assert data["total"] < unfiltered


def test_internships_industry_filter_unknown_value_returns_empty():
    resp = client.get("/internships", params={"industry": "Nonexistent Industry XYZ"})
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["total"] == 0


def test_internships_first_seen_desc_sort_is_accepted():
    resp = client.get("/internships", params={"sort": "first_seen_desc", "page_size": 5})
    assert resp.status_code == 200
    items = resp.json()["items"]
    timestamps = [item["first_seen_at"] for item in items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_internships_invalid_sort_returns_422():
    resp = client.get("/internships", params={"sort": "not_a_real_sort"})
    assert resp.status_code == 422


def test_internships_pagination_respects_page_size():
    resp = client.get("/internships", params={"page_size": 2, "page": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_internships_existing_category_filter_still_works():
    resp = client.get("/internships", params={"category": "Finance", "page_size": 50})
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["category"] == "Finance"


def test_health_check_returns_no_internal_details():
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"status", "service"}
