from scrapers import scheduler
from tests.conftest import make_fake_scraper


def test_one_company_failing_does_not_stop_the_others(db_session, monkeypatch):
    good_a = make_fake_scraper("test-sched-a", [{"title": "A Intern", "url": "https://x/a"}])
    failing = make_fake_scraper("test-sched-b", [], raise_on_fetch=ConnectionError("simulated"))
    good_c = make_fake_scraper("test-sched-c", [{"title": "C Intern", "url": "https://x/c"}])

    monkeypatch.setattr(scheduler, "SCRAPERS", [good_a, failing, good_c])

    succeeded = scheduler.run_all()

    assert succeeded is False  # overall result reflects the one hard failure

    from backend.models import Company

    # But the companies on either side of the failing one still ran.
    assert db_session.query(Company).filter_by(slug="test-sched-a").one_or_none() is not None
    assert db_session.query(Company).filter_by(slug="test-sched-c").one_or_none() is not None


def test_all_companies_succeeding_returns_true(db_session, monkeypatch):
    good_a = make_fake_scraper("test-sched-d", [{"title": "A Intern", "url": "https://x/a"}])
    good_b = make_fake_scraper("test-sched-e", [{"title": "B Intern", "url": "https://x/b"}])

    monkeypatch.setattr(scheduler, "SCRAPERS", [good_a, good_b])

    assert scheduler.run_all() is True
