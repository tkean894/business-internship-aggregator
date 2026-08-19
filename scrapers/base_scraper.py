from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.database.utils import compute_dedupe_key
from backend.models import Company, Internship, ScraperRun, ScraperRunStatus
from scrapers.schemas import NormalizedInternship, validate_normalized_internship

logger = logging.getLogger(__name__)


@dataclass
class ScraperRunResult:
    """Outcome of a single scraper run, for logging and manual verification."""

    company_slug: str
    raw_count: int = 0
    relevant_count: int = 0
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    deactivated_count: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"[{self.company_slug}] raw={self.raw_count} relevant={self.relevant_count} "
            f"created={self.created_count} updated={self.updated_count} "
            f"skipped={self.skipped_count} deactivated={self.deactivated_count} "
            f"errors={self.error_count}"
        )


class BaseScraper(abc.ABC):
    """Shared lifecycle every company scraper follows.

    A subclass only needs to implement `fetch_raw_listings` (however the
    company's site needs to be reached - Playwright for JS-rendered
    sites, a plain HTTP request where a public API exists, etc.) and
    `parse_listing` (turn one raw item into a NormalizedInternship, or
    return None to filter it out). Company lookup, deduplication,
    insert/update, and per-listing error isolation all live here so
    they behave identically across every company.
    """

    company_slug: str
    company_name: str
    career_url: str
    website_url: str | None = None
    industry: str | None = None

    def setup(self) -> None:
        """Optional hook for subclasses that need to open resources
        (e.g. launch a Playwright browser). No-op by default."""

    def teardown(self) -> None:
        """Optional hook to release resources opened in setup()."""

    @abc.abstractmethod
    def fetch_raw_listings(self) -> list[dict]:
        """Return raw listing data from the company's career site."""

    @abc.abstractmethod
    def parse_listing(self, raw: dict) -> NormalizedInternship | None:
        """Convert one raw listing into a NormalizedInternship.

        Return None if the listing should be skipped (not an
        internship, not business-relevant, or unparseable).
        """

    def run(self) -> ScraperRunResult:
        result = ScraperRunResult(company_slug=self.company_slug)
        started_at = datetime.now(timezone.utc)
        logger.info("Starting scraper: %s", self.company_slug)

        self.setup()
        try:
            try:
                raw_listings = self.fetch_raw_listings()
            except Exception as exc:
                # A network/HTTP failure fetching the list itself (after
                # http_utils' own retry/backoff has already been
                # exhausted) is a hard failure for this company's run -
                # nothing has been written yet, so no data is at risk.
                logger.error("%s: failed to fetch listings (%s): %s", self.company_slug, type(exc).__name__, exc)
                self._record_run(result, started_at, ScraperRunStatus.FAILED, error_message=str(exc)[:2000])
                raise
            result.raw_count = len(raw_listings)
            logger.info("%s: fetched %d raw listings", self.company_slug, result.raw_count)

            try:
                session = SessionLocal()
                try:
                    company = self._get_or_create_company(session)
                    seen_dedupe_keys: set[str] = set()

                    for raw in raw_listings:
                        try:
                            parsed = self.parse_listing(raw)
                        except Exception as exc:  # noqa: BLE001 - isolate one bad listing from the rest of the run
                            result.error_count += 1
                            result.errors.append(f"parse error: {exc}")
                            logger.warning("%s: failed to parse a listing: %s", self.company_slug, exc)
                            continue

                        if parsed is None:
                            result.skipped_count += 1
                            continue

                        problems = validate_normalized_internship(parsed)
                        if problems:
                            result.error_count += 1
                            result.errors.append(f"validation failed for {parsed.title!r}: {'; '.join(problems)}")
                            logger.warning(
                                "%s: rejected invalid listing %r: %s", self.company_slug, parsed.title, "; ".join(problems)
                            )
                            continue

                        dedupe_key = compute_dedupe_key(company.id, parsed.title, parsed.location)
                        if dedupe_key in seen_dedupe_keys:
                            # Two DIFFERENT postings from this same run
                            # produced the same dedupe_key - i.e. identical
                            # title + location, a known, documented
                            # limitation of this hashing strategy (see
                            # "Deduplication Strategy" in database/schema.sql).
                            # Observed for real with Rocket Lab, which runs
                            # two distinct "Business Analyst Intern - Supply
                            # Chain" reqs at the same office. There is no way
                            # to tell them apart from title+location alone,
                            # so the second is skipped (not silently - logged
                            # and counted) rather than crashing the whole
                            # company's run on a unique-constraint violation.
                            result.error_count += 1
                            result.errors.append(
                                f"duplicate dedupe_key within this run for {parsed.title!r} at "
                                f"{parsed.location!r} - cannot distinguish from another listing with "
                                f"the same title+location; skipped"
                            )
                            logger.warning(
                                "%s: skipping listing with title+location matching another listing "
                                "in this run: %r at %r", self.company_slug, parsed.title, parsed.location
                            )
                            continue

                        result.relevant_count += 1
                        self._upsert_internship(session, company, parsed, result, dedupe_key)
                        seen_dedupe_keys.add(dedupe_key)

                    # A listing still in the DB as active but absent from this
                    # run's raw listings is no longer posted - mark it inactive
                    # rather than deleting (historical data stays queryable).
                    # Only runs here if fetch_raw_listings() succeeded above, so
                    # a scraper that fails outright never wipes out its company's
                    # listings.
                    stale_query = session.query(Internship).filter_by(company_id=company.id, is_active=True)
                    if seen_dedupe_keys:
                        stale_query = stale_query.filter(~Internship.dedupe_key.in_(seen_dedupe_keys))
                    still_active = stale_query.all()
                    for internship in still_active:
                        internship.is_active = False
                        result.deactivated_count += 1

                    session.commit()
                finally:
                    session.close()
            except Exception as exc:
                # Fetch succeeded but something in DB processing failed
                # (e.g. a constraint violation, a lost connection mid-run).
                # Treated as a hard failure too - upstream callers (the
                # scheduler) should know this company's data may be stale.
                logger.error("%s: database processing failed (%s): %s", self.company_slug, type(exc).__name__, exc)
                self._record_run(result, started_at, ScraperRunStatus.FAILED, error_message=str(exc)[:2000])
                raise
        finally:
            self.teardown()

        self._record_run(result, started_at, ScraperRunStatus.SUCCESS, error_message=None)
        logger.info(result.summary())
        return result

    def _record_run(
        self,
        result: ScraperRunResult,
        started_at: datetime,
        status: ScraperRunStatus,
        error_message: str | None,
    ) -> None:
        """Persist this run's outcome (Phase 7, Step 8). Uses its own
        short-lived session, independent of the main working session
        above, so a run's metrics are still recorded even when that
        session was never opened (a fetch failure) or already closed."""
        session = SessionLocal()
        try:
            session.add(
                ScraperRun(
                    company_slug=self.company_slug,
                    scraper_name=type(self).__name__,
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    status=status,
                    raw_count=result.raw_count,
                    relevant_count=result.relevant_count,
                    created_count=result.created_count,
                    updated_count=result.updated_count,
                    deactivated_count=result.deactivated_count,
                    skipped_count=result.skipped_count,
                    error_count=result.error_count,
                    error_message=error_message,
                )
            )
            session.commit()
        except Exception:  # noqa: BLE001 - recording metrics must never mask the original failure
            logger.exception("%s: failed to record scraper_runs row", self.company_slug)
        finally:
            session.close()

    def _get_or_create_company(self, session: Session) -> Company:
        company = session.query(Company).filter_by(slug=self.company_slug).one_or_none()
        if company is None:
            company = Company(
                name=self.company_name,
                slug=self.company_slug,
                career_url=self.career_url,
                website_url=self.website_url,
                industry=self.industry,
            )
            session.add(company)
            session.flush()  # assign company.id for use below
            logger.info("%s: created company record (id=%d)", self.company_slug, company.id)
        elif company.industry != self.industry:
            # Backfills industry on companies created before Phase 8, and
            # picks up a corrected value if a company config's industry
            # changes later - cheap to refresh every run rather than
            # requiring a one-off manual migration script.
            company.industry = self.industry
        return company

    def _upsert_internship(
        self,
        session: Session,
        company: Company,
        parsed: NormalizedInternship,
        result: ScraperRunResult,
        dedupe_key: str,
    ) -> None:
        existing = session.query(Internship).filter_by(dedupe_key=dedupe_key).one_or_none()
        now = datetime.now(timezone.utc)

        if existing is None:
            session.add(
                Internship(
                    company_id=company.id,
                    title=parsed.title,
                    description=parsed.description,
                    category=parsed.category,
                    location=parsed.location,
                    employment_type=parsed.employment_type,
                    application_url=parsed.application_url,
                    source_url=parsed.source_url,
                    posted_date=parsed.posted_date,
                    application_deadline=parsed.application_deadline,
                    dedupe_key=dedupe_key,
                    first_seen_at=now,
                    last_seen_at=now,
                )
            )
            result.created_count += 1
        else:
            existing.description = parsed.description
            existing.category = parsed.category
            existing.employment_type = parsed.employment_type
            existing.application_url = parsed.application_url
            existing.source_url = parsed.source_url
            existing.posted_date = parsed.posted_date
            existing.application_deadline = parsed.application_deadline
            existing.is_active = True
            existing.last_seen_at = now
            result.updated_count += 1
