from __future__ import annotations

import re

from backend.models.internship import InternshipCategory

# Word-boundary match so "International"/"Internal" don't false-positive
# on the substring "intern" (confirmed necessary during Phase 2 testing -
# a naive `"intern" in title.lower()` matched 8 non-internship
# "International ..." roles at Robinhood out of 9 "matches").
INTERN_TITLE_RE = re.compile(r"\bintern(ship)?\b", re.IGNORECASE)


# Phrases that must match as a PREFIX of a longer word - specifically,
# "...engineering intern" needs to also match "...Engineering
# Internship" (the word continues into "ship"). Everything else uses a
# full word-boundary match (see _keyword_pattern below): a trailing
# boundary is what stops a bare word like "sales" from wrongly matching
# mid-word inside "Salesforce" (found via testing during Phase 7 - a
# leading-boundary-only check let "Salesforce Administrator Intern"
# falsely land in the new Sales category, since "Sales" also starts a
# word boundary at the front of "Salesforce").
_PREFIX_MATCH_PHRASES = frozenset({"engineering intern", "engineer intern"})


def _keyword_pattern(phrase: str) -> re.Pattern[str]:
    boundary = r"\b" if phrase not in _PREFIX_MATCH_PHRASES else ""
    return re.compile(r"\b" + re.escape(phrase) + boundary, re.IGNORECASE)


def _normalize_for_matching(title: str) -> str:
    """Regex `\\b` treats underscores as word characters, so a raw title
    like Medtronic's "Cardiovascular _Marketing Intern" (a stray
    underscore from a messy ATS export) would NOT word-boundary-match
    "marketing" - the "_" right before "m" isn't a boundary. Found via
    real Phase 8 data. Replacing separator punctuation with spaces
    before matching fixes this without weakening the boundary check
    itself."""
    return re.sub(r"[_/]+", " ", title)


