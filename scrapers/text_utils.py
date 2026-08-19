from __future__ import annotations

import html
import logging
import re
from datetime import date, datetime

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_html_description(raw_content: str | None) -> str | None:
    """Shared by every ATS scraper: descriptions arrive as HTML (often
    itself HTML-entity-escaped, e.g. literal "&lt;div&gt;"). Unescape
    once, then strip tags down to plain text."""
    if not raw_content:
        return None
    unescaped = html.unescape(raw_content)
    text = BeautifulSoup(unescaped, "html.parser").get_text(separator=" ", strip=True)
    return text or None


def normalize_location(location: str | None) -> str | None:
    """Collapse whitespace variants (e.g. double spaces, stray tabs)
    that would otherwise make the same real-world office produce two
    different dedupe_key values across scraper runs. Deliberately does
    not rewrite content (e.g. abbreviating state names) - only
    formatting - so this stays safe to apply to every ATS's raw text
    without risking silently merging two different real locations."""
    if not location:
        return None
    normalized = re.sub(r"\s+", " ", location).strip()
    return normalized or None


def parse_date_safe(value: str | None) -> date | None:
    """Parse an ISO-ish date string, e.g. Greenhouse's `first_published`
    or Workday's `startDate`. Returns None (rather than raising) for
    anything unparseable, since a malformed date shouldn't fail an
    otherwise-valid listing."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        logger.warning("Could not parse date value: %r", value)
        return None
