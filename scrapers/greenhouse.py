from __future__ import annotations

import logging

from scrapers.base_scraper import BaseScraper
from scrapers.classification import classify_internship
from scrapers.http_utils import REQUEST_TIMEOUT_SECONDS, new_session
from scrapers.schemas import NormalizedInternship
from scrapers.text_utils import clean_html_description, normalize_location, parse_date_safe

logger = logging.getLogger(__name__)


class GreenhouseScraper(BaseScraper):
    """Shared scraper for any company hosted on Greenhouse's public Job Board API.

    Greenhouse (boards-api.greenhouse.io) exposes a public, unauthenticated
    JSON API meant for external job-board/aggregator consumption (robots.txt
    for that host only disallows /embed/). Introduced after confirming, by
    actually fetching three companies' data (Robinhood, Cloudflare, Braze),
    that the raw JSON schema is identical across all of them - title,
    location, offices, departments, absolute_url, content, first_published,
    application_deadline. Duplicating that fetch/parse logic per company
    would have meant three near-identical copies of the same code.

    A company scraper only needs to set `board_token` plus the usual
    BaseScraper company_slug/company_name/career_url/website_url - all
    fetching, filtering, and classification is shared here.
    """

    board_token: str

    def fetch_raw_listings(self) -> list[dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs?content=true"
        session = new_session()
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()["jobs"]

    def parse_listing(self, raw: dict) -> NormalizedInternship | None:
        title = raw["title"].strip()

        category = classify_internship(title)
        if category is None:
            return None

        return NormalizedInternship(
            title=title,
            description=clean_html_description(raw.get("content")),
            category=category,
            location=normalize_location(_extract_location(raw)),
            application_url=raw["absolute_url"],
            source_url=raw["absolute_url"],
            posted_date=parse_date_safe(raw.get("first_published")),
            application_deadline=parse_date_safe(raw.get("application_deadline")),
        )


def _extract_location(raw: dict) -> str | None:
    # Some Greenhouse boards (e.g. Cloudflare) set location.name to a
    # generic label like "In-Office" instead of a real place, while
    # `offices` reliably holds the actual office name. Prefer offices
    # when present. This matters for correctness, not just cosmetics:
    # Cloudflare posted two "Network Strategy Intern" listings with
    # identical titles but different offices (London vs Austin, TX) - if
    # both had normalized to "In-Office", they'd collapse into a single
    # dedupe_key and silently drop one of two real, distinct openings.
    offices = raw.get("offices") or []
    if offices and offices[0].get("name"):
        return offices[0]["name"].strip()
    raw_location = raw.get("location")
    if raw_location and raw_location.get("name"):
        return raw_location["name"].strip()
    return None
