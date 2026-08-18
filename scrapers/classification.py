from __future__ import annotations

import re

from backend.models.internship import InternshipCategory

# Word-boundary match so "International"/"Internal" don't false-positive
# on the substring "intern" (confirmed necessary during Phase 2 testing -
# a naive `"intern" in title.lower()` matched 8 non-internship
# "International ..." roles at Robinhood out of 9 "matches").
INTERN_TITLE_RE = re.compile(r"\bintern(ship)?\b", re.IGNORECASE)

# Internship postings for technical roles this platform doesn't target.
# Checked after the intern-title match, so e.g. "Software Engineer
# Intern" is excluded even though it passes the intern check above.
# "research engineer" was added after Phase 2B testing found Cloudflare's
# "Research Engineer Intern" postings weren't caught by the prior list.
EXCLUDE_KEYWORDS = (
    "software engineer", "software engineering", "swe", "backend", "frontend",
    "full stack", "full-stack", "data engineer", "research engineer",
    "machine learning", "ml engineer", "security engineer", "site reliability",
    "sre", "devops", "infrastructure engineer", "qa engineer", "quality assurance",
    "ios", "android", "hardware engineer", "network engineer", "systems engineer",
    "data scientist",
)

# (category, keyword) pairs. Deliberately keyed on specific function terms
# (e.g. "market research", "supply chain", "professional services") rather
# than the literal word "business", since a title containing "business"
# doesn't reliably indicate which business function - or any - it belongs
# to. When multiple keywords match the same title, the LONGEST matching
# keyword wins (see classify_internship), so a specific phrase like
# "market research" outranks a generic single word like "strategy". This
# fixed a real Phase 2 miscategorization: "Market Research Strategy
# Intern" was landing in Strategy purely because of keyword list order,
# not because "strategy" was the more meaningful signal.
CATEGORY_KEYWORDS: list[tuple[InternshipCategory, tuple[str, ...]]] = [
    (InternshipCategory.FINANCE, ("finance", "financial", "treasury", "fp&a")),
    (InternshipCategory.ACCOUNTING, ("accounting", "audit")),
    (InternshipCategory.CONSULTING, ("consulting", "advisory", "professional services")),
    (InternshipCategory.MARKETING, ("marketing", "brand", "growth", "communications")),
    (InternshipCategory.SUPPLY_CHAIN, ("supply chain", "logistics", "procurement")),
    (InternshipCategory.OPERATIONS, ("operations", " ops")),
    (InternshipCategory.STRATEGY, ("strategy", "strategic")),
    (InternshipCategory.HUMAN_RESOURCES, ("human resources", "people team", "talent acquisition", "recruiting")),
    (InternshipCategory.PRODUCT_MANAGEMENT, ("product manager", "product management", "associate product manager")),
    (InternshipCategory.BUSINESS_ANALYTICS, ("business analyst", "business analytics", "market research", "data analyst", "analytics")),
]


def classify_internship(title: str) -> InternshipCategory | None:
    """Decide whether a job title is a relevant business internship, and
    if so, which category it belongs to.

    Returns None if the title isn't an internship at all, or is an
    internship for a technical role outside this platform's scope.
    Otherwise returns the best-matching category, falling back to OTHER
    when no specific keyword matches - a legitimate outcome for real
    postings (e.g. "GRC Team Intern", which doesn't fit any fixed
    category) rather than a bug to paper over with a forced match.
    """
    if not INTERN_TITLE_RE.search(title):
        return None

    lowered = title.lower()
    if any(keyword in lowered for keyword in EXCLUDE_KEYWORDS):
        return None

    best_category: InternshipCategory | None = None
    best_keyword_length = 0
    for category, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            if keyword in lowered and len(keyword) > best_keyword_length:
                best_category = category
                best_keyword_length = len(keyword)

    return best_category or InternshipCategory.OTHER
