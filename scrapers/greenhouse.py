from __future__ import annotations

import html
import logging
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from scrapers.classification import classify_internship
from scrapers.schemas import NormalizedInternship

logger = logging.getLogger(__name__)

REQUEST_HEADERS = {"User-Agent": "BusinessInternshipAggregator/0.1 (educational project)"}
REQUEST_TIMEOUT_SECONDS = 30


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
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()["jobs"]

    def parse_listing(self, raw: dict) -> NormalizedInternship | None:
        title = raw["title"].strip()

        category = classify_internship(title)
        if category is None:
            return None

        return NormalizedInternship(
            title=title,
            description=_clean_description(raw.get("content")),
            category=category,
            location=_extract_location(raw),
            application_url=raw["absolute_url"],
            source_url=raw["absolute_url"],
            posted_date=_parse_date(raw.get("first_published")),
            application_deadline=_parse_date(raw.get("application_deadline")),
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


def _clean_description(raw_content: str | None) -> str | None:
    """Greenhouse's `content` field is HTML, itself HTML-entity-escaped
    (e.g. literal "&lt;div&gt;"). Unescape once, then strip tags."""
    if not raw_content:
        return None
    unescaped = html.unescape(raw_content)
    text = BeautifulSoup(unescaped, "html.parser").get_text(separator=" ", strip=True)
    return text or None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        logger.warning("Could not parse date value: %r", value)
        return None
