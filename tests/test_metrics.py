from backend.models import ScraperRun, ScraperRunStatus
from tests.conftest import make_fake_scraper


def test_successful_run_is_recorded_with_correct_counts(db_session):
    scraper_cls = make_fake_scraper(
        "test-metrics-a",
        [{"title": "A Intern", "url": "https://x/a"}, {"title": "Not Relevant", "url": "https://x/b"}],
        parse=lambda raw: None if raw["title"] == "Not Relevant" else _parse(raw),
    )
    scraper_cls().run()

    run = db_session.query(ScraperRun).filter_by(company_slug="test-metrics-a").one()
    assert run.status == ScraperRunStatus.SUCCESS
    assert run.raw_count == 2
    assert run.relevant_count == 1
    assert run.created_count == 1
    assert run.skipped_count == 1
    assert run.completed_at is not None
    assert run.completed_at >= run.started_at


def test_failed_run_is_recorded_with_error_message(db_session):
    scraper_cls = make_fake_scraper("test-metrics-b", [], raise_on_fetch=TimeoutError("simulated timeout"))
    try:
        scraper_cls().run()
    except TimeoutError:
        pass

    run = db_session.query(ScraperRun).filter_by(company_slug="test-metrics-b").one()
    assert run.status == ScraperRunStatus.FAILED
    assert run.error_message is not None
    assert "simulated timeout" in run.error_message
    assert "DATABASE_URL" not in run.error_message


def test_partial_company_failure_still_records_created_and_error_counts(db_session):
    scraper_cls = make_fake_scraper(
        "test-metrics-c",
        [{"title": "Good Intern", "url": "https://x/a"}, {"title": "Bad", "url": "https://x/b"}],
        parse=lambda raw: _raise_for_bad(raw),
    )
    scraper_cls().run()

    run = db_session.query(ScraperRun).filter_by(company_slug="test-metrics-c").one()
    assert run.status == ScraperRunStatus.SUCCESS  # per-listing errors don't fail the whole run
    assert run.created_count == 1
    assert run.error_count == 1


def _parse(raw):
    from datetime import date

    from backend.models import InternshipCategory
    from scrapers.schemas import NormalizedInternship

    return NormalizedInternship(
        title=raw["title"],
        category=InternshipCategory.OTHER,
        location="Remote",
        application_url=raw["url"],
        source_url=raw["url"],
        posted_date=date.today(),
    )


def _raise_for_bad(raw):
    if raw["title"] == "Bad":
        raise ValueError("simulated parse failure")
    return _parse(raw)
