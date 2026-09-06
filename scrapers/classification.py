from __future__ import annotations

import re

from backend.models.internship import InternshipCategory

# Word-boundary match so "International"/"Internal" don't false-positive
# on the substring "intern" (confirmed necessary during Phase 2 testing -
# a naive `"intern" in title.lower()` matched 8 non-internship
# "International ..." roles at Robinhood out of 9 "matches").
#
# "summer analyst" (Phase 10 Step 2): investment banking/financial
# services internships are frequently titled e.g. "Investment Banking
# Summer Analyst (Summer 2026)" or "Campus Recruiting - 2026 Investment
# Banking Summer Analyst - Restructuring NY" with no "intern"/
# "internship" anywhere in the title - confirmed across multiple real,
# unrelated companies' live postings during this phase's research (TD
# Securities, CIBC, Piper Sandler all titled this way; Truist and Texas
# Capital Bank happen to also append "(Internship)" to the same "Summer
# Analyst Program" phrasing, confirming it's the same role, just
# inconsistently labeled). This is an industry-standard synonym for a
# finance internship, not a one-off keyword for a single company's
# posting - "Summer Analyst" without "summer" (i.e. a full-time,
# post-graduation "Analyst" role) is a different, non-internship title
# and is unaffected since the phrase requires both words together.
INTERN_TITLE_RE = re.compile(r"\b(intern(ship)?|summer analyst)\b", re.IGNORECASE)


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
    # Phase 10 Step 7 additions - found via real Booz Allen Hamilton
    # postings that were falling to OTHER instead of being excluded as
    # technical: "Software Developer Intern"/"AI Software Developer
    # Intern" (a real, common alternate phrasing for "Software Engineer"
    # not covered by that keyword) and "Cybersecurity Analyst Intern"
    # (the one-word spelling - the existing "cyber security" two-word
    # phrase doesn't match it; both spellings are kept rather than one
    # replacing the other).
    "software developer", "cybersecurity",
    # Phase 10 Step 9 additions - found via a full-dataset audit of the
    # Other bucket. All confirmed technical/vocational disciplines outside
    # this platform's business-internship scope, not business functions
    # that happen to share a word with an existing exclusion:
    "hvac", "electrician",  # JLL: "HVAC Technician Intern", "Electrician Technician Intern" (13 real postings)
    # JLL/GE Aerospace/Mondelez: "Maintenance Technician", "Test
    # Technician", "Technician Safety Intern" (19 real postings, all
    # skilled-trade/vocational roles - checked for false positives
    # against the full active dataset, none found).
    "technician",
    # Applied Materials/Mondelez use "Industrial Engineer"; GlobalFoundries/
    # UPS use the gerund "Industrial Engineering" for the same discipline -
    # both forms needed since the word-boundary match doesn't bridge them.
    "industrial engineer", "industrial engineering",
    # GM/Airbus use the gerund "Manufacturing Engineering"; GE Aerospace
    # uses "Manufacturing Engineer" - neither is caught by the existing
    # "engineering intern"/"engineer intern" pair above, which requires
    # "Engineering"/"Engineer" to sit immediately next to "Intern" - these
    # titles instead put "Intern" first, e.g. "2027 Summer Intern -
    # Manufacturing Engineering - Body Center" / "Intern - Airfoils
    # Manufacturing Engineer". Found via the Step 16 quality sample after
    # the gerund-only form was already added, confirming both forms need
    # their own keyword.
    "manufacturing engineering", "manufacturing engineer",
    "process engineering",  # GlobalFoundries/Mondelez: "Implant Process Engineering", "Process Engineering"
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
        # Phase 10 Step 6: real, recurring across TWO unrelated companies
        # (PNC's "Corporate & Institutional Banking Undergraduate Intern -
        # Commercial & Corporate Banking", Wells Fargo's "Consumer Banking
        # and Lending Summer Internship" / "Commercial Banking Summer
        # Internship") - all were falling to OTHER despite being
        # unambiguously financial-services roles. Deliberately NOT adding
        # "capital markets" alongside it - it would (as the longer match)
        # override the existing, already-correct "analytics" match on
        # real postings like Wells Fargo's "Quantitative Analytics Summer
        # Internship ... Capital Markets (PhD)", which is genuinely more
        # an analytics program than a banking one.
        "banking",
        # Phase 10 Step 7: Citigroup's "Wealth - Citigold, Summer Analyst"
        # and "Wealth - Private Bank, Summer Analyst" postings (4 real,
        # recurring instances) were falling to OTHER - Wealth Management
        # is an explicit target business function for this platform, and
        # "wealth" as a bare word in an internship title (already
        # pre-filtered to real internship postings) unambiguously means
        # wealth management, not a false-positive risk.
        "wealth",
        # Phase 10 Step 9: Northern Trust/Blackstone/IFF's "Credit Intern"
        # / "Credit and Insurance ... Summer Analyst" postings (5 real
        # instances) - standard finance/banking sub-function (credit
        # analysis/risk), previously falling to OTHER. Checked against the
        # full active dataset first: every other "credit"-containing title
        # already resolves correctly via a longer keyword ("banking",
        # "real estate", "strategy", "analytics"), so this only reaches
        # titles with no stronger existing signal.
        "credit",
    )),
    (InternshipCategory.ACCOUNTING, (
        "accounting", "audit",
        "tax",  # Phase 8: HCVT (tax/accounting firm) - "Tax Internship", "International Tax Internship", etc.
        # Phase 10 Step 8: PwC's "Assurance" practice (Big 4 industry-
        # standard term for audit/attestation services) - ~30 real,
        # recurring postings ("Intern - Assurance", "Financial Services
        # Assurance - Off-Cycle Internship", "Assurance CPA - Summer
        # Intern") were falling to OTHER despite being unambiguously
        # accounting/audit roles. Verified zero regressions against
        # existing data: same length as FINANCE's "financial" keyword,
        # but CATEGORY_KEYWORDS iterates FINANCE first and the longest-
        # match comparison is strict `>`, so titles like "Assurance
        # (Financial Services)" that already correctly matched Finance
        # keep doing so.
        "assurance",
        # Phase 10 Step 9: PwC's "Junior Auditor (Intern)" postings (3 real
        # instances) - "audit" above requires a trailing word boundary, so
        # it doesn't match the "-or" noun form. Disney's one "...Auditor
        # Intern" posting already correctly matches Operations via the
        # longer "operations" keyword and is unaffected by this addition.
        "auditor",
    )),
    (InternshipCategory.CONSULTING, (
        "consulting", "advisory", "professional services",
        # Phase 10 Step 6: Marsh McLennan's Oliver Wyman postings are
        # frequently titled "... Consultant Intern ..." or "Intern
        # Consultant" (the noun "Consultant", not "Consulting") - a real,
        # recurring pattern at a company whose entire business IS
        # consulting, previously falling to OTHER.
        "consultant",
    )),
    (InternshipCategory.MARKETING, ("marketing", "brand", "growth", "communications")),
    (InternshipCategory.SUPPLY_CHAIN, (
        "supply chain", "logistics", "procurement",
        # Phase 10 Step 9: P&G/GM's "Purchasing Intern" postings (2 real
        # instances) - "purchasing" is the standard retail/manufacturing
        # synonym for procurement.
        "purchasing",
    )),
    (InternshipCategory.OPERATIONS, (
        "operations", "ops",
        # Phase 10 Step 8: Target's "Operation Manager Intern" postings
        # (30 real, recurring instances across distribution centers) use
        # the singular "Operation", not "Operations" - the existing
        # keyword requires the plural and all 30 were falling to OTHER.
        # The same company's "Operations Manager Intern" (plural) titles
        # already classified correctly, confirming this was purely a
        # singular/plural gap, not a different role type. Since
        # "operation" (9 chars) is longer than SALES's "sales" (5 chars),
        # this does reclassify one existing title, "Intern, Content Sales
        # Operation", from Sales to Operations - a genuinely ambiguous
        # "Sales Operations"-style role either way, and a reasonable
        # trade for correctly fixing 30 other postings.
        "operation",
        # Phase 10 Step 9: Target's "Store Executive Intern (Store
        # Leadership Intern)" - a single retail-management internship
        # program posted separately per store location, discovered as 80
        # (!) near-identical active postings all falling to OTHER - by far
        # the single largest fix in this phase. "Store Leadership"/"Store
        # Executive" are industry-standard retail internship-program names
        # (also used by other large retailers), not Target-specific
        # jargon. Both variants are kept since 2 of the 80 postings say
        # "Stores Executive" (plural) rather than "Store Executive" -
        # "store leadership" alone already covers all 80, "store
        # executive" is kept for robustness if a future posting drops the
        # "(Store Leadership Intern)" parenthetical.
        "store leadership", "store executive",
    )),
    (InternshipCategory.STRATEGY, ("strategy", "strategies", "strategic")),
    (InternshipCategory.HUMAN_RESOURCES, (
        "human resources", "people team", "talent acquisition", "recruiting",
        # Phase 7: Rocket Lab's "Learning & Development Intern" is a real,
        # legitimate HR sub-function (L&D) that the original keyword list
        # had no synonym for and would have fallen to OTHER.
        "learning & development", "learning and development",
        # Phase 10 Step 7: Kraft Heinz's bare "HR Intern" posting was
        # falling to OTHER - the existing "human resources" keyword
        # requires the spelled-out phrase. Same short-abbreviation
        # precedent as "ops" under Operations above; word-boundary
        # matched so it only fires on "HR" as its own word, not embedded
        # inside another word.
        "hr",
        # Phase 10 Step 9: GlobalFoundries' "HRBP Intern" - "HR Business
        # Partner" is a standard, unambiguous HR title abbreviation (only
        # 1 real instance found, but zero plausible false-positive risk,
        # unlike a broader term).
        "hrbp",
    )),
    (InternshipCategory.PRODUCT_MANAGEMENT, ("product manager", "product management", "associate product manager")),
    (InternshipCategory.BUSINESS_ANALYTICS, (
        "business analyst", "business analytics", "market research", "data analyst", "analytics",
        # Phase 10 Step 9: P&G's "Business Intelligence & Data Analysis
        # Internship" - standard synonym for business analytics. Longer
        # than "analytics" (9 chars) so it doesn't change Medline's
        # already-correct "IT Business Intelligence Development/Analytics
        # Intern" match, just gives it a more specific reason to land in
        # the same category.
        "business intelligence",
    )),
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
    # Phase 10 Step 9: a dedicated Legal category, added after auditing the
    # full active dataset for legal-related titles - see InternshipCategory.LEGAL
    # for the cross-company evidence. "attorney"/"counsel"/"paralegal" have
    # zero matches in the current dataset but are standard, unambiguous
    # legal-profession terms kept for when future postings use them; the
    # more general "contracts" was deliberately NOT added since it's
    # equally common as a Supply Chain/procurement term and only "legal"/
    # "law"/"litigation" actually appeared in real legal postings.
    (InternshipCategory.LEGAL, ("legal", "law", "litigation", "paralegal", "attorney", "counsel")),
]

