from backend.models import Company, Internship
from tests.conftest import make_fake_scraper


def test_existing_job_remains_active_when_seen_again(db_session):
    scraper_cls = make_fake_scraper("test-lifecycle-a", [{"title": "A Intern", "url": "https://x/a"}])
    scraper_cls().run()
    scraper_cls().run()  # same listing again

    company = db_session.query(Company).filter_by(slug="test-lifecycle-a").one()
    internship = db_session.query(Internship).filter_by(company_id=company.id).one()
    assert internship.is_active is True


def test_missing_job_becomes_inactive(db_session):
    scraper_cls = make_fake_scraper(
        "test-lifecycle-b",
        [{"title": "A Intern", "url": "https://x/a"}, {"title": "B Intern", "url": "https://x/b"}],
    )
    scraper_cls().run()

    # Second run: "B Intern" no longer posted.
    scraper_cls.fetch_raw_listings = lambda self: [{"title": "A Intern", "url": "https://x/a"}]
    scraper_cls().run()

    company = db_session.query(Company).filter_by(slug="test-lifecycle-b").one()
    a = db_session.query(Internship).filter_by(company_id=company.id, title="A Intern").one()
    b = db_session.query(Internship).filter_by(company_id=company.id, title="B Intern").one()
    assert a.is_active is True
    assert b.is_active is False


def test_reappearing_job_becomes_active_again(db_session):
    scraper_cls = make_fake_scraper(
        "test-lifecycle-c",
        [{"title": "A Intern", "url": "https://x/a"}, {"title": "B Intern", "url": "https://x/b"}],
    )
    scraper_cls().run()

    scraper_cls.fetch_raw_listings = lambda self: [{"title": "A Intern", "url": "https://x/a"}]
    scraper_cls().run()  # B goes inactive

    scraper_cls.fetch_raw_listings = lambda self: [
        {"title": "A Intern", "url": "https://x/a"},
        {"title": "B Intern", "url": "https://x/b"},
    ]
    scraper_cls().run()  # B reappears

    company = db_session.query(Company).filter_by(slug="test-lifecycle-c").one()
    b = db_session.query(Internship).filter_by(company_id=company.id, title="B Intern").one()
    assert b.is_active is True
    assert b.first_seen_at < b.last_seen_at or b.first_seen_at == b.last_seen_at


def test_failed_fetch_does_not_deactivate_existing_jobs(db_session):
    """Extremely important (Phase 7 Step 14): a scraper outage must not
    wipe out a company's postings just because one run's fetch failed."""
    scraper_cls = make_fake_scraper("test-lifecycle-d", [{"title": "A Intern", "url": "https://x/a"}])
    scraper_cls().run()

    failing_cls = make_fake_scraper(
        "test-lifecycle-d", [], raise_on_fetch=ConnectionError("simulated network failure")
    )
    try:
        failing_cls().run()
    except ConnectionError:
        pass  # expected - the failure must propagate so the scheduler can see it

    company = db_session.query(Company).filter_by(slug="test-lifecycle-d").one()
    a = db_session.query(Internship).filter_by(company_id=company.id, title="A Intern").one()
    assert a.is_active is True  # unaffected by the failed run
