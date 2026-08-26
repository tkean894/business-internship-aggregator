import time

from scrapers import scheduler
from tests.conftest import make_fake_scraper


def test_scrapers_run_concurrently_not_sequentially(monkeypatch):
    # Regression test for the Phase 10 Step 5 follow-up: run_all() must
    # actually run scrapers in parallel, not just accept a thread pool
    # object without using it - a purely sequential fallback would defeat
    # the whole point (the GitHub Actions timeout this was built to fix).
    # Five scrapers that each sleep 0.3s: sequential would take >=1.5s;
    # with MAX_PARALLEL_SCRAPERS=8 all five fit in one batch and should
    # complete in well under 1.5s.
    def _slow_fetch(self):
        time.sleep(0.3)
        return []

    scrapers = [
        make_fake_scraper(f"test-parallel-{i}", [], parse=lambda raw: None)
        for i in range(5)
    ]
    for cls in scrapers:
        monkeypatch.setattr(cls, "fetch_raw_listings", _slow_fetch)
    monkeypatch.setattr(scheduler, "SCRAPERS", scrapers)

    started = time.monotonic()
    assert scheduler.run_all() is True
    elapsed = time.monotonic() - started

    assert elapsed < 1.0, f"expected concurrent execution well under 1.5s, took {elapsed:.2f}s"


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