_EXCLUDE_PATTERNS = [(kw, _keyword_pattern(kw)) for kw in EXCLUDE_KEYWORDS]
_CATEGORY_PATTERNS: list[tuple[InternshipCategory, str, re.Pattern[str]]] = [
    (category, kw, _keyword_pattern(kw))
    for category, keywords in CATEGORY_KEYWORDS
    for kw in keywords
]

# Phase 10 Step 9: some keywords are only reliable within a specific
# company industry. "Capital Markets" means real-estate investment
# sales/financing at a real-estate services firm (JLL: 24 real, recurring
# postings, e.g. "Capital Markets Summer 2027 Internship - Miami, FL")
# but investment-banking capital markets at a bank (Barclays, Citigroup,
# Deutsche Bank, Wells Fargo, PNC) or a Big 4 advisory practice (PwC) - a
# full-dataset scan found 37 "capital markets" matches across 8 companies
# spanning Real Estate/Finance/Accounting, so a global keyword in any one
# category would misclassify the other two. Scoping by Company.industry
# (set by every scraper - see BaseScraper.industry) rather than by company
# slug generalizes to any other real-estate-industry company (Prologis,
# Simon Property Group are already in the registry with the same
# industry, and were checked for regressions: 0 and 1 Other postings
# respectively, neither containing "capital markets").
INDUSTRY_SCOPED_CATEGORY_KEYWORDS: dict[str, list[tuple[InternshipCategory, tuple[str, ...]]]] = {
    "Real Estate": [
        (InternshipCategory.REAL_ESTATE, ("capital markets",)),
    ],
}

