"""Shared test fixtures.

These tests run against the local development PostgreSQL database (the
same one used for `python -m scrapers.scheduler` locally - see
README.md "Local Development") rather than a mocked DB layer: this
project already treats "run the real scraper pipeline against a real
Postgres instance and inspect the result" as its primary verification
method (see docs/architecture.md), and duplicating that with a second,
separately-maintained fake-DB layer would be more machinery than a
student-project test suite needs. External HTTP calls ARE mocked
(FakeScraper below), per Phase 7 Step 20, so tests never depend on
company career sites being reachable or unchanged.

All test data uses a "test-" prefixed company slug, and the `cleanup`
fixture below deletes anything under that prefix after every test, so
tests never pollute real scraped data and can be re-run freely.
"""

from __future__ import annotations

from typing import Callable

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.database.session import SessionLocal
from backend.models import Company, Internship, ScraperRun, User
from scrapers.base_scraper import BaseScraper
from scrapers.schemas import NormalizedInternship

TEST_SLUG_PREFIX = "test-"
TEST_USER_PREFIX = "test-"


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield
    session = SessionLocal()
    try:
        test_companies = (
            session.query(Company).filter(Company.slug.like(f"{TEST_SLUG_PREFIX}%")).all()
        )
        for company in test_companies:
            session.query(Internship).filter_by(company_id=company.id).delete()
        session.query(ScraperRun).filter(ScraperRun.company_slug.like(f"{TEST_SLUG_PREFIX}%")).delete(
            synchronize_session=False
        )
        for company in test_companies:
            session.delete(company)
        # SavedInternship / NotificationPreference / NotificationEvent all
        # have ondelete="CASCADE" foreign keys to users.id, so deleting the
        # test user rows here cleans those up automatically.
        session.query(User).filter(User.clerk_user_id.like(f"{TEST_USER_PREFIX}%")).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def make_test_user(db_session, suffix: str, *, email: str | None = None) -> User:
    """A throwaway User row for auth-related tests. `suffix` must be
    unique per test to avoid clashing with other tests running in the
    same session; the clerk_user_id is prefixed with "test-" so the
    cleanup fixture above finds and removes it (and, via CASCADE,
    anything that references it) afterward."""
    user = User(clerk_user_id=f"test-{suffix}", email=email or f"test-{suffix}@example.test")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def api_client():
    """A FastAPI TestClient factory that overrides the Clerk-verification
    dependencies directly (the standard FastAPI testing pattern) rather
    than forging JWTs - the JWT verification logic itself (signature
    checking against Clerk's real JWKS) is exercised separately in
    tests/test_auth.py."""
    from backend.api.auth import get_current_user, get_current_user_optional
    from backend.api.main import app

    def _make(user: User | None = None) -> TestClient:
        if user is not None:
            app.dependency_overrides[get_current_user_optional] = lambda: user
            app.dependency_overrides[get_current_user] = lambda: user
        else:
            def _require_auth():
                raise HTTPException(status_code=401, detail="Authentication required")

            app.dependency_overrides[get_current_user_optional] = lambda: None
            app.dependency_overrides[get_current_user] = _require_auth
        return TestClient(app)

    yield _make
    from backend.api.main import app as _app

    _app.dependency_overrides.clear()


def make_fake_scraper(
    slug: str,
    listings: list[dict],
    *,
    parse: Callable[[dict], NormalizedInternship | None] | None = None,
    raise_on_fetch: Exception | None = None,
) -> type[BaseScraper]:
    """Build a throwaway BaseScraper subclass with a fully-controlled,
    in-memory fetch_raw_listings() - the "mock external HTTP requests"
    seam Phase 7 Step 20 asks for. `slug` must start with "test-" so
    the cleanup fixture above can find and remove it afterward."""
    assert slug.startswith(TEST_SLUG_PREFIX), "test scraper slugs must start with 'test-' for cleanup"

    default_parse = parse or _default_parse

    class FakeScraper(BaseScraper):
        company_slug = slug
        company_name = f"Fake Co ({slug})"
        career_url = "https://example.test/careers"
        website_url = "https://example.test"

        def fetch_raw_listings(self) -> list[dict]:
            if raise_on_fetch is not None:
                raise raise_on_fetch
            return listings

        def parse_listing(self, raw: dict) -> NormalizedInternship | None:
            return default_parse(raw)

    FakeScraper.__name__ = f"FakeScraper_{slug}"
    return FakeScraper


def _default_parse(raw: dict) -> NormalizedInternship | None:
    from datetime import date

    from backend.models import InternshipCategory

    return NormalizedInternship(
        title=raw["title"],
        description=raw.get("description"),
        category=raw.get("category", InternshipCategory.OTHER),
        location=raw.get("location", "Remote"),
        application_url=raw.get("url", "https://example.test/jobs/x"),
        source_url=raw.get("url", "https://example.test/jobs/x"),
        posted_date=raw.get("posted_date", date.today()),
        application_deadline=None,
    )
