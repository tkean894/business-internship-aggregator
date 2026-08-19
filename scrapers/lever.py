from __future__ import annotations

import logging
from datetime import datetime, timezone

from scrapers.base_scraper import BaseScraper
from scrapers.classification import classify_internship
from scrapers.http_utils import REQUEST_TIMEOUT_SECONDS, new_session
from scrapers.schemas import NormalizedInternship
from scrapers.text_utils import clean_html_description, normalize_location

logger = logging.getLogger(__name__)


class LeverScraper(BaseScraper):
    """Shared scraper for any company hosted on Lever's public Postings
    API (Phase 8 - the platform's third ATS integration).

    Uses Lever's own officially documented, unauthenticated Postings API
    (`api.lever.co/v0/postings/{site}` - see github.com/lever/postings-api,
    maintained by Lever itself), explicitly designed to power public
    career sites and job-board syndication - the same category of public
    endpoint as Greenhouse's board API, just on a different host. This
    scraper only ever talks to `api.lever.co` (robots.txt: plain
    `Allow: /`, `Crawl-delay: 1`) and never Lever's separate
    `jobs.lever.co` hosted-posting-page host or its authenticated OAuth
    Data API (which requires credentials this project deliberately does
    not obtain).

    One request returns a company's entire posting list already, like
    Greenhouse and unlike Workday - no per-job detail request needed,
    so a single company run makes exactly one request to api.lever.co
    and the 1-second crawl-delay is trivially satisfied. If a second
    Lever company is ever added, revisit whether the scheduler's
    natural per-company spacing keeps consecutive api.lever.co requests
    at least 1 second apart.

    A company config only needs to set `site` plus the usual BaseScraper
    fields.
    """

    site: str

    def fetch_raw_listings(self) -> list[dict]:
        url = f"https://api.lever.co/v0/postings/{self.site}?mode=json"
        session = new_session()
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()

    def parse_listing(self, raw: dict) -> NormalizedInternship | None:
        title = raw["text"].strip()

        category = classify_internship(title)
        if category is None:
            return None

        categories = raw.get("categories") or {}
        posted_date = None
        created_at_ms = raw.get("createdAt")
        if created_at_ms:
            posted_date = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc).date()

        application_url = raw.get("applyUrl") or raw["hostedUrl"]

        return NormalizedInternship(
            title=title,
            description=clean_html_description(raw.get("description")),
            category=category,
            location=normalize_location(categories.get("location")),
            application_url=application_url,
            source_url=raw["hostedUrl"],
            posted_date=posted_date,
            application_deadline=None,  # not exposed by Lever's Postings API
        )