_INDUSTRY_SCOPED_PATTERNS: dict[str, list[tuple[InternshipCategory, str, re.Pattern[str]]]] = {
    industry: [(category, kw, _keyword_pattern(kw)) for category, keywords in rules for kw in keywords]
    for industry, rules in INDUSTRY_SCOPED_CATEGORY_KEYWORDS.items()
}


def classify_internship(title: str, *, industry: str | None = None) -> InternshipCategory | None:
    """Decide whether a job title is a relevant business internship, and
    if so, which category it belongs to.

    Returns None if the title isn't an internship at all, or is an
    internship for a technical role outside this platform's scope.
    Otherwise returns the best-matching category, falling back to OTHER
    when no specific keyword matches - a legitimate outcome for real
    postings (e.g. "GRC Team Intern", which doesn't fit any fixed
    category) rather than a bug to paper over with a forced match.

    `industry` is optional and only widens the keyword set with the
    company's industry-scoped rules (see INDUSTRY_SCOPED_CATEGORY_KEYWORDS)
    - callers that don't pass it (e.g. existing tests) get identical
    behavior to before this parameter was added.
    """
    if not INTERN_TITLE_RE.search(title):
        return None

    normalized_title = _normalize_for_matching(title)

    if any(pattern.search(normalized_title) for _, pattern in _EXCLUDE_PATTERNS):
        return None

    patterns = _CATEGORY_PATTERNS
    if industry in _INDUSTRY_SCOPED_PATTERNS:
        patterns = patterns + _INDUSTRY_SCOPED_PATTERNS[industry]

    best_category: InternshipCategory | None = None
    best_keyword_length = 0
    for category, keyword, pattern in patterns:
        if len(keyword) > best_keyword_length and pattern.search(normalized_title):
            best_category = category
            best_keyword_length = len(keyword)

    return best_category or InternshipCategory.OTHER
