from __future__ import annotations

import hashlib
import re


def normalize_text(value: str | None) -> str:
    """Lowercase, strip, collapse whitespace, and drop punctuation.

    Used to build a stable comparison key for values that legitimately
    vary in formatting between scraper runs (e.g. "Indianapolis, IN"
    vs "Indianapolis,  IN").
    """
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def compute_dedupe_key(company_id: int, title: str, location: str | None) -> str:
    """Compute the internships.dedupe_key value.

    See database/schema.sql "Deduplication Strategy" for the reasoning
    behind using company + normalized title + normalized location
    instead of a raw URL.
    """
    raw = f"{company_id}|{normalize_text(title)}|{normalize_text(location)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