# Internship postings for technical roles this platform doesn't target.
# Checked after the intern-title match, so e.g. "Software Engineer
# Intern" is excluded even though it passes the intern check above.
EXCLUDE_KEYWORDS = (
    # Software/data/infra roles (Phase 2B - Cloudflare's "Research
    # Engineer Intern" wasn't caught by the original software-only list).
    "software engineer", "software engineering", "swe", "backend", "frontend",
    "full stack", "full-stack", "data engineer", "research engineer",
    "machine learning", "ml engineer", "security engineer", "site reliability",
    "sre", "devops", "infrastructure engineer", "qa engineer", "quality assurance",
    "ios", "android", "hardware engineer", "network engineer", "systems engineer",
    "data scientist",
    # Phase 7 additions - found via real postings from Rocket Lab (aerospace
    # hardware) and SpaceX. Neither company's technical-internship titles
    # were caught by the software-focused list above, and both would
    # otherwise have fallen into OTHER as if they were unclassified
    # *business* roles, which is misleading (OTHER should mean "a real
    # business function without a fixed category", not "a technical role
    # that slipped through"). "engineering intern"/"engineer intern" are
    # deliberately written without a trailing word boundary so they also
    # match as a prefix of "...Engineering Internship" / "...Engineer
    # Internship" titles (see _leading_boundary_pattern above) - this one
    # pair alone covers "Manufacturing/Development/Mechanical Engineering
    # Intern" (Rocket Lab), "Civil/Silicon/Graduate Engineer(ing)
    # Internship" (SpaceX), and "RF Test/Supplier Quality Engineer Intern"
    # (Rocket Lab) without needing a separate keyword for each variant.
    "engineering intern", "engineer intern",
    "avionics",              # Rocket Lab: "Avionics ... Intern" (no "engineer" in title)
    "flight software",       # Rocket Lab: "Flight Software Intern - Neutron"
    "flight analysis",       # Rocket Lab: "Flight Analysis Intern - Software"
    "mechanical development",  # Rocket Lab: "Neutron Mechanical Development Intern"
    "configuration management",  # Rocket Lab: "Electron Configuration Management Intern"
    # Phase 8 additions. "engineering intern"/"engineer intern" above
    # already excludes e.g. "Mechanical Engineering Intern", but not a
    # title like "Mechanical Engineer" with "Intern" appearing elsewhere
    # in the string - added explicitly for the technical disciplines a
    # business-internship aggregator should never surface.
    "mechanical engineer", "electrical engineer", "computer engineer",
    "embedded engineer", "embedded systems",
    "cyber security",        # AIA: "Intern, Cyber Security"
    "it intern",             # AIA/Chevron: bare "IT Intern" - IT helpdesk/systems, not a business function
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
    (InternshipCategory.FINANCE, (
        "finance", "financial", "treasury", "fp&a",
        # Phase 8: Invesco (investment management) postings like "Early
        # Career Intern - Investments (Bank Loans)" and "...(Risk)", and
        # AIA (insurance) postings like "Actuarial Valuation & Reporting
        # Intern", were all falling to OTHER - real, recurring investment/
        # risk-analysis roles that fit within Finance for this platform's
        # purposes rather than justifying their own separate categories
        # (too little distinct volume yet to split out, per the "only add
        # a category if there are enough real postings" rule).
        "investment", "investments", "risk", "actuarial", "equity", "equities",
    )),
    (InternshipCategory.ACCOUNTING, (
        "accounting", "audit",
        "tax",  # Phase 8: HCVT (tax/accounting firm) - "Tax Internship", "International Tax Internship", etc.
    )),
    (InternshipCategory.CONSULTING, ("consulting", "advisory", "professional services")),
    (InternshipCategory.MARKETING, ("marketing", "brand", "growth", "communications")),
    (InternshipCategory.SUPPLY_CHAIN, ("supply chain", "logistics", "procurement")),
    (InternshipCategory.OPERATIONS, ("operations", "ops")),
    (InternshipCategory.STRATEGY, ("strategy", "strategies", "strategic")),
    (InternshipCategory.HUMAN_RESOURCES, (
        "human resources", "people team", "talent acquisition", "recruiting",
        # Phase 7: Rocket Lab's "Learning & Development Intern" is a real,
        # legitimate HR sub-function (L&D) that the original keyword list
        # had no synonym for and would have fallen to OTHER.
        "learning & development", "learning and development",
    )),
    (InternshipCategory.PRODUCT_MANAGEMENT, ("product manager", "product management", "associate product manager")),
    (InternshipCategory.BUSINESS_ANALYTICS, ("business analyst", "business analytics", "market research", "data analyst", "analytics")),
    # Phase 7 addition: Braze's "Business Development Representative
    # Intern" (Phase 5) and Abbott's "Commercial Excellence Intern" /
    # SpotHopper's "Business Development Internship" (Phase 7) are real,
    # recurring postings across multiple companies that don't fit any
    # existing category - a legitimate taxonomy gap, not a bug to paper
    # over with a forced match into an unrelated category.
    (InternshipCategory.SALES, ("sales", "business development", "bdr", "account executive", "commercial excellence")),
    # Phase 8: Invesco's recurring "Early Career Intern - Real Estate
    # (Equity & Credit)" postings (multiple, across offices) - a distinct,
    # explicitly-suggested category (task Step 6) with enough real volume
    # to justify it, unlike Risk/Actuarial above.
    (InternshipCategory.REAL_ESTATE, ("real estate",)),
]

_EXCLUDE_PATTERNS = [(kw, _keyword_pattern(kw)) for kw in EXCLUDE_KEYWORDS]
_CATEGORY_PATTERNS: list[tuple[InternshipCategory, str, re.Pattern[str]]] = [
    (category, kw, _keyword_pattern(kw))
    for category, keywords in CATEGORY_KEYWORDS
    for kw in keywords
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

    normalized_title = _normalize_for_matching(title)

    if any(pattern.search(normalized_title) for _, pattern in _EXCLUDE_PATTERNS):
        return None

    best_category: InternshipCategory | None = None
    best_keyword_length = 0
    for category, keyword, pattern in _CATEGORY_PATTERNS:
        if len(keyword) > best_keyword_length and pattern.search(normalized_title):
            best_category = category
            best_keyword_length = len(keyword)

    return best_category or InternshipCategory.OTHER
