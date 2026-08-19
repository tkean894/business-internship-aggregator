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
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://magna.wd3.myworkdayjobs.com/Magna",
        website_url="https://www.magna.com",
        ats_config={"tenant": "magna", "site": "Magna", "facet_parameter": "Worker_Type", "intern_facet_id": "5aaaed564f43016878b0b7f1c60258d1"},
        notes="Phase 10 Step 3: live-verified. This tenant's employment-type facet dimension is named `Worker_Type`, not the usual `workerSubType` - new `facet_parameter` config support added to WorkdayScraper for this. \"Intern (Fixed Term) (Trainee)\" facet had 13 open postings at verification time. Implemented.",
        scraper_module="scrapers.companies.magna",
    ),
    CompanyRecord(
        name="Polaris Inc.", slug="polaris-inc", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://polaris.wd5.myworkdayjobs.com/PolarisJobs",
        website_url="https://www.polaris.com",
        ats_config={"tenant": "polaris", "site": "PolarisJobs", "intern_facet_id": "6236a7dc0277102c2f7cc69ac6a45817"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern/Co-op\" (4 open postings at verification time, including Marketing and Finance internships). Implemented.",
        scraper_module="scrapers.companies.polaris",
    ),
    CompanyRecord(
        name="3M Company", slug="3m", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://3m.wd1.myworkdayjobs.com/Search",
        website_url="https://www.3m.com",
        ats_config={"tenant": "3m", "site": "Search"},
        notes="Phase 10 Step 3: live-verified, and real intern postings clearly exist (Undergraduate Marketing/Business Analytics/Sales Intern titles found via direct search) - but no `workerSubType` facet value tags them (only Regular=619, Temporary=14), and `searchText=\"intern\"` returns all 633 total with zero narrowing (unlike every other tenant checked this phase), meaning it provides no benefit over an unfiltered scan. Total board (633) exceeds the safe pagination cap either way. No clean, bounded implementation exists today; deferred rather than forced.",
    ),
    CompanyRecord(
        name="GlobalFoundries", slug="globalfoundries", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://globalfoundries.wd1.myworkdayjobs.com/External",
        website_url="https://gf.com",
        ats_config={"tenant": "globalfoundries", "site": "External", "intern_facet_id": "51f993b53bda010524990ac0ea5d0004"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (With Pay) (Fixed Term) (Trainee)\" (62 open postings at verification time, including Investor Relations, Finance & Business Operations, and Legal Corporate Affairs interns - strong business fit). Implemented.",
        scraper_module="scrapers.companies.globalfoundries",
    ),
    CompanyRecord(
        name="MKS Instruments", slug="mks-instruments", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://mksinst.wd1.myworkdayjobs.com/MKSCareersUniversity",
        website_url="https://www.mks.com",
        ats_config={"tenant": "mksinst", "site": "MKSCareersUniversity", "intern_facet_id": "9f854d39924a0175398333d9e3072e69"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern / Co-Op / Student (Fixed Term)\" (8 open postings at verification time) on the dedicated `MKSCareersUniversity` site (distinct from the general `MKSCareersEMEA` site also found during research). Implemented.",
        scraper_module="scrapers.companies.mksinstruments",
    ),
    CompanyRecord(
        name="SpartanNash Company", slug="spartannash", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://spartannash.wd1.myworkdayjobs.com/SpartanNash_Careers",
        website_url="https://www.spartannash.com",
        ats_config={"tenant": "spartannash", "site": "SpartanNash_Careers"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value (Casual=823, Regular=305 - a warehouse/retail-heavy board); `searchText=\"intern\"` narrows to 85 (technically bounded), but the two intern postings found via direct search (IT Ecommerce Developer Intern, Benefits and Payroll Intern) suggest thin, mostly-non-business volume relative to the strength of other Tier 3 candidates implemented this phase. Deprioritized rather than implemented given the 10-15 target and stronger alternatives available - not a compliance concern, a prioritization one. Revisit in a future pass.",
    ),
    CompanyRecord(
        name="RaceTrac Inc.", slug="racetrac", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://racetrac.wd5.myworkdayjobs.com/SSC",
        website_url="https://www.racetrac.com",
        ats_config={"tenant": "racetrac", "site": "SSC"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value; board is small (~51 total on this corporate-support-office site), scanned in full. Confirmed real, diverse business-relevant postings at verification time: HR, Data Science, Retail Accounting, Pricing and Revenue interns. Implemented.",
        scraper_module="scrapers.companies.racetrac",
    ),
    CompanyRecord(
        name="Cox Enterprises", slug="cox-enterprises", industry="Media & Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://cox.wd1.myworkdayjobs.com/Cox_External_Career_Site_1",
        website_url="https://www.coxenterprises.com",
        ats_config={"tenant": "cox", "site": "Cox_External_Career_Site_1", "search_text": "intern"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value; `searchText=\"intern\"` narrows the 681-total board to 111, within the pagination safety cap. Confirmed real, diverse business-relevant postings: Analytics, Talent Acquisition, CSR, Finance & IT interns. Implemented.",
        scraper_module="scrapers.companies.cox",
    ),
    CompanyRecord(
        name="Anheuser-Busch InBev", slug="ab-inbev", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://abinbev.wd1.myworkdayjobs.com/USA",
        website_url="https://www.ab-inbev.com",
        ats_config={"tenant": "abinbev", "site": "USA"},
        notes="Phase 10 Step 3: live-verified. This tenant hosts several region-specific sites (EUR, MEX, BCBU, USA); `USA` confirmed as the correct US-only site. `workerSubType` facet only tags 1 posting as Intern despite real confirmed internship/trainee postings (MBA Intern, Global Supply Chain Masters/MBA/PhD Intern) - board is small (143 total), scanned in full instead. Implemented.",
        scraper_module="scrapers.companies.abinbev",
    ),
    CompanyRecord(
        name="International Flavors & Fragrances (IFF)", slug="iff", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://iff.wd5.myworkdayjobs.com/IFF_Careers",
        website_url="https://www.iff.com",
        ats_config={"tenant": "iff", "site": "IFF_Careers", "search_text": "intern"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` facet at all; `searchText=\"intern\"` narrows the 419-total board to 291, within the pagination safety cap. Confirmed real business-relevant postings alongside the scientific majority: HRBP Intern, Marketing Intern, Sales Support Intern. Implemented.",
        scraper_module="scrapers.companies.iff",
    ),
    CompanyRecord(
        name="Saputo Inc.", slug="saputo", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://saputo.wd5.myworkdayjobs.com/Saputo_External_Careers",
        website_url="https://www.saputo.com",
        ats_config={"tenant": "saputo", "site": "Saputo_External_Careers"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value despite real confirmed postings (Intern Sales Analyst, Intern Finance, Intern Continuous Improvement); board is small (262 total), scanned in full. Canadian company (Montreal HQ) - now a useful target given this platform's US+Canada location display filter (Phase 10 Step 2 follow-up). Implemented.",
        scraper_module="scrapers.companies.saputo",
    ),
    CompanyRecord(
        name="Primient", slug="primient", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://primient.wd1.myworkdayjobs.com/External_Careers",
        website_url="https://www.primient.com",
        ats_config={"tenant": "primient", "site": "External_Careers"},
        notes="Phase 10 Step 3: live-verified. `workerSubType` Intern facet only tags 1 posting despite real confirmed postings (Tax and Treasury Intern, Digital Data and Analytics Intern, HR Intern); board is small (52 total), scanned in full. Implemented.",
        scraper_module="scrapers.companies.primient",
    ),
    CompanyRecord(
        name="Marathon Petroleum Corporation", slug="marathon-petroleum", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://mpc.wd1.myworkdayjobs.com/MPCCareers",
        website_url="https://www.marathonpetroleum.com",
        ats_config={"tenant": "mpc", "site": "MPCCareers", "intern_facet_id": "762d3bc5687201008504b33faf520000"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern\" (17 open postings at verification time, including Finance and Commercial interns). Implemented.",
        scraper_module="scrapers.companies.marathonpetroleum",
    ),
    CompanyRecord(
        name="Hilcorp Energy Company", slug="hilcorp", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://hec.wd5.myworkdayjobs.com/Hilcorp_Energy_Company",
        website_url="https://www.hilcorp.com",
        ats_config={"tenant": "hec", "site": "Hilcorp_Energy_Company"},
        notes="Phase 10 Step 3: live-verified. `workerSubType` \"Co-Op Student\" facet exists (3 postings) and board is small (33 total, safely scannable in full), but confirmed real postings skew heavily technical (Engineer Intern, Geology Intern) with only occasional business roles (HR Accounting Intern, Office Services Intern). Deprioritized given the 10-15 target and stronger alternatives implemented this phase - not a compliance concern. Revisit in a future pass.",
    ),
    CompanyRecord(
        name="Medline Industries", slug="medline", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://medline.wd5.myworkdayjobs.com/Medline",
        website_url="https://www.medline.com",
        ats_config={"tenant": "medline", "site": "Medline", "intern_facet_id": "a71dfaf3f3d31000c6fcb5c805bd0001"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (Fixed Term) (Trainee)\" (7 open postings at verification time, including Product Management, Supply Chain, Sales, and Business Operations interns - strong business fit). Implemented.",
        scraper_module="scrapers.companies.medline",
    ),
    CompanyRecord(
        name="Takeda Pharmaceutical Company", slug="takeda", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://takeda.wd3.myworkdayjobs.com/External",
        website_url="https://www.takeda.com",
        ats_config={"tenant": "takeda", "site": "External"},
        notes="Phase 10 Step 3: this tenant currently returns HTTP 500/422 on both the jobs API and the career page itself (confirmed on multiple attempts, including with a browser User-Agent header) - the same failure pattern as Verizon in Phase 10 Step 2. Real intern postings were found via direct search (US Tax Summer Intern, FP&A Global BioLife Intern), so this is a real, worthwhile target once the endpoint is reachable again. Deferred rather than guessing an alternate tenant/pod.",
    ),
    CompanyRecord(
        name="ResMed Inc.", slug="resmed", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://resmed.wd3.myworkdayjobs.com/ResMed_External_Careers",
        website_url="https://www.resmed.com",
        ats_config={"tenant": "resmed", "site": "ResMed_External_Careers", "intern_facet_id": "57129bf02a5f01966a976e3306078f0d"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (Fixed Term)\" - technically clean, but only 2 open postings at verification time and the board is overwhelmingly software/engineering-focused (Software Engineer/Developer, Test Engineering, Automation interns), with only a Digital Marketing Intern as a clear business-relevant exception. Deprioritized given the 10-15 target and stronger alternatives implemented this phase - not a compliance concern. Revisit in a future pass.",
    ),
    CompanyRecord(
        name="Workiva Inc.", slug="workiva", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.workiva.com",
        notes="Phase 10 Step 3: two direct search attempts this session (including one targeted specifically at job-boards.greenhouse.io/boards.greenhouse.io) found only third-party aggregator listings (Built In, JobRight, Clera, Breakroom) for Workiva's real 2026 internship postings (Software Engineering, Machine Learning, CPX Insights/System interns all confirmed to exist) - no direct Greenhouse (or any ATS host) URL was found. Not scraping via an aggregator per the explicit compliance rule; platform and board token remain unconfirmed.",
    ),
    CompanyRecord(
        name="Sierra Nevada Corporation", slug="sierra-nevada-corp", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://snc.wd1.myworkdayjobs.com/SNC_External_Career_Site",
        website_url="https://www.sncorp.com",
        ats_config={"tenant": "snc", "site": "SNC_External_Career_Site", "intern_facet_id": "bd3f3405ddee105b4243e938c45a16d5"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (Trainee)\" - technically clean, but only 1 open posting at verification time and the board (aerospace/defense engineering) shows little historical business-role diversity. Deprioritized given the 10-15 target and stronger alternatives implemented this phase - not a compliance concern. Revisit in a future pass.",
    ),
    CompanyRecord(
        name="Airbus", slug="airbus", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://ag.wd3.myworkdayjobs.com/Airbus",
        website_url="https://www.airbus.com",
        ats_config={"tenant": "ag", "site": "Airbus", "intern_facet_id": "f5811cef9cb50193723ed01d470a6e15"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Trainee / Student (Fixed Term)\" (124 open postings worldwide at verification time - this is Airbus's single global tenant, covering every legal entity including Airbus Americas). A combined workerSubType+hiringCompany query narrowed to just \"Airbus Americas, Inc.\" returned only 2 results, fewer than US postings independently confirmed via direct search, so hiringCompany narrowing was not used. Scrapes globally; the existing frontend US/Canada display filter surfaces the relevant subset, same pattern as Barclays/Disney. Implemented.",
        scraper_module="scrapers.companies.airbus",
    ),
    CompanyRecord(
        name="ICF International", slug="icf-international", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://icf.wd5.myworkdayjobs.com/ICFExternal_Career_Site",
        website_url="https://www.icf.com",
        ats_config={"tenant": "icf", "site": "ICFExternal_Career_Site", "search_text": "intern"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` facet at all; `searchText=\"intern\"` narrows the 378-total board to 132, within the pagination safety cap. Confirmed strong business-relevant postings: Marketing, Business Analyst, Energy Analyst, Program Operations interns. Implemented.",
        scraper_module="scrapers.companies.icf",
    ),
    CompanyRecord(
        name="Shield AI", slug="shield-ai", industry="Aerospace",
        ats=ATSPlatform.LEVER, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://shield.ai",
        ats_config={"site": "shieldai"},
        notes="Phase 10 Step 3: live-verified public Lever Postings API access (api.lever.co/v0/postings/shieldai, 434 total postings), but zero currently open postings match the internship title pattern (the Production Planning/Data Analyst/Strategy & Operations interns found during earlier research had closed by verification time) - a real, live snapshot fact. Deprioritized rather than implemented given zero current yield and the 10-15 target; the endpoint itself is legitimate and this is a reasonable candidate to revisit in a future pass.",
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
        notes="Excluded: 2026/27 Global Markets Summer Analyst Campaign observed live, but the program and postings are Australia-based. This platform's location filter only surfaces US/Canada-based (and unlabeled/Remote) postings, so this company's listings would be filtered out of every search result - not a useful scrape target given current product scope.",
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
