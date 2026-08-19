"""Phase 10 Step 1 - Company Registry & Expansion Architecture.

This module is a PLANNING / TRACKING artifact, not a scraper. It records
every company under consideration for the Top-200 business-internship
expansion, independent of whether a scraper has been implemented for it
yet. It intentionally does NOT duplicate `backend/models/company.py`
(that table only exists for companies with real scraped data - name,
slug, career_url, website_url, industry, is_active - and is populated by
`BaseScraper._get_or_create_company()` on each scraper run, never by
this file directly). This registry adds the fields that DB table has no
reason to carry: ATS platform + per-ATS identifiers, implementation/
verification status, priority tier, and research notes/evidence - all
needed to plan and safely scale the *scraper* side, none of it meaningful
for the runtime Company row.

See docs/architecture.md ("Company Registry & Expansion Architecture",
Phase 10) for the full design rationale, tiering policy, and compliance
rules this file encodes, and docs/roadmap.md (Phase 10) for the rollout
plan.

Compliance rule encoded by CompanyStatus.NEEDS_REVIEW: a company is only
promoted to READY (and later IMPLEMENTED) once its ATS access has been
confirmed to be a public, unauthenticated, officially-documented-or-
equivalent endpoint - the same bar applied to Greenhouse's board API,
Workday's CXS API, and Lever's Postings API in Phases 2-8. If that isn't
clearly true (unclear robots.txt, only found via an aggregator rather
than the ATS host itself, requires auth, etc.) the company stays at
NEEDS_REVIEW rather than being forced through.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ATSPlatform(str, Enum):
    GREENHOUSE = "greenhouse"
    WORKDAY = "workday"
    LEVER = "lever"
    UNKNOWN = "unknown"  # candidate company, ATS platform not yet identified


class CompanyTier(int, Enum):
    """Priority tier for implementation order. Lower number = higher
    priority. Tiering is about sequencing, not company "quality" - a
    Tier 3 company is just as real as a Tier 1 one, it simply needs more
    work (exact identifier confirmation, lower observed posting volume,
    smaller name recognition) before it's worth spending a scraper slot
    on relative to other candidates.
    """

    TIER_1 = 1  # implemented and already running in production today
    TIER_2 = 2  # exact ATS identifier confirmed via direct evidence this phase; large/recognizable employer; ready to implement next with minimal extra research
    TIER_3 = 3  # real company + ATS platform identified with reasonable confidence, but exact identifier and/or current posting volume not independently confirmed this phase
    TIER_4 = 4  # candidate only - ATS platform unconfirmed, evidence too indirect, or access legitimacy unclear; Needs Review before any further work


class CompanyStatus(str, Enum):
    IMPLEMENTED = "implemented"  # scraper exists in scrapers/companies/ and runs in production
    READY = "ready"  # ATS config (platform + exact token/tenant/site) verified this phase; not yet implemented
    RESEARCHED = "researched"  # company + ATS platform identified with real evidence; exact identifier and/or public-access status not independently re-confirmed this phase
    NEEDS_REVIEW = "needs_review"  # access legitimacy and/or exact ATS identifier is unclear or unconfirmed - do not implement until resolved
    EXCLUDED = "excluded"  # considered and deliberately rejected (not a direct employer, non-US-focused program, disallowed access, etc.)


@dataclass(frozen=True)
class CompanyRecord:
    name: str
    slug: str
    industry: str
    ats: ATSPlatform
    tier: CompanyTier
    status: CompanyStatus
    career_url: str | None = None
    website_url: str | None = None
    # Greenhouse: {"board_token": "..."}
    # Workday:    {"tenant": "...", "site": "..."} (optionally "intern_facet_id")
    # Lever:      {"site": "..."}
    ats_config: dict = field(default_factory=dict)
    notes: str = ""
    scraper_module: str | None = None  # e.g. "scrapers.companies.hcvt", set only when status == IMPLEMENTED


# ---------------------------------------------------------------------------
# Tier 1 - Implemented, running in production today (16 companies).
# Values pulled directly from scrapers/companies/*.py, not re-typed from
# memory, so this registry cannot silently drift from the real configs.
# ---------------------------------------------------------------------------

_TIER_1: list[CompanyRecord] = [
    CompanyRecord(
        name="Abbott Laboratories", slug="abbott", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://abbott.wd5.myworkdayjobs.com/abbottcareers",
        website_url="https://www.abbott.com",
        ats_config={"tenant": "abbott", "site": "abbottcareers", "intern_facet_id": "d0663057a84410077d944a83d8896dd3"},
        scraper_module="scrapers.companies.abbott",
    ),
    CompanyRecord(
        name="AIA Group Limited", slug="aia", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://aia.wd3.myworkdayjobs.com/External",
        website_url="https://www.aia.com",
        ats_config={"tenant": "aia", "site": "External", "intern_facet_id": "bd3d6b20175f01ed58af1567352c2c0d"},
        scraper_module="scrapers.companies.aia",
    ),
    CompanyRecord(
        name="Applied Materials, Inc.", slug="applied-materials", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://amat.wd1.myworkdayjobs.com/External",
        website_url="https://www.appliedmaterials.com",
        ats_config={"tenant": "amat", "site": "External", "intern_facet_id": "ba9df317f7ac456da2faff4fd6a521c8"},
        scraper_module="scrapers.companies.appliedmaterials",
    ),
    CompanyRecord(
        name="Assurant, Inc.", slug="assurant", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://assurant.wd1.myworkdayjobs.com/Assurant_Careers",
        website_url="https://www.assurant.com",
        ats_config={"tenant": "assurant", "site": "Assurant_Careers", "intern_facet_id": "48706393987501e4fbdb24f7940b8109"},
        scraper_module="scrapers.companies.assurant",
    ),
    CompanyRecord(
        name="Braze, Inc.", slug="braze", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/braze",
        website_url="https://www.braze.com",
        ats_config={"board_token": "braze"},
        scraper_module="scrapers.companies.braze",
    ),
    CompanyRecord(
        name="Chevron Corporation", slug="chevron", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://chevron.wd5.myworkdayjobs.com/jobs",
        website_url="https://www.chevron.com",
        ats_config={"tenant": "chevron", "site": "jobs", "intern_facet_id": "3cd342d9804f01e3bd250104bb00c80e"},
        scraper_module="scrapers.companies.chevron",
    ),
    CompanyRecord(
        name="Cloudflare, Inc.", slug="cloudflare", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/cloudflare",
        website_url="https://www.cloudflare.com",
        ats_config={"board_token": "cloudflare"},
        scraper_module="scrapers.companies.cloudflare",
    ),
    CompanyRecord(
        name="HCVT LLP", slug="hcvt", industry="Consulting",
        ats=ATSPlatform.LEVER, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://jobs.lever.co/hcvt",
        website_url="https://www.hcvt.com",
        ats_config={"site": "hcvt"},
        scraper_module="scrapers.companies.hcvt",
    ),
    CompanyRecord(
        name="Invesco Ltd.", slug="invesco", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://invesco.wd1.myworkdayjobs.com/ivzearlycareers",
        website_url="https://www.invesco.com",
        ats_config={"tenant": "invesco", "site": "ivzearlycareers", "intern_facet_id": "97a56ab3ad0b10186c046d05f3ee0001"},
        scraper_module="scrapers.companies.invesco",
    ),
    CompanyRecord(
        name="Medtronic plc", slug="medtronic", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://medtronic.wd1.myworkdayjobs.com/MedtronicCareers",
        website_url="https://www.medtronic.com",
        ats_config={"tenant": "medtronic", "site": "MedtronicCareers", "intern_facet_id": "6726e368deda465eb362a1203261d1e5"},
        scraper_module="scrapers.companies.medtronic",
    ),
    CompanyRecord(
        name="Red Ventures", slug="redventures", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/redventures",
        website_url="https://www.redventures.com",
        ats_config={"board_token": "redventures"},
        scraper_module="scrapers.companies.redventures",
    ),
    CompanyRecord(
        name="Robinhood Markets, Inc.", slug="robinhood", industry="Financial Services",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/robinhood",
        website_url="https://robinhood.com",
        ats_config={"board_token": "robinhood"},
        scraper_module="scrapers.companies.robinhood",
    ),
    CompanyRecord(
        name="Rocket Lab USA, Inc.", slug="rocketlab", industry="Aerospace",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/rocketlab",
        website_url="https://www.rocketlabusa.com",
        ats_config={"board_token": "rocketlab"},
        scraper_module="scrapers.companies.rocketlab",
    ),
    CompanyRecord(
        name="The J.M. Smucker Company", slug="smucker", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://smucker.wd5.myworkdayjobs.com/US_External_Careers",
        website_url="https://www.jmsmucker.com",
        ats_config={"tenant": "smucker", "site": "US_External_Careers", "intern_facet_id": "900f59dd9b82101e1295ecea2e0d8b34"},
        scraper_module="scrapers.companies.smucker",
    ),
    CompanyRecord(
        name="Space Exploration Technologies Corp.", slug="spacex", industry="Aerospace",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/spacex",
        website_url="https://www.spacex.com",
        ats_config={"board_token": "spacex"},
        scraper_module="scrapers.companies.spacex",
    ),
    CompanyRecord(
        name="SpotHopper", slug="spothopper", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/spothopper",
        website_url="https://www.spothopper.com",
        ats_config={"board_token": "spothopper"},
        scraper_module="scrapers.companies.spothopper",
    ),
]


# ---------------------------------------------------------------------------
# Tier 2 - Exact ATS identifier confirmed via direct search evidence during
# this phase's research (a live myworkdayjobs.com / boards.greenhouse.io /
# jobs.lever.co URL was observed, not just a company name). Large,
# recognizable, business-relevant employers. Ready to implement next with
# only a quick confirmation request against the live endpoint (the same
# "verify before shipping" step every Tier 1 company already went through),
# not a fresh research effort.
# ---------------------------------------------------------------------------

_TIER_2: list[CompanyRecord] = [
    CompanyRecord(
        name="Truist Financial Corporation", slug="truist", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://truist.wd1.myworkdayjobs.com/Careers",
        website_url="https://www.truist.com",
        ats_config={"tenant": "truist", "site": "Careers"},
        notes="Phase 10 Step 2: live-verified, but this tenant has no `workerSubType` facet at all (only Job_Area/timeType/Regular_Temporary/location facets), and a `searchText=\"intern\"` fallback returns 846 total results - well over the 500-result (25-page) pagination safety cap, and would silently truncate rather than complete. No clean, bounded implementation exists today; deferred rather than forced. Revisit if a narrower Workday facet appears, or if a higher request-volume budget is deliberately approved.",
    ),
    CompanyRecord(
        name="TD Bank / TD Securities", slug="td-bank", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://td.wd3.myworkdayjobs.com/TD_Bank_Careers",
        website_url="https://www.td.com",
        ats_config={"tenant": "td", "site": "TD_Bank_Careers"},
        notes="Phase 10 Step 2: live-verified, but this tenant has no `workerSubType` facet (only `jobFamilyGroup`, a department breakdown with no employment-type dimension), and `searchText=\"intern\"` returns 1516 total results - far over the safe pagination cap. Same reasoning as Truist above; deferred rather than forced.",
    ),
    CompanyRecord(
        name="Barclays", slug="barclays", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://barclays.wd3.myworkdayjobs.com/External_Career_Site_Barclays",
        website_url="https://www.barclays.com",
        ats_config={"tenant": "barclays", "site": "External_Career_Site_Barclays", "intern_facet_id": "6139d325cdcc1001a72ceb63d5d60001"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Intern\" (14 open postings at verification time, including real business roles). Implemented.",
        scraper_module="scrapers.companies.barclays",
    ),
    CompanyRecord(
        name="Federal Reserve Bank of New York", slug="ny-fed", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://rb.wd5.myworkdayjobs.com/FRS",
        website_url="https://www.newyorkfed.org",
        ats_config={"tenant": "rb", "site": "FRS"},
        notes="Phase 10 Step 2: live-verified. No `workerSubType` facet on this tenant (only Regular/Temporary); board is small (~105 total), so the whole board is scanned and narrowed by the existing client-side title pre-filter alone. Zero currently-open postings matched at verification time (a real, live snapshot fact - the previously-found \"Summer Intern\" posting had since closed) - implemented anyway since the scraper itself is correct and will pick up new postings automatically.",
        scraper_module="scrapers.companies.nyfed",
    ),
    CompanyRecord(
        name="CIBC", slug="cibc", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://cibc.wd3.myworkdayjobs.com/campus",
        website_url="https://www.cibc.com",
        ats_config={"tenant": "cibc", "site": "campus"},
        notes="Phase 10 Step 2: live-verified. No `workerSubType` facet; board is tiny (~7 total), scanned in full. One real internship-labeled posting confirmed at verification time.",
        scraper_module="scrapers.companies.cibc",
    ),
    CompanyRecord(
        name="Piper Sandler Companies", slug="piper-sandler", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://pipersandler.wd501.myworkdayjobs.com/Piper_Sandler_Careers",
        website_url="https://www.pipersandler.com",
        ats_config={"tenant": "pipersandler", "site": "Piper_Sandler_Careers"},
        notes="Phase 10 Step 2: live-verified. No `workerSubType` facet; board is small (~43 total), scanned in full. This tenant's internships are titled \"Summer Analyst\" with no \"intern\"/\"internship\" in the title at all - only classify correctly because of the new \"summer analyst\" synonym added to INTERN_TITLE_RE this same phase (see scrapers/classification.py).",
        scraper_module="scrapers.companies.pipersandler",
    ),
    CompanyRecord(
        name="Texas Capital Bank", slug="texas-capital-bank", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://texascapitalbank.wd12.myworkdayjobs.com/College_Career",
        website_url="https://www.texascapitalbank.com",
        ats_config={"tenant": "texascapitalbank", "site": "College_Career", "intern_facet_id": "a2a9056096f710012bf10d7b8a530000"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Intern (Fixed Term) (Trainee)\" (1 open posting at verification time - a small regional bank's naturally smaller board, not a scraper issue). Implemented.",
        scraper_module="scrapers.companies.texascapitalbank",
    ),
    CompanyRecord(
        name="Verizon Communications Inc.", slug="verizon", industry="Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://verizon.wd5.myworkdayjobs.com/verizon-careers",
        website_url="https://www.verizon.com",
        ats_config={"tenant": "verizon", "site": "verizon-careers"},
        notes="Phase 10 Step 2: this tenant currently redirects to Workday's own maintenance page (`community.workday.com/maintenance-page`, HTTP 500/422 on both robots.txt and the jobs API) - confirmed this is specific to the \"verizon\" tenant, not a wd5-pod-wide outage (Abbott, already in production on the same wd5 pod, responded normally). Deferred rather than guessing an alternate tenant slug; retry in a future pass.",
    ),
    CompanyRecord(
        name="PwC (PricewaterhouseCoopers)", slug="pwc", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://pwc.wd3.myworkdayjobs.com/Global_Campus_Careers",
        website_url="https://www.pwc.com",
        ats_config={"tenant": "pwc", "site": "Global_Campus_Careers", "intern_facet_id": ["e57e6863118d01e8c8ee4356e52a5e2d", "e57e6863118d01ccc3941a45322bfba2"]},
        notes="Phase 10 Step 2: `US_Entry_Level_Careers` (the Step 1 guess) returned 0 total postings when live-verified - an empty/inactive site path, not a real career site. `Global_Campus_Careers` returned 1519 total postings and has two real intern-related `workerSubType` facets (\"Intern\": 72, \"Intern (Trainee)\": 410), both used via the new multi-facet-id support added to WorkdayScraper this phase. Implemented.",
        scraper_module="scrapers.companies.pwc",
    ),
    CompanyRecord(
        name="Accenture", slug="accenture", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://accenture.wd103.myworkdayjobs.com/AccentureCareers",
        website_url="https://www.accenture.com",
        ats_config={"tenant": "accenture", "site": "AccentureCareers"},
        notes="Phase 10 Step 2: live-verified, but this tenant's `workerSubType` facet parameter is repurposed to carry a \"Skills\" facet instead of job type (a real, tenant-specific anomaly - confirmed by inspecting the facet's own `descriptor` field). `jobFamilyGroup` is a functional-area breakdown (Software Engineering, Consulting, Finance, etc.) with no employment-type dimension, and `searchText=\"intern\"` is capped at the display maximum (2000 total) - the board is both too large and lacks any reliable narrowing mechanism. Deferred rather than forced.",
    ),
    CompanyRecord(
        name="Guidehouse", slug="guidehouse", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://guidehouse.wd1.myworkdayjobs.com/External",
        website_url="https://guidehouse.com",
        ats_config={"tenant": "guidehouse", "site": "External", "search_text": "intern"},
        notes="Phase 10 Step 2: no `workerSubType` facet on this tenant; `searchText=\"intern\"` returns 361 total results, comfortably within the 500-result pagination safety cap (unlike Truist/TD above). Implemented using the new search_text fallback mode added to WorkdayScraper this phase.",
        scraper_module="scrapers.companies.guidehouse",
    ),
    CompanyRecord(
        name="GE Aerospace", slug="ge-aerospace", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite",
        website_url="https://www.geaerospace.com",
        ats_config={"tenant": "geaerospace", "site": "GE_ExternalSite", "intern_facet_id": "74cbdbfadb6e1001457c5daa0b900000"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Co-op/Intern (Fixed Term)\" (108 open postings at verification time; board skews engineering-heavy, business-relevant subset filtered by the existing shared classifier as usual). Implemented.",
        scraper_module="scrapers.companies.geaerospace",
    ),
    CompanyRecord(
        name="The Boeing Company", slug="boeing", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS",
        website_url="https://www.boeing.com",
        ats_config={"tenant": "boeing", "site": "EXTERNAL_CAREERS", "intern_facet_id": "8b618a30e00f01dbf217e9650c3fc507"},
        notes="Phase 10 Step 2: `EXTERNAL_CAREERS` confirmed as the correct/complete site path (739 total postings) over the alternate `INTERN` path. `workerSubType` facet for \"Intern - Paid (Seasonal)\" (16 open postings at verification time, real business roles like Business Operations and Program Management alongside engineering). Deliberately excludes the separate \"Intern Fixed Term (Non-US)\" facet value. Implemented.",
        scraper_module="scrapers.companies.boeing",
    ),
    CompanyRecord(
        name="The Walt Disney Company", slug="disney", industry="Media & Entertainment",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://disney.wd5.myworkdayjobs.com/disneycareer",
        website_url="https://www.thewaltdisneycompany.com",
        ats_config={"tenant": "disney", "site": "disneycareer", "intern_facet_id": "4f84d9e8a0970100aec0ae70150e0000"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Student Program / Intern (Fixed Term)\" (11 open postings at verification time). The specific Accounting & Finance Rotation Program posting found during Step 1 research had rotated off the live board by verification time; open postings skewed EMEA/regional at this exact moment - a live snapshot fact, not a facet-selection error (same multinational scraping pattern already used for Barclays/Chevron, with frontend USA-location filtering and the shared classifier handling relevance downstream). Implemented.",
        scraper_module="scrapers.companies.disney",
    ),
]


# ---------------------------------------------------------------------------
# Tier 3 - Real company and ATS platform identified via this phase's
# research with reasonable confidence, but the exact board token / tenant /
# site identifier was not captured with a citable URL in the material
# carried into this compiled registry, and/or observed posting volume or
# US-location focus needs confirmation. Good next-wave candidates; each
# needs one confirmation pass (the same kind of check Tier 2 already had)
# before being promoted to READY.
# ---------------------------------------------------------------------------

_TIER_3: list[CompanyRecord] = [
    CompanyRecord(
        name="Magna International", slug="magna-international", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.magna.com",
        notes="Identified via Workday manufacturing/automotive research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Polaris Inc.", slug="polaris-inc", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.polaris.com",
        notes="Identified via Workday manufacturing research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="3M Company", slug="3m", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.3m.com",
        notes="Named as a Workday-platform candidate in earlier manufacturing research; a direct-evidence search this session did not return a live posting URL. Confirm platform and tenant before promoting.",
    ),
    CompanyRecord(
        name="GlobalFoundries", slug="globalfoundries", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://gf.com",
        notes="Identified via Workday manufacturing/semiconductor research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="MKS Instruments", slug="mks-instruments", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.mks.com",
        notes="Identified via Workday manufacturing research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="SpartanNash Company", slug="spartannash", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.spartannash.com",
        notes="Identified via Workday retail research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="RaceTrac Inc.", slug="racetrac", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.racetrac.com",
        notes="Identified via Workday retail research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Cox Enterprises", slug="cox-enterprises", industry="Media & Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.coxenterprises.com",
        notes="Identified via Workday retail/media research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Anheuser-Busch InBev", slug="ab-inbev", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.ab-inbev.com",
        notes="Identified via Workday food & beverage research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="International Flavors & Fragrances (IFF)", slug="iff", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.iff.com",
        notes="Identified via Workday food & beverage research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Saputo Inc.", slug="saputo", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.saputo.com",
        notes="Identified via Workday food & beverage research; confirm US-location postings exist (Canadian parent company) before promoting.",
    ),
    CompanyRecord(
        name="Primient", slug="primient", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.primient.com",
        notes="Identified via Workday food & beverage research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Marathon Petroleum Corporation", slug="marathon-petroleum", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.marathonpetroleum.com",
        notes="Identified via Workday energy research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Hilcorp Energy Company", slug="hilcorp", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.hilcorp.com",
        notes="Identified via Workday energy research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Medline Industries", slug="medline", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.medline.com",
        notes="Identified via Workday healthcare/pharma research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Takeda Pharmaceutical Company", slug="takeda", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.takeda.com",
        notes="Identified via Workday healthcare/pharma research; confirm US-location postings exist (Japanese parent company) before promoting.",
    ),
    CompanyRecord(
        name="ResMed Inc.", slug="resmed", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.resmed.com",
        notes="Identified via Workday healthcare research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Workiva Inc.", slug="workiva", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.workiva.com",
        notes="Identified as a likely Greenhouse-hosted company via research; exact board token not captured this pass.",
    ),
    CompanyRecord(
        name="Sierra Nevada Corporation", slug="sierra-nevada-corp", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.sncorp.com",
        notes="Identified via Workday aerospace/defense research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Airbus", slug="airbus", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.airbus.com",
        notes="Identified via Workday aerospace research; confirm US-location (Airbus Americas, Mobile AL) postings specifically before promoting (European parent company).",
    ),
    CompanyRecord(
        name="ICF International", slug="icf-international", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://www.icf.com",
        notes="Identified via Workday consulting research; exact tenant/site not captured this pass.",
    ),
    CompanyRecord(
        name="Shield AI", slug="shield-ai", industry="Aerospace",
        ats=ATSPlatform.LEVER, tier=CompanyTier.TIER_3, status=CompanyStatus.RESEARCHED,
        website_url="https://shield.ai",
        notes="Identified via Lever defense-tech research; exact Lever site slug not captured this pass.",
    ),
]


# ---------------------------------------------------------------------------
# Tier 4 - Candidate only. ATS platform is unconfirmed, evidence is too
# indirect (e.g. only seen via a third-party aggregator rather than the
# ATS host itself), or public-access legitimacy is unclear. Needs Review:
# do not implement, and do not assume a platform, until this is resolved
# by re-research at implementation time. This mirrors the Phase 8 Lever
# precedent (jobs.lever.co vs. api.lever.co) - when in doubt, mark it
# Needs Review rather than guessing.
# ---------------------------------------------------------------------------

_TIER_4: list[CompanyRecord] = [
    CompanyRecord(
        name="T-Mobile US, Inc.", slug="t-mobile", industry="Telecommunications",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.t-mobile.com",
        notes="Summer 2026 Finance internship postings (Financial Reporting, Tax, graduate-level Finance) confirmed to exist via an aggregator (builtin.com), but no direct ATS host URL was observed this session. Do not assume a platform/tenant - confirm the actual career-site host and its access model before proceeding.",
    ),
    CompanyRecord(
        name="Charter Communications (Spectrum)", slug="spectrum-charter", industry="Telecommunications",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://corporate.charter.com",
        notes="2026 Summer Intern: Business Analyst posting confirmed to exist via an aggregator (builtin.com), but no direct ATS host URL was observed this session. Same caveat as T-Mobile above.",
    ),
    CompanyRecord(
        name="NVIDIA Corporation", slug="nvidia", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.nvidia.com",
        notes="Named as a candidate in earlier research; a direct-evidence search this session returned no live posting URL for any platform. Confirm platform before any further work.",
    ),
    CompanyRecord(
        name="Deloitte", slug="deloitte", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www2.deloitte.com",
        notes="Big 4 peer of PwC (Tier 2, confirmed Workday) and Accenture/Guidehouse (Tier 2, confirmed Workday); plausible Workday tenant but not directly evidenced this session. Do not assume - confirm before promoting.",
    ),
    CompanyRecord(
        name="EY (Ernst & Young)", slug="ey", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.ey.com",
        notes="Same caveat as Deloitte above - plausible but unconfirmed this session.",
    ),
    CompanyRecord(
        name="KPMG", slug="kpmg", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://kpmg.com",
        notes="Same caveat as Deloitte above - plausible but unconfirmed this session.",
    ),
    CompanyRecord(
        name="Commonwealth Bank of Australia", slug="commonwealth-bank-australia", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_4, status=CompanyStatus.EXCLUDED,
        career_url="https://cba.wd3.myworkdayjobs.com/CommBank_Careers",
        website_url="https://www.commbank.com.au",
        ats_config={"tenant": "cba", "site": "CommBank_Careers"},
        notes="Excluded: 2026/27 Global Markets Summer Analyst Campaign observed live, but the program and postings are Australia-based. This platform's location filter only surfaces USA-based (and unlabeled/Remote) postings, so this company's listings would be filtered out of every search result - not a useful scrape target given current product scope.",
    ),
]


COMPANY_REGISTRY: list[CompanyRecord] = [*_TIER_1, *_TIER_2, *_TIER_3, *_TIER_4]


def get_by_status(status: CompanyStatus) -> list[CompanyRecord]:
    return [c for c in COMPANY_REGISTRY if c.status == status]


def get_by_tier(tier: CompanyTier) -> list[CompanyRecord]:
    return [c for c in COMPANY_REGISTRY if c.tier == tier]


def get_by_ats(ats: ATSPlatform) -> list[CompanyRecord]:
    return [c for c in COMPANY_REGISTRY if c.ats == ats]


def get_implemented() -> list[CompanyRecord]:
    return get_by_status(CompanyStatus.IMPLEMENTED)


def validate_registry() -> None:
    """Internal consistency checks, run in tests/test_company_registry.py."""
    slugs = [c.slug for c in COMPANY_REGISTRY]
    duplicates = {s for s in slugs if slugs.count(s) > 1}
    if duplicates:
        raise ValueError(f"Duplicate slug(s) in COMPANY_REGISTRY: {duplicates}")

    for c in COMPANY_REGISTRY:
        if c.status == CompanyStatus.IMPLEMENTED and not c.scraper_module:
            raise ValueError(f"{c.slug} is marked IMPLEMENTED but has no scraper_module")
        if c.status == CompanyStatus.READY and c.ats == ATSPlatform.UNKNOWN:
            raise ValueError(f"{c.slug} is marked READY but has an UNKNOWN ats platform")
        if c.status == CompanyStatus.READY and not c.ats_config:
            raise ValueError(f"{c.slug} is marked READY but has no ats_config")
