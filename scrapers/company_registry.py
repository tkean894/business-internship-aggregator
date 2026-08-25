"""Phase 10 Step 1 - Company Registry & Expansion Architecture.
Phase 10 Step 4 - Reprioritized around business-internship value, with a
transparent scoring system and a much larger researched candidate pool.

This module is a PLANNING / TRACKING artifact, not a scraper. It records
every company under consideration for the Top-200 business-internship
expansion, independent of whether a scraper has been implemented for it
yet. It intentionally does NOT duplicate `backend/models/company.py`
(that table only exists for companies with real scraped data - name,
slug, career_url, website_url, industry, is_active - and is populated by
`BaseScraper._get_or_create_company()` on each scraper run, never by
this file directly). This registry adds the fields that DB table has no
reason to carry: ATS platform + per-ATS identifiers, implementation/
verification status, priority tier, scoring, and research notes/evidence -
all needed to plan and safely scale the *scraper* side, none of it
meaningful for the runtime Company row.

See docs/architecture.md ("Company Registry & Expansion Architecture",
Phase 10) for the full design rationale, tiering policy, scoring
methodology, and compliance rules this file encodes, and docs/roadmap.md
(Phase 10) for the rollout plan.

Compliance rule encoded by CompanyStatus.NEEDS_REVIEW: a company is only
promoted to READY (and later IMPLEMENTED) once its ATS access has been
confirmed to be a public, unauthenticated, officially-documented-or-
equivalent endpoint - the same bar applied to Greenhouse's board API,
Workday's CXS API, and Lever's Postings API in Phases 2-8. If that isn't
clearly true (unclear robots.txt, only found via an aggregator rather
than the ATS host itself, requires auth, etc.) the company stays at
NEEDS_REVIEW rather than being forced through.

--- Phase 10 Step 4: scoring system ---

Every company - implemented or candidate - carries six 0-10 subscores:

- business_relevance_score: how much of this company's internship volume
  maps to Finance/Consulting/Marketing/Strategy/Ops/HR/Sales/etc. rather
  than pure engineering/technical roles.
- company_reputation_score: brand recognition and recruiting prestige
  among students specifically searching for BUSINESS internships.
- internship_volume_score: estimated size/structure of the internship
  program (a large structured "Summer Analyst"-style program scores
  high even if this project has not yet observed live postings for it).
- function_breadth_score: how many distinct business functions the
  program spans (a company with only one narrow track scores lower than
  a diversified conglomerate with Finance + Marketing + Ops + HR + Supply
  Chain internships).
- ats_accessibility_score: how accessible the company's actual ATS is to
  this project's architecture (BaseScraper/GreenhouseScraper/
  WorkdayScraper/LeverScraper) - a confirmed, live, bounded endpoint
  scores near 10; a known-proprietary/custom recruiting platform with no
  Greenhouse/Workday/Lever access scores near 1.
- evidence_score: how much direct, this-project evidence backs the
  above - a company already implemented and running in production scores
  9-10; a company scored this phase purely from general industry
  knowledge, with no live verification, scores low (2-3), regardless of
  how confident the estimate is.

`priority_score` is the unweighted mean of the six subscores (see the
`CompanyRecord.priority_score` property below) - deliberately simple
rather than engineered, per Phase 10 Step 4's explicit instruction not to
over-engineer this. The purpose is to make relative ordering legible, not
to produce a scientifically precise ranking. Because evidence_score is
one of the six inputs, an unverified-but-plausible Fortune 500 candidate
will generally NOT outrank an already-implemented company of similar
business value - implementation status/verification is a real signal,
not noise, and this keeps the score from just reflecting "how famous is
this company" alone.
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
    TIER_5 = 5  # Phase 10 Step 4: broad researched candidate pool - business value assessed and scored this phase, but ATS platform/identifier is an informed estimate (or fully unknown), not independently verified via a live endpoint this phase. Lowest sequencing priority for *implementation work specifically*, independent of how high a candidate's priority_score is - real verification happens before any candidate here is promoted.


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

    # Phase 10 Step 4 scoring (see module docstring for methodology). All
    # 0-10; default 0.0 only exists so the dataclass is constructible -
    # every record in this file sets these explicitly.
    business_relevance_score: float = 0.0
    company_reputation_score: float = 0.0
    internship_volume_score: float = 0.0
    function_breadth_score: float = 0.0
    ats_accessibility_score: float = 0.0
    evidence_score: float = 0.0

    @property
    def priority_score(self) -> float:
        scores = (
            self.business_relevance_score,
            self.company_reputation_score,
            self.internship_volume_score,
            self.function_breadth_score,
            self.ats_accessibility_score,
            self.evidence_score,
        )
        return round(sum(scores) / len(scores), 2)


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
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="AIA Group Limited", slug="aia", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://aia.wd3.myworkdayjobs.com/External",
        website_url="https://www.aia.com",
        ats_config={"tenant": "aia", "site": "External", "intern_facet_id": "bd3d6b20175f01ed58af1567352c2c0d"},
        scraper_module="scrapers.companies.aia",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Applied Materials, Inc.", slug="applied-materials", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://amat.wd1.myworkdayjobs.com/External",
        website_url="https://www.appliedmaterials.com",
        ats_config={"tenant": "amat", "site": "External", "intern_facet_id": "ba9df317f7ac456da2faff4fd6a521c8"},
        scraper_module="scrapers.companies.appliedmaterials",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Assurant, Inc.", slug="assurant", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://assurant.wd1.myworkdayjobs.com/Assurant_Careers",
        website_url="https://www.assurant.com",
        ats_config={"tenant": "assurant", "site": "Assurant_Careers", "intern_facet_id": "48706393987501e4fbdb24f7940b8109"},
        scraper_module="scrapers.companies.assurant",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Braze, Inc.", slug="braze", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/braze",
        website_url="https://www.braze.com",
        ats_config={"board_token": "braze"},
        scraper_module="scrapers.companies.braze",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Chevron Corporation", slug="chevron", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://chevron.wd5.myworkdayjobs.com/jobs",
        website_url="https://www.chevron.com",
        ats_config={"tenant": "chevron", "site": "jobs", "intern_facet_id": "3cd342d9804f01e3bd250104bb00c80e"},
        scraper_module="scrapers.companies.chevron",
        business_relevance_score=7, company_reputation_score=9, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Cloudflare, Inc.", slug="cloudflare", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/cloudflare",
        website_url="https://www.cloudflare.com",
        ats_config={"board_token": "cloudflare"},
        scraper_module="scrapers.companies.cloudflare",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="HCVT LLP", slug="hcvt", industry="Consulting",
        ats=ATSPlatform.LEVER, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://jobs.lever.co/hcvt",
        website_url="https://www.hcvt.com",
        ats_config={"site": "hcvt"},
        scraper_module="scrapers.companies.hcvt",
        business_relevance_score=9, company_reputation_score=4, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Invesco Ltd.", slug="invesco", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://invesco.wd1.myworkdayjobs.com/ivzearlycareers",
        website_url="https://www.invesco.com",
        ats_config={"tenant": "invesco", "site": "ivzearlycareers", "intern_facet_id": "97a56ab3ad0b10186c046d05f3ee0001"},
        scraper_module="scrapers.companies.invesco",
        business_relevance_score=9, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Medtronic plc", slug="medtronic", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://medtronic.wd1.myworkdayjobs.com/MedtronicCareers",
        website_url="https://www.medtronic.com",
        ats_config={"tenant": "medtronic", "site": "MedtronicCareers", "intern_facet_id": "6726e368deda465eb362a1203261d1e5"},
        scraper_module="scrapers.companies.medtronic",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Red Ventures", slug="redventures", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/redventures",
        website_url="https://www.redventures.com",
        ats_config={"board_token": "redventures"},
        scraper_module="scrapers.companies.redventures",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Robinhood Markets, Inc.", slug="robinhood", industry="Financial Services",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/robinhood",
        website_url="https://robinhood.com",
        ats_config={"board_token": "robinhood"},
        scraper_module="scrapers.companies.robinhood",
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Rocket Lab USA, Inc.", slug="rocketlab", industry="Aerospace",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/rocketlab",
        website_url="https://www.rocketlabusa.com",
        ats_config={"board_token": "rocketlab"},
        scraper_module="scrapers.companies.rocketlab",
        business_relevance_score=4, company_reputation_score=7, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="The J.M. Smucker Company", slug="smucker", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://smucker.wd5.myworkdayjobs.com/US_External_Careers",
        website_url="https://www.jmsmucker.com",
        ats_config={"tenant": "smucker", "site": "US_External_Careers", "intern_facet_id": "900f59dd9b82101e1295ecea2e0d8b34"},
        scraper_module="scrapers.companies.smucker",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=7, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Space Exploration Technologies Corp.", slug="spacex", industry="Aerospace",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/spacex",
        website_url="https://www.spacex.com",
        ats_config={"board_token": "spacex"},
        scraper_module="scrapers.companies.spacex",
        business_relevance_score=4, company_reputation_score=10, internship_volume_score=5,
        function_breadth_score=4, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="SpotHopper", slug="spothopper", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_1, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boards.greenhouse.io/spothopper",
        website_url="https://www.spothopper.com",
        ats_config={"board_token": "spothopper"},
        scraper_module="scrapers.companies.spothopper",
        business_relevance_score=5, company_reputation_score=2, internship_volume_score=2,
        function_breadth_score=3, ats_accessibility_score=9, evidence_score=10,
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
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=4, evidence_score=8,
    ),
    CompanyRecord(
        name="TD Bank / TD Securities", slug="td-bank", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://td.wd3.myworkdayjobs.com/TD_Bank_Careers",
        website_url="https://www.td.com",
        ats_config={"tenant": "td", "site": "TD_Bank_Careers"},
        notes="Phase 10 Step 2: live-verified, but this tenant has no `workerSubType` facet (only `jobFamilyGroup`, a department breakdown with no employment-type dimension), and `searchText=\"intern\"` returns 1516 total results - far over the safe pagination cap. Same reasoning as Truist above; deferred rather than forced.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=7,
        function_breadth_score=6, ats_accessibility_score=4, evidence_score=8,
    ),
    CompanyRecord(
        name="Barclays", slug="barclays", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://barclays.wd3.myworkdayjobs.com/External_Career_Site_Barclays",
        website_url="https://www.barclays.com",
        ats_config={"tenant": "barclays", "site": "External_Career_Site_Barclays", "intern_facet_id": "6139d325cdcc1001a72ceb63d5d60001"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Intern\" (14 open postings at verification time, including real business roles). Implemented.",
        scraper_module="scrapers.companies.barclays",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Federal Reserve Bank of New York", slug="ny-fed", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://rb.wd5.myworkdayjobs.com/FRS",
        website_url="https://www.newyorkfed.org",
        ats_config={"tenant": "rb", "site": "FRS"},
        notes="Phase 10 Step 2: live-verified. No `workerSubType` facet on this tenant (only Regular/Temporary); board is small (~105 total), so the whole board is scanned and narrowed by the existing client-side title pre-filter alone. Zero currently-open postings matched at verification time (a real, live snapshot fact - the previously-found \"Summer Intern\" posting had since closed) - implemented anyway since the scraper itself is correct and will pick up new postings automatically.",
        scraper_module="scrapers.companies.nyfed",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="CIBC", slug="cibc", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://cibc.wd3.myworkdayjobs.com/campus",
        website_url="https://www.cibc.com",
        ats_config={"tenant": "cibc", "site": "campus"},
        notes="Phase 10 Step 2: live-verified. No `workerSubType` facet; board is tiny (~7 total), scanned in full. One real internship-labeled posting confirmed at verification time.",
        scraper_module="scrapers.companies.cibc",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Piper Sandler Companies", slug="piper-sandler", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://pipersandler.wd501.myworkdayjobs.com/Piper_Sandler_Careers",
        website_url="https://www.pipersandler.com",
        ats_config={"tenant": "pipersandler", "site": "Piper_Sandler_Careers"},
        notes="Phase 10 Step 2: live-verified. No `workerSubType` facet; board is small (~43 total), scanned in full. This tenant's internships are titled \"Summer Analyst\" with no \"intern\"/\"internship\" in the title at all - only classify correctly because of the new \"summer analyst\" synonym added to INTERN_TITLE_RE this same phase (see scrapers/classification.py).",
        scraper_module="scrapers.companies.pipersandler",
        business_relevance_score=9, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Texas Capital Bank", slug="texas-capital-bank", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://texascapitalbank.wd12.myworkdayjobs.com/College_Career",
        website_url="https://www.texascapitalbank.com",
        ats_config={"tenant": "texascapitalbank", "site": "College_Career", "intern_facet_id": "a2a9056096f710012bf10d7b8a530000"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Intern (Fixed Term) (Trainee)\" (1 open posting at verification time - a small regional bank's naturally smaller board, not a scraper issue). Implemented.",
        scraper_module="scrapers.companies.texascapitalbank",
        business_relevance_score=8, company_reputation_score=4, internship_volume_score=2,
        function_breadth_score=4, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Verizon Communications Inc.", slug="verizon", industry="Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://verizon.wd5.myworkdayjobs.com/verizon-careers",
        website_url="https://www.verizon.com",
        ats_config={"tenant": "verizon", "site": "verizon-careers"},
        notes="Phase 10 Step 2: this tenant currently redirects to Workday's own maintenance page (`community.workday.com/maintenance-page`, HTTP 500/422 on both robots.txt and the jobs API) - confirmed this is specific to the \"verizon\" tenant, not a wd5-pod-wide outage (Abbott, already in production on the same wd5 pod, responded normally). Deferred rather than guessing an alternate tenant slug; retry in a future pass.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=3, evidence_score=6,
    ),
    CompanyRecord(
        name="PwC (PricewaterhouseCoopers)", slug="pwc", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://pwc.wd3.myworkdayjobs.com/Global_Campus_Careers",
        website_url="https://www.pwc.com",
        ats_config={"tenant": "pwc", "site": "Global_Campus_Careers", "intern_facet_id": ["e57e6863118d01e8c8ee4356e52a5e2d", "e57e6863118d01ccc3941a45322bfba2"]},
        notes="Phase 10 Step 2: `US_Entry_Level_Careers` (the Step 1 guess) returned 0 total postings when live-verified - an empty/inactive site path, not a real career site. `Global_Campus_Careers` returned 1519 total postings and has two real intern-related `workerSubType` facets (\"Intern\": 72, \"Intern (Trainee)\": 410), both used via the new multi-facet-id support added to WorkdayScraper this phase. Implemented.",
        scraper_module="scrapers.companies.pwc",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=9,
        function_breadth_score=7, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Accenture", slug="accenture", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://accenture.wd103.myworkdayjobs.com/AccentureCareers",
        website_url="https://www.accenture.com",
        ats_config={"tenant": "accenture", "site": "AccentureCareers"},
        notes="Phase 10 Step 2: live-verified, but this tenant's `workerSubType` facet parameter is repurposed to carry a \"Skills\" facet instead of job type (a real, tenant-specific anomaly - confirmed by inspecting the facet's own `descriptor` field). `jobFamilyGroup` is a functional-area breakdown (Software Engineering, Consulting, Finance, etc.) with no employment-type dimension, and `searchText=\"intern\"` is capped at the display maximum (2000 total) - the board is both too large and lacks any reliable narrowing mechanism. Deferred rather than forced.",
        business_relevance_score=8, company_reputation_score=8, internship_volume_score=8,
        function_breadth_score=7, ats_accessibility_score=3, evidence_score=8,
    ),
    CompanyRecord(
        name="Guidehouse", slug="guidehouse", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://guidehouse.wd1.myworkdayjobs.com/External",
        website_url="https://guidehouse.com",
        ats_config={"tenant": "guidehouse", "site": "External", "search_text": "intern"},
        notes="Phase 10 Step 2: no `workerSubType` facet on this tenant; `searchText=\"intern\"` returns 361 total results, comfortably within the 500-result pagination safety cap (unlike Truist/TD above). Implemented using the new search_text fallback mode added to WorkdayScraper this phase.",
        scraper_module="scrapers.companies.guidehouse",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="GE Aerospace", slug="ge-aerospace", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite",
        website_url="https://www.geaerospace.com",
        ats_config={"tenant": "geaerospace", "site": "GE_ExternalSite", "intern_facet_id": "74cbdbfadb6e1001457c5daa0b900000"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Co-op/Intern (Fixed Term)\" (108 open postings at verification time; board skews engineering-heavy, business-relevant subset filtered by the existing shared classifier as usual). Implemented.",
        scraper_module="scrapers.companies.geaerospace",
        business_relevance_score=4, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=4, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="The Boeing Company", slug="boeing", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS",
        website_url="https://www.boeing.com",
        ats_config={"tenant": "boeing", "site": "EXTERNAL_CAREERS", "intern_facet_id": "8b618a30e00f01dbf217e9650c3fc507"},
        notes="Phase 10 Step 2: `EXTERNAL_CAREERS` confirmed as the correct/complete site path (739 total postings) over the alternate `INTERN` path. `workerSubType` facet for \"Intern - Paid (Seasonal)\" (16 open postings at verification time, real business roles like Business Operations and Program Management alongside engineering). Deliberately excludes the separate \"Intern Fixed Term (Non-US)\" facet value. Implemented.",
        scraper_module="scrapers.companies.boeing",
        business_relevance_score=5, company_reputation_score=9, internship_volume_score=6,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="The Walt Disney Company", slug="disney", industry="Media & Entertainment",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_2, status=CompanyStatus.IMPLEMENTED,
        career_url="https://disney.wd5.myworkdayjobs.com/disneycareer",
        website_url="https://www.thewaltdisneycompany.com",
        ats_config={"tenant": "disney", "site": "disneycareer", "intern_facet_id": "4f84d9e8a0970100aec0ae70150e0000"},
        notes="Phase 10 Step 2: live-verified `workerSubType` facet for \"Student Program / Intern (Fixed Term)\" (11 open postings at verification time). The specific Accounting & Finance Rotation Program posting found during Step 1 research had rotated off the live board by verification time; open postings skewed EMEA/regional at this exact moment - a live snapshot fact, not a facet-selection error (same multinational scraping pattern already used for Barclays/Chevron, with frontend USA-location filtering and the shared classifier handling relevance downstream). Implemented.",
        scraper_module="scrapers.companies.disney",
        business_relevance_score=6, company_reputation_score=10, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
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
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Polaris Inc.", slug="polaris-inc", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://polaris.wd5.myworkdayjobs.com/PolarisJobs",
        website_url="https://www.polaris.com",
        ats_config={"tenant": "polaris", "site": "PolarisJobs", "intern_facet_id": "6236a7dc0277102c2f7cc69ac6a45817"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern/Co-op\" (4 open postings at verification time, including Marketing and Finance internships). Implemented.",
        scraper_module="scrapers.companies.polaris",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="3M Company", slug="3m", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://3m.wd1.myworkdayjobs.com/Search",
        website_url="https://www.3m.com",
        ats_config={"tenant": "3m", "site": "Search"},
        notes="Phase 10 Step 3: live-verified, and real intern postings clearly exist (Undergraduate Marketing/Business Analytics/Sales Intern titles found via direct search) - but no `workerSubType` facet value tags them (only Regular=619, Temporary=14), and `searchText=\"intern\"` returns all 633 total with zero narrowing (unlike every other tenant checked this phase), meaning it provides no benefit over an unfiltered scan. Total board (633) exceeds the safe pagination cap either way. No clean, bounded implementation exists today; deferred rather than forced.",
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=2, evidence_score=7,
    ),
    CompanyRecord(
        name="GlobalFoundries", slug="globalfoundries", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://globalfoundries.wd1.myworkdayjobs.com/External",
        website_url="https://gf.com",
        ats_config={"tenant": "globalfoundries", "site": "External", "intern_facet_id": "51f993b53bda010524990ac0ea5d0004"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (With Pay) (Fixed Term) (Trainee)\" (62 open postings at verification time, including Investor Relations, Finance & Business Operations, and Legal Corporate Affairs interns - strong business fit). Implemented.",
        scraper_module="scrapers.companies.globalfoundries",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="MKS Instruments", slug="mks-instruments", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://mksinst.wd1.myworkdayjobs.com/MKSCareersUniversity",
        website_url="https://www.mks.com",
        ats_config={"tenant": "mksinst", "site": "MKSCareersUniversity", "intern_facet_id": "9f854d39924a0175398333d9e3072e69"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern / Co-Op / Student (Fixed Term)\" (8 open postings at verification time) on the dedicated `MKSCareersUniversity` site (distinct from the general `MKSCareersEMEA` site also found during research). Implemented.",
        scraper_module="scrapers.companies.mksinstruments",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="SpartanNash Company", slug="spartannash", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://spartannash.wd1.myworkdayjobs.com/SpartanNash_Careers",
        website_url="https://www.spartannash.com",
        ats_config={"tenant": "spartannash", "site": "SpartanNash_Careers"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value (Casual=823, Regular=305 - a warehouse/retail-heavy board); `searchText=\"intern\"` narrows to 85 (technically bounded), but the two intern postings found via direct search (IT Ecommerce Developer Intern, Benefits and Payroll Intern) suggest thin, mostly-non-business volume relative to the strength of other Tier 3 candidates implemented this phase. Deprioritized rather than implemented given the 10-15 target and stronger alternatives available - not a compliance concern, a prioritization one. Revisit in a future pass.",
        business_relevance_score=4, company_reputation_score=3, internship_volume_score=2,
        function_breadth_score=3, ats_accessibility_score=4, evidence_score=7,
    ),
    CompanyRecord(
        name="RaceTrac Inc.", slug="racetrac", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://racetrac.wd5.myworkdayjobs.com/SSC",
        website_url="https://www.racetrac.com",
        ats_config={"tenant": "racetrac", "site": "SSC"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value; board is small (~51 total on this corporate-support-office site), scanned in full. Confirmed real, diverse business-relevant postings at verification time: HR, Data Science, Retail Accounting, Pricing and Revenue interns. Implemented.",
        scraper_module="scrapers.companies.racetrac",
        business_relevance_score=7, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Cox Enterprises", slug="cox-enterprises", industry="Media & Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://cox.wd1.myworkdayjobs.com/Cox_External_Career_Site_1",
        website_url="https://www.coxenterprises.com",
        ats_config={"tenant": "cox", "site": "Cox_External_Career_Site_1", "search_text": "intern"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value; `searchText=\"intern\"` narrows the 681-total board to 111, within the pagination safety cap. Confirmed real, diverse business-relevant postings: Analytics, Talent Acquisition, CSR, Finance & IT interns. Implemented.",
        scraper_module="scrapers.companies.cox",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Anheuser-Busch InBev", slug="ab-inbev", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://abinbev.wd1.myworkdayjobs.com/USA",
        website_url="https://www.ab-inbev.com",
        ats_config={"tenant": "abinbev", "site": "USA"},
        notes="Phase 10 Step 3: live-verified. This tenant hosts several region-specific sites (EUR, MEX, BCBU, USA); `USA` confirmed as the correct US-only site. `workerSubType` facet only tags 1 posting as Intern despite real confirmed internship/trainee postings (MBA Intern, Global Supply Chain Masters/MBA/PhD Intern) - board is small (143 total), scanned in full instead. Implemented.",
        scraper_module="scrapers.companies.abinbev",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="International Flavors & Fragrances (IFF)", slug="iff", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://iff.wd5.myworkdayjobs.com/IFF_Careers",
        website_url="https://www.iff.com",
        ats_config={"tenant": "iff", "site": "IFF_Careers", "search_text": "intern"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` facet at all; `searchText=\"intern\"` narrows the 419-total board to 291, within the pagination safety cap. Confirmed real business-relevant postings alongside the scientific majority: HRBP Intern, Marketing Intern, Sales Support Intern. Implemented.",
        scraper_module="scrapers.companies.iff",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Saputo Inc.", slug="saputo", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://saputo.wd5.myworkdayjobs.com/Saputo_External_Careers",
        website_url="https://www.saputo.com",
        ats_config={"tenant": "saputo", "site": "Saputo_External_Careers"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` Intern facet value despite real confirmed postings (Intern Sales Analyst, Intern Finance, Intern Continuous Improvement); board is small (262 total), scanned in full. Canadian company (Montreal HQ) - now a useful target given this platform's US+Canada location display filter (Phase 10 Step 2 follow-up). Implemented.",
        scraper_module="scrapers.companies.saputo",
        business_relevance_score=6, company_reputation_score=4, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Primient", slug="primient", industry="Food & Beverage",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://primient.wd1.myworkdayjobs.com/External_Careers",
        website_url="https://www.primient.com",
        ats_config={"tenant": "primient", "site": "External_Careers"},
        notes="Phase 10 Step 3: live-verified. `workerSubType` Intern facet only tags 1 posting despite real confirmed postings (Tax and Treasury Intern, Digital Data and Analytics Intern, HR Intern); board is small (52 total), scanned in full. Implemented.",
        scraper_module="scrapers.companies.primient",
        business_relevance_score=6, company_reputation_score=3, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Marathon Petroleum Corporation", slug="marathon-petroleum", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://mpc.wd1.myworkdayjobs.com/MPCCareers",
        website_url="https://www.marathonpetroleum.com",
        ats_config={"tenant": "mpc", "site": "MPCCareers", "intern_facet_id": "762d3bc5687201008504b33faf520000"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern\" (17 open postings at verification time, including Finance and Commercial interns). Implemented.",
        scraper_module="scrapers.companies.marathonpetroleum",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Hilcorp Energy Company", slug="hilcorp", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://hec.wd5.myworkdayjobs.com/Hilcorp_Energy_Company",
        website_url="https://www.hilcorp.com",
        ats_config={"tenant": "hec", "site": "Hilcorp_Energy_Company"},
        notes="Phase 10 Step 3: live-verified. `workerSubType` \"Co-Op Student\" facet exists (3 postings) and board is small (33 total, safely scannable in full), but confirmed real postings skew heavily technical (Engineer Intern, Geology Intern) with only occasional business roles (HR Accounting Intern, Office Services Intern). Deprioritized given the 10-15 target and stronger alternatives implemented this phase - not a compliance concern. Revisit in a future pass.",
        business_relevance_score=3, company_reputation_score=4, internship_volume_score=2,
        function_breadth_score=3, ats_accessibility_score=5, evidence_score=7,
    ),
    CompanyRecord(
        name="Medline Industries", slug="medline", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://medline.wd5.myworkdayjobs.com/Medline",
        website_url="https://www.medline.com",
        ats_config={"tenant": "medline", "site": "Medline", "intern_facet_id": "a71dfaf3f3d31000c6fcb5c805bd0001"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (Fixed Term) (Trainee)\" (7 open postings at verification time, including Product Management, Supply Chain, Sales, and Business Operations interns - strong business fit). Implemented.",
        scraper_module="scrapers.companies.medline",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Takeda Pharmaceutical Company", slug="takeda", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://takeda.wd3.myworkdayjobs.com/External",
        website_url="https://www.takeda.com",
        ats_config={"tenant": "takeda", "site": "External"},
        notes="Phase 10 Step 3: this tenant currently returns HTTP 500/422 on both the jobs API and the career page itself (confirmed on multiple attempts, including with a browser User-Agent header) - the same failure pattern as Verizon in Phase 10 Step 2. Real intern postings were found via direct search (US Tax Summer Intern, FP&A Global BioLife Intern), so this is a real, worthwhile target once the endpoint is reachable again. Deferred rather than guessing an alternate tenant/pod.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=3, evidence_score=6,
    ),
    CompanyRecord(
        name="ResMed Inc.", slug="resmed", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://resmed.wd3.myworkdayjobs.com/ResMed_External_Careers",
        website_url="https://www.resmed.com",
        ats_config={"tenant": "resmed", "site": "ResMed_External_Careers", "intern_facet_id": "57129bf02a5f01966a976e3306078f0d"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (Fixed Term)\" - technically clean, but only 2 open postings at verification time and the board is overwhelmingly software/engineering-focused (Software Engineer/Developer, Test Engineering, Automation interns), with only a Digital Marketing Intern as a clear business-relevant exception. Deprioritized given the 10-15 target and stronger alternatives implemented this phase - not a compliance concern. Revisit in a future pass.",
        business_relevance_score=3, company_reputation_score=5, internship_volume_score=2,
        function_breadth_score=3, ats_accessibility_score=6, evidence_score=8,
    ),
    CompanyRecord(
        name="Workiva Inc.", slug="workiva", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.workiva.com",
        notes="Phase 10 Step 3: two direct search attempts this session (including one targeted specifically at job-boards.greenhouse.io/boards.greenhouse.io) found only third-party aggregator listings (Built In, JobRight, Clera, Breakroom) for Workiva's real 2026 internship postings (Software Engineering, Machine Learning, CPX Insights/System interns all confirmed to exist) - no direct Greenhouse (or any ATS host) URL was found. Not scraping via an aggregator per the explicit compliance rule; platform and board token remain unconfirmed.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=1, evidence_score=3,
    ),
    CompanyRecord(
        name="Sierra Nevada Corporation", slug="sierra-nevada-corp", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        career_url="https://snc.wd1.myworkdayjobs.com/SNC_External_Career_Site",
        website_url="https://www.sncorp.com",
        ats_config={"tenant": "snc", "site": "SNC_External_Career_Site", "intern_facet_id": "bd3f3405ddee105b4243e938c45a16d5"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Intern (Trainee)\" - technically clean, but only 1 open posting at verification time and the board (aerospace/defense engineering) shows little historical business-role diversity. Deprioritized given the 10-15 target and stronger alternatives implemented this phase - not a compliance concern. Revisit in a future pass.",
        business_relevance_score=3, company_reputation_score=4, internship_volume_score=1,
        function_breadth_score=3, ats_accessibility_score=6, evidence_score=7,
    ),
    CompanyRecord(
        name="Airbus", slug="airbus", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://ag.wd3.myworkdayjobs.com/Airbus",
        website_url="https://www.airbus.com",
        ats_config={"tenant": "ag", "site": "Airbus", "intern_facet_id": "f5811cef9cb50193723ed01d470a6e15"},
        notes="Phase 10 Step 3: live-verified `workerSubType` facet for \"Trainee / Student (Fixed Term)\" (124 open postings worldwide at verification time - this is Airbus's single global tenant, covering every legal entity including Airbus Americas). A combined workerSubType+hiringCompany query narrowed to just \"Airbus Americas, Inc.\" returned only 2 results, fewer than US postings independently confirmed via direct search, so hiringCompany narrowing was not used. Scrapes globally; the existing frontend US/Canada display filter surfaces the relevant subset, same pattern as Barclays/Disney. Implemented.",
        scraper_module="scrapers.companies.airbus",
        business_relevance_score=5, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="ICF International", slug="icf-international", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_3, status=CompanyStatus.IMPLEMENTED,
        career_url="https://icf.wd5.myworkdayjobs.com/ICFExternal_Career_Site",
        website_url="https://www.icf.com",
        ats_config={"tenant": "icf", "site": "ICFExternal_Career_Site", "search_text": "intern"},
        notes="Phase 10 Step 3: live-verified. No `workerSubType` facet at all; `searchText=\"intern\"` narrows the 378-total board to 132, within the pagination safety cap. Confirmed strong business-relevant postings: Marketing, Business Analyst, Energy Analyst, Program Operations interns. Implemented.",
        scraper_module="scrapers.companies.icf",
        business_relevance_score=8, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=9, evidence_score=10,
    ),
    CompanyRecord(
        name="Shield AI", slug="shield-ai", industry="Aerospace",
        ats=ATSPlatform.LEVER, tier=CompanyTier.TIER_3, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://shield.ai",
        ats_config={"site": "shieldai"},
        notes="Phase 10 Step 3: live-verified public Lever Postings API access (api.lever.co/v0/postings/shieldai, 434 total postings), but zero currently open postings match the internship title pattern (the Production Planning/Data Analyst/Strategy & Operations interns found during earlier research had closed by verification time) - a real, live snapshot fact. Deprioritized rather than implemented given zero current yield and the 10-15 target; the endpoint itself is legitimate and this is a reasonable candidate to revisit in a future pass.",
        business_relevance_score=4, company_reputation_score=5, internship_volume_score=1,
        function_breadth_score=3, ats_accessibility_score=6, evidence_score=7,
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
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=1, evidence_score=3,
    ),
    CompanyRecord(
        name="Charter Communications (Spectrum)", slug="spectrum-charter", industry="Telecommunications",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://corporate.charter.com",
        notes="2026 Summer Intern: Business Analyst posting confirmed to exist via an aggregator (builtin.com), but no direct ATS host URL was observed this session. Same caveat as T-Mobile above.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=1, evidence_score=3,
    ),
    CompanyRecord(
        name="NVIDIA Corporation", slug="nvidia", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.nvidia.com",
        notes="Named as a candidate in earlier research; a direct-evidence search this session returned no live posting URL for any platform. Confirm platform before any further work.",
        business_relevance_score=5, company_reputation_score=9, internship_volume_score=5,
        function_breadth_score=4, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Deloitte", slug="deloitte", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www2.deloitte.com",
        notes="Big 4 peer of PwC (Tier 2, confirmed Workday) and Accenture/Guidehouse (Tier 2, confirmed Workday); plausible Workday tenant but not directly evidenced this session. Do not assume - confirm before promoting.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=8,
        function_breadth_score=7, ats_accessibility_score=3, evidence_score=3,
    ),
    CompanyRecord(
        name="EY (Ernst & Young)", slug="ey", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.ey.com",
        notes="Same caveat as Deloitte above - plausible but unconfirmed this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=8,
        function_breadth_score=7, ats_accessibility_score=3, evidence_score=3,
    ),
    CompanyRecord(
        name="KPMG", slug="kpmg", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_4, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://kpmg.com",
        notes="Same caveat as Deloitte above - plausible but unconfirmed this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=3, evidence_score=3,
    ),
    CompanyRecord(
        name="Commonwealth Bank of Australia", slug="commonwealth-bank-australia", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_4, status=CompanyStatus.EXCLUDED,
        career_url="https://cba.wd3.myworkdayjobs.com/CommBank_Careers",
        website_url="https://www.commbank.com.au",
        ats_config={"tenant": "cba", "site": "CommBank_Careers"},
        notes="Excluded: 2026/27 Global Markets Summer Analyst Campaign observed live, but the program and postings are Australia-based. This platform's location filter only surfaces US/Canada-based (and unlabeled/Remote) postings, so this company's listings would be filtered out of every search result - not a useful scrape target given current product scope.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=9, evidence_score=9,
    ),
]


# ---------------------------------------------------------------------------
# Tier 5 (Phase 10 Step 4) - Broad researched candidate pool. Every entry
# below has a real, distinct, business-relevant employer identified by
# name and industry, with all six subscores assigned from general industry
# knowledge of that company's internship program (structure, size, brand
# recognition among students, functional breadth). ATS platform is an
# INFORMED ESTIMATE ONLY for most entries - based on well-established
# sector patterns already confirmed elsewhere in this registry (e.g. large
# traditional enterprises - CPG, insurance, energy, industrials, banks -
# skew heavily toward Workday; this project has independently confirmed
# Workday at Chevron, Boeing, Disney, Medtronic, Abbott, Assurant, AIA,
# Smucker, GE Aerospace, Barclays, PwC, Truist, TD, Marathon Petroleum,
# and more) - NOT independently verified via a live endpoint this phase.
# Mega-cap tech (Microsoft/Amazon/Google/Apple/Meta), elite consulting
# (MBB), and bulge-bracket investment banks are marked ats=UNKNOWN rather
# than guessed, because these are well known to run custom/proprietary
# campus-recruiting platforms rather than a plain Greenhouse/Workday/Lever
# board - see docs/architecture.md for the full reasoning and the "future
# ATS integration candidates" this implies.
#
# evidence_score is deliberately low (2-3) across this entire tier
# regardless of how confident the ATS estimate is, to keep the scoring
# system honest: nothing here has been live-verified this phase. No
# scraper, ats_config, or scheduler entry exists for anything in this
# tier - per Phase 10 Step 4 Step 8, this phase is research/ranking only.
# ---------------------------------------------------------------------------

_TIER_5: list[CompanyRecord] = [
    # --- Consulting -----------------------------------------------------
    CompanyRecord(
        name="McKinsey & Company", slug="mckinsey", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.mckinsey.com",
        notes="Candidate pool (Step 4). Elite management consultancy with one of the largest, most structured summer Business Analyst programs in the industry. Career site is a custom recruiting platform, not a Greenhouse/Workday/Lever board - ATS unconfirmed, likely needs new integration research. Not verified this session.",
        business_relevance_score=9, company_reputation_score=10, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Bain & Company", slug="bain-and-company", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.bain.com",
        notes="Candidate pool (Step 4). MBB peer of McKinsey/BCG; same custom-platform caveat. Not verified this session.",
        business_relevance_score=9, company_reputation_score=10, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Boston Consulting Group", slug="bcg", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.bcg.com",
        notes="Candidate pool (Step 4). MBB peer of McKinsey/Bain; same custom-platform caveat. Not verified this session.",
        business_relevance_score=9, company_reputation_score=10, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Oliver Wyman", slug="oliver-wyman", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.oliverwyman.com",
        notes="Candidate pool (Step 4). Tier-2 strategy consultancy (Marsh McLennan subsidiary), strong Finance/Strategy internship relevance. Not verified this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="L.E.K. Consulting", slug="lek-consulting", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.lek.com",
        notes="Candidate pool (Step 4). Boutique strategy consultancy, structured summer associate program. Not verified this session.",
        business_relevance_score=9, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Roland Berger", slug="roland-berger", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.rolandberger.com",
        notes="Candidate pool (Step 4). Global strategy consultancy, smaller US footprint than MBB. Not verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=2,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Booz Allen Hamilton", slug="booz-allen-hamilton", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.boozallen.com",
        notes="Candidate pool (Step 4). Large government/management consultancy with a sizable structured internship program; similar profile to already-implemented ICF/Guidehouse. Platform not confirmed this session - worth an early confirmation pass given the ICF/Guidehouse precedent.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=3, evidence_score=2,
    ),
    CompanyRecord(
        name="West Monroe", slug="west-monroe", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.westmonroe.com",
        notes="Candidate pool (Step 4). Mid-size management/technology consultancy with a known structured internship program. Not verified this session.",
        business_relevance_score=8, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=3, evidence_score=2,
    ),
    CompanyRecord(
        name="Alvarez & Marsal", slug="alvarez-and-marsal", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.alvarezandmarsal.com",
        notes="Candidate pool (Step 4). Restructuring/turnaround and performance-improvement consultancy, strong Finance relevance. Not verified this session.",
        business_relevance_score=9, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=3, evidence_score=2,
    ),
    CompanyRecord(
        name="A.T. Kearney", slug="at-kearney", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.kearney.com",
        notes="Candidate pool (Step 4). Global strategy/operations consultancy. Not verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=2,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Protiviti", slug="protiviti", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.protiviti.com",
        notes="Candidate pool (Step 4). Risk/internal-audit/technology consulting (Robert Half subsidiary), large structured campus program. Not verified this session.",
        business_relevance_score=8, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=3, evidence_score=2,
    ),
    CompanyRecord(
        name="Slalom Consulting", slug="slalom", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.slalom.com",
        notes="Candidate pool (Step 4). Business/technology consultancy with a growing early-career program. Not verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=3, evidence_score=2,
    ),
    CompanyRecord(
        name="ZS Associates", slug="zs-associates", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.zs.com",
        notes="Candidate pool (Step 4). Life-sciences/healthcare-focused management consultancy and analytics firm. Not verified this session.",
        business_relevance_score=8, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=3, evidence_score=2,
    ),
    CompanyRecord(
        name="Simon-Kucher & Partners", slug="simon-kucher", industry="Consulting",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.simon-kucher.com",
        notes="Candidate pool (Step 4). Pricing/growth strategy boutique consultancy. Not verified this session.",
        business_relevance_score=8, company_reputation_score=4, internship_volume_score=2,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Grant Thornton", slug="grant-thornton", industry="Consulting",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.grantthornton.com",
        notes="Candidate pool (Step 4). Large accounting/advisory firm; Workday estimated by analogy to PwC (Tier 2, confirmed Workday) - not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Investment Banking / Financial Services -------------------------
    CompanyRecord(
        name="Goldman Sachs", slug="goldman-sachs", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.goldmansachs.com",
        notes="Candidate pool (Step 4). Bulge-bracket IB with one of the largest, most structured Summer Analyst programs in finance. Custom proprietary recruiting platform, not a Greenhouse/Workday/Lever board - ATS unconfirmed. Not verified this session.",
        business_relevance_score=10, company_reputation_score=10, internship_volume_score=9,
        function_breadth_score=7, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="JPMorgan Chase", slug="jpmorgan-chase", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.jpmorganchase.com",
        notes="Candidate pool (Step 4). Largest US bank by assets; massive structured Summer Analyst program across IB/Markets/Corporate. Custom proprietary campus platform. Not verified this session.",
        business_relevance_score=10, company_reputation_score=10, internship_volume_score=10,
        function_breadth_score=8, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Morgan Stanley", slug="morgan-stanley", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.morganstanley.com",
        notes="Candidate pool (Step 4). Bulge-bracket IB/wealth management; large Summer Analyst program. Custom platform. Not verified this session.",
        business_relevance_score=10, company_reputation_score=10, internship_volume_score=8,
        function_breadth_score=7, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Bank of America", slug="bank-of-america", industry="Financial Services",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.bankofamerica.com",
        notes="Candidate pool (Step 4). Bulge-bracket bank with a very large campus recruiting program spanning IB, Global Markets, and retail banking. Custom platform. Not verified this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=9,
        function_breadth_score=8, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Citigroup", slug="citigroup", industry="Financial Services",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.citigroup.com",
        notes="Candidate pool (Step 4). Global bank, large structured campus program. Custom platform. Not verified this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=8,
        function_breadth_score=8, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Wells Fargo", slug="wells-fargo", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.wellsfargo.com",
        notes="Candidate pool (Step 4). Large US bank; Workday estimated by analogy to Truist/TD (both Tier 2, confirmed Workday tenants) - not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="UBS", slug="ubs", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.ubs.com",
        notes="Candidate pool (Step 4). Global bank/wealth manager, large campus program. Custom platform. Not verified this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Deutsche Bank", slug="deutsche-bank", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.db.com",
        notes="Candidate pool (Step 4). Global bank, structured Summer Analyst program. Custom platform. Not verified this session.",
        business_relevance_score=9, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Jefferies Financial Group", slug="jefferies", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.jefferies.com",
        notes="Candidate pool (Step 4). Independent full-service investment bank, sizable Summer Analyst class. Not verified this session.",
        business_relevance_score=9, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Evercore", slug="evercore", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.evercore.com",
        notes="Candidate pool (Step 4). Elite boutique advisory bank, small but highly-regarded Summer Analyst program. Not verified this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Lazard", slug="lazard", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.lazard.com",
        notes="Candidate pool (Step 4). Elite boutique advisory bank. Not verified this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Moelis & Company", slug="moelis", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.moelis.com",
        notes="Candidate pool (Step 4). Elite boutique advisory bank. Not verified this session.",
        business_relevance_score=9, company_reputation_score=7, internship_volume_score=2,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Houlihan Lokey", slug="houlihan-lokey", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.hl.com",
        notes="Candidate pool (Step 4). Mid-market M&A/restructuring bank, large deal volume and campus presence. Not verified this session.",
        business_relevance_score=9, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Raymond James Financial", slug="raymond-james", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.raymondjames.com",
        notes="Candidate pool (Step 4). Diversified financial services firm; Workday estimated by analogy to similarly-sized regional/diversified banks already confirmed in this registry. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="William Blair", slug="william-blair", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.williamblair.com",
        notes="Candidate pool (Step 4). Independent investment bank and asset manager. Not verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Stifel Financial", slug="stifel", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.stifel.com",
        notes="Candidate pool (Step 4). Full-service investment bank/wealth manager; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Harris Williams", slug="harris-williams", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.harriswilliams.com",
        notes="Candidate pool (Step 4). Mid-market M&A advisory boutique (PNC subsidiary). Not verified this session.",
        business_relevance_score=8, company_reputation_score=5, internship_volume_score=2,
        function_breadth_score=3, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Rothschild & Co", slug="rothschild-and-co", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.rothschildandco.com",
        notes="Candidate pool (Step 4). Independent global advisory bank. Not verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=2,
        function_breadth_score=3, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Centerview Partners", slug="centerview-partners", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.centerview.com",
        notes="Candidate pool (Step 4). Elite boutique M&A advisory firm. Not verified this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=2,
        function_breadth_score=3, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Guggenheim Partners", slug="guggenheim-partners", industry="Investment Banking",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.guggenheimpartners.com",
        notes="Candidate pool (Step 4). Global investment/advisory firm. Not verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="PNC Financial Services", slug="pnc-financial", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.pnc.com",
        notes="Candidate pool (Step 4). Large regional bank; Workday estimated by analogy to Truist/TD. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="U.S. Bancorp", slug="us-bancorp", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.usbank.com",
        notes="Candidate pool (Step 4). Large regional bank; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Capital One", slug="capital-one", industry="Financial Services",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.capitalone.com",
        notes="Candidate pool (Step 4). Large bank with a well-known, large, tech-forward internship program (Business Analyst, Product, Finance tracks). Career site is custom/tech-forward - platform uncertain. Not verified this session.",
        business_relevance_score=8, company_reputation_score=8, internship_volume_score=7,
        function_breadth_score=6, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Ally Financial", slug="ally-financial", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.ally.com",
        notes="Candidate pool (Step 4). Digital-first bank; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Charles Schwab", slug="charles-schwab", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.schwab.com",
        notes="Candidate pool (Step 4). Large brokerage/wealth management firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Edward Jones", slug="edward-jones", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.edwardjones.com",
        notes="Candidate pool (Step 4). Large wealth-management firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=4, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Northwestern Mutual", slug="northwestern-mutual", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.northwesternmutual.com",
        notes="Candidate pool (Step 4). Large insurance/wealth-management firm with a well-known college financial-representative internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=6,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Discover Financial Services", slug="discover-financial", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.discover.com",
        notes="Candidate pool (Step 4). Card issuer/digital bank; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Synchrony Financial", slug="synchrony-financial", industry="Financial Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.synchrony.com",
        notes="Candidate pool (Step 4). Consumer financial services firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Asset Management / Investment Management -------------------------
    CompanyRecord(
        name="BlackRock", slug="blackrock", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.blackrock.com",
        notes="Candidate pool (Step 4). World's largest asset manager, large structured Summer Analyst program; Workday estimated by analogy to Invesco (Tier 1, confirmed Workday). Not independently verified this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="The Vanguard Group", slug="vanguard", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.vanguard.com",
        notes="Candidate pool (Step 4). Massive index/mutual fund manager; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Fidelity Investments", slug="fidelity-investments", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.fidelity.com",
        notes="Candidate pool (Step 4). Large asset manager/brokerage with a well-known large internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=8, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="State Street Corporation", slug="state-street", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.statestreet.com",
        notes="Candidate pool (Step 4). Large custody bank/asset manager; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Capital Group", slug="capital-group", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.capitalgroup.com",
        notes="Candidate pool (Step 4). Large active asset manager (American Funds); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="T. Rowe Price", slug="t-rowe-price", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.troweprice.com",
        notes="Candidate pool (Step 4). Large active asset manager; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Franklin Templeton", slug="franklin-templeton", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.franklintempleton.com",
        notes="Candidate pool (Step 4). Global asset manager; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="PIMCO", slug="pimco", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.pimco.com",
        notes="Candidate pool (Step 4). Elite fixed-income asset manager. Not verified this session.",
        business_relevance_score=8, company_reputation_score=8, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Wellington Management", slug="wellington-management", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.wellington.com",
        notes="Candidate pool (Step 4). Large private active asset manager. Not verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Northern Trust", slug="northern-trust", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.northerntrust.com",
        notes="Candidate pool (Step 4). Custody bank/wealth manager with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Ares Management", slug="ares-management", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.aresmgmt.com",
        notes="Candidate pool (Step 4). Alternative asset manager (private credit/equity); typically smaller, more custom recruiting platform than traditional asset managers. Not verified this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Apollo Global Management", slug="apollo-global-management", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.apollo.com",
        notes="Candidate pool (Step 4). Major alternative asset manager (PE/credit). Not verified this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="KKR & Co.", slug="kkr", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.kkr.com",
        notes="Candidate pool (Step 4). Major private equity firm. Not verified this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Blackstone Inc.", slug="blackstone", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.blackstone.com",
        notes="Candidate pool (Step 4). World's largest alternative asset manager (PE/real estate/credit). Not verified this session.",
        business_relevance_score=9, company_reputation_score=10, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="The Carlyle Group", slug="carlyle-group", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.carlyle.com",
        notes="Candidate pool (Step 4). Major global private equity firm. Not verified this session.",
        business_relevance_score=9, company_reputation_score=8, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Neuberger Berman", slug="neuberger-berman", industry="Investment Management",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.nb.com",
        notes="Candidate pool (Step 4). Employee-owned active asset manager. Not verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=2,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Janus Henderson", slug="janus-henderson", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.janushenderson.com",
        notes="Candidate pool (Step 4). Global active asset manager; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="PGIM", slug="pgim", industry="Investment Management",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.pgim.com",
        notes="Candidate pool (Step 4). Prudential's asset-management arm; Workday estimated by analogy to parent company sector pattern. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Insurance ---------------------------------------------------------
    CompanyRecord(
        name="American International Group (AIG)", slug="aig", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.aig.com",
        notes="Candidate pool (Step 4). Large multiline insurer; Workday estimated by analogy to Assurant/AIA (both already confirmed Workday). Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="State Farm Insurance", slug="state-farm", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.statefarm.com",
        notes="Candidate pool (Step 4). Largest US personal-lines insurer, large structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Progressive Corporation", slug="progressive", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.progressive.com",
        notes="Candidate pool (Step 4). Large auto insurer with a well-known large structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Allstate Corporation", slug="allstate", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.allstate.com",
        notes="Candidate pool (Step 4). Large multiline insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Travelers Companies", slug="travelers", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.travelers.com",
        notes="Candidate pool (Step 4). Large commercial/personal insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Liberty Mutual Insurance", slug="liberty-mutual", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.libertymutual.com",
        notes="Candidate pool (Step 4). Large mutual insurer with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Chubb Limited", slug="chubb", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.chubb.com",
        notes="Candidate pool (Step 4). Large commercial P&C insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Nationwide Mutual Insurance", slug="nationwide", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.nationwide.com",
        notes="Candidate pool (Step 4). Large mutual insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="USAA", slug="usaa", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.usaa.com",
        notes="Candidate pool (Step 4). Large military-affiliated insurer/bank with a well-regarded internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="MetLife", slug="metlife", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.metlife.com",
        notes="Candidate pool (Step 4). Large multiline insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Prudential Financial", slug="prudential-financial", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.prudential.com",
        notes="Candidate pool (Step 4). Large insurance/asset-management conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Marsh McLennan", slug="marsh-mclennan", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.marshmclennan.com",
        notes="Candidate pool (Step 4). Largest insurance broker/professional-services firm (parent of Oliver Wyman); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="The Hartford", slug="the-hartford", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.thehartford.com",
        notes="Candidate pool (Step 4). Large commercial/personal insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Aon plc", slug="aon", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.aon.com",
        notes="Candidate pool (Step 4). Large insurance broker/professional-services firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Willis Towers Watson", slug="willis-towers-watson", industry="Insurance",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.wtwco.com",
        notes="Candidate pool (Step 4). Large insurance broker/professional-services firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Technology ----------------------------------------------------
    CompanyRecord(
        name="Microsoft Corporation", slug="microsoft", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.microsoft.com",
        notes="Candidate pool (Step 4). Mega-cap tech with a very large, well-known internship program spanning business functions (Finance, Marketing, BizApps, Product) as well as engineering. Custom large-scale proprietary careers platform, not a Greenhouse/Workday/Lever board. Not verified this session.",
        business_relevance_score=6, company_reputation_score=10, internship_volume_score=9,
        function_breadth_score=8, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Amazon.com, Inc.", slug="amazon", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.amazon.com",
        notes="Candidate pool (Step 4). Mega-cap tech/retail with a massive internship program including business-heavy tracks (Finance, Operations, Product, HR). Custom large-scale proprietary careers platform. Not verified this session.",
        business_relevance_score=6, company_reputation_score=10, internship_volume_score=10,
        function_breadth_score=9, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Alphabet Inc. (Google)", slug="google", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.google.com",
        notes="Candidate pool (Step 4). Mega-cap tech; large internship program with real business tracks (BOLD, Marketing, Finance, gTech) alongside engineering. Custom proprietary careers platform. Not verified this session.",
        business_relevance_score=6, company_reputation_score=10, internship_volume_score=8,
        function_breadth_score=7, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Apple Inc.", slug="apple", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.apple.com",
        notes="Candidate pool (Step 4). Mega-cap tech; internship program skews engineering/design but includes Finance, Marketing, Ops tracks. Custom proprietary careers platform. Not verified this session.",
        business_relevance_score=5, company_reputation_score=10, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Meta Platforms, Inc.", slug="meta-platforms", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://about.meta.com",
        notes="Candidate pool (Step 4). Mega-cap tech; large internship program with real business tracks (BizOps, Finance, Marketing, People). Custom proprietary careers platform. Not verified this session.",
        business_relevance_score=6, company_reputation_score=10, internship_volume_score=7,
        function_breadth_score=6, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Salesforce, Inc.", slug="salesforce", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.salesforce.com",
        notes="Candidate pool (Step 4). Large enterprise SaaS company, well-known Futureforce internship program with real business tracks (Sales, Marketing, BizTech). Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Adobe Inc.", slug="adobe", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.adobe.com",
        notes="Candidate pool (Step 4). Large enterprise software company with Finance/Marketing/BizDev internship tracks alongside engineering. Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Oracle Corporation", slug="oracle", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.oracle.com",
        notes="Candidate pool (Step 4). Large enterprise software company; platform uncertain at this scale. Not verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Cisco Systems", slug="cisco-systems", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.cisco.com",
        notes="Candidate pool (Step 4). Large networking/enterprise tech company. Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="IBM", slug="ibm", industry="Technology",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.ibm.com",
        notes="Candidate pool (Step 4). Large legacy enterprise tech/consulting company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Dell Technologies", slug="dell-technologies", industry="Technology",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.dell.com",
        notes="Candidate pool (Step 4). Large hardware/enterprise tech company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Intuit Inc.", slug="intuit", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.intuit.com",
        notes="Candidate pool (Step 4). Financial software company (QuickBooks/TurboTax) with real Finance/Marketing internship tracks. Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="ServiceNow", slug="servicenow", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.servicenow.com",
        notes="Candidate pool (Step 4). Large enterprise SaaS company. Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Workday, Inc.", slug="workday-inc", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.workday.com",
        notes="Candidate pool (Step 4). HR/Finance SaaS company - notably, the ATS vendor itself; its own careers site is not necessarily hosted on its own consumer Workday board. Platform unconfirmed. Not verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Datadog, Inc.", slug="datadog", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.datadoghq.com",
        notes="Candidate pool (Step 4). Cloud monitoring SaaS company; Greenhouse estimated (common pattern among similarly-sized tech companies, e.g. Cloudflare/Braze/Robinhood already confirmed on Greenhouse). Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Snowflake Inc.", slug="snowflake", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.snowflake.com",
        notes="Candidate pool (Step 4). Cloud data platform company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Databricks, Inc.", slug="databricks", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.databricks.com",
        notes="Candidate pool (Step 4). Data/AI platform company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="HubSpot, Inc.", slug="hubspot", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.hubspot.com",
        notes="Candidate pool (Step 4). Marketing/sales SaaS company with strong Marketing/Sales internship relevance; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="LinkedIn Corporation", slug="linkedin", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.linkedin.com",
        notes="Candidate pool (Step 4). Professional-network platform (Microsoft subsidiary) with real business-side internship tracks (Sales, Marketing, BizOps). Platform likely tied to Microsoft's own custom system. Not verified this session.",
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Intel Corporation", slug="intel", industry="Technology",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.intel.com",
        notes="Candidate pool (Step 4). Large semiconductor company; Workday estimated by analogy to Applied Materials/GlobalFoundries (both already confirmed Workday in the semiconductor sector). Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Qualcomm Incorporated", slug="qualcomm", industry="Technology",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.qualcomm.com",
        notes="Candidate pool (Step 4). Large semiconductor/wireless tech company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Texas Instruments", slug="texas-instruments", industry="Technology",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.ti.com",
        notes="Candidate pool (Step 4). Large semiconductor company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Palo Alto Networks", slug="palo-alto-networks", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.paloaltonetworks.com",
        notes="Candidate pool (Step 4). Large cybersecurity company. Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="CrowdStrike Holdings", slug="crowdstrike", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.crowdstrike.com",
        notes="Candidate pool (Step 4). Large cybersecurity company. Platform uncertain. Not verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Zoom Communications", slug="zoom", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.zoom.com",
        notes="Candidate pool (Step 4). Video communications SaaS company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Atlassian Corporation", slug="atlassian", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.atlassian.com",
        notes="Candidate pool (Step 4). Large enterprise SaaS company. Platform uncertain. Not verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Block, Inc.", slug="block-inc", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://block.xyz",
        notes="Candidate pool (Step 4). Fintech company (Square/Cash App); Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="PayPal Holdings", slug="paypal", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.paypal.com",
        notes="Candidate pool (Step 4). Large fintech/payments company. Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Etsy, Inc.", slug="etsy", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.etsy.com",
        notes="Candidate pool (Step 4). E-commerce marketplace company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Shopify Inc.", slug="shopify", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.shopify.com",
        notes="Candidate pool (Step 4). E-commerce platform company (Canada-based, relevant given this platform's US+Canada scope); Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Uber Technologies", slug="uber", industry="Technology",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.uber.com",
        notes="Candidate pool (Step 4). Large ride-share/delivery tech company with real business tracks (Strategy & Planning, Marketing, Finance). Platform uncertain at this scale. Not verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Lyft, Inc.", slug="lyft", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.lyft.com",
        notes="Candidate pool (Step 4). Ride-share tech company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="DoorDash, Inc.", slug="doordash", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.doordash.com",
        notes="Candidate pool (Step 4). Food-delivery platform company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Airbnb, Inc.", slug="airbnb", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.airbnb.com",
        notes="Candidate pool (Step 4). Large travel-marketplace tech company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Coinbase Global", slug="coinbase", industry="Technology",
        ats=ATSPlatform.GREENHOUSE, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.coinbase.com",
        notes="Candidate pool (Step 4). Cryptocurrency exchange company; Greenhouse estimated by sector pattern. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=6, evidence_score=2,
    ),

    # --- Healthcare / Pharma ---------------------------------------------
    CompanyRecord(
        name="Eli Lilly and Company", slug="eli-lilly", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.lilly.com",
        notes="Candidate pool (Step 4). Large pharmaceutical company; Workday estimated by analogy to Abbott/Medtronic (both already confirmed Workday). Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Johnson & Johnson", slug="johnson-and-johnson", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.jnj.com",
        notes="Candidate pool (Step 4). Large diversified healthcare/pharma company with a well-known large internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=9, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Pfizer Inc.", slug="pfizer", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.pfizer.com",
        notes="Candidate pool (Step 4). Large pharmaceutical company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=9, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Merck & Co.", slug="merck", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.merck.com",
        notes="Candidate pool (Step 4). Large pharmaceutical company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="AbbVie Inc.", slug="abbvie", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.abbvie.com",
        notes="Candidate pool (Step 4). Large pharmaceutical company (Abbott spinoff); Workday estimated by analogy to former parent Abbott (already confirmed Workday). Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Bristol Myers Squibb", slug="bristol-myers-squibb", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.bms.com",
        notes="Candidate pool (Step 4). Large pharmaceutical company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Amgen Inc.", slug="amgen", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.amgen.com",
        notes="Candidate pool (Step 4). Large biotech company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Gilead Sciences", slug="gilead-sciences", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.gilead.com",
        notes="Candidate pool (Step 4). Large biotech company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="UnitedHealth Group", slug="unitedhealth-group", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.unitedhealthgroup.com",
        notes="Candidate pool (Step 4). Largest US health insurer, large structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="CVS Health", slug="cvs-health", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.cvshealth.com",
        notes="Candidate pool (Step 4). Large healthcare/retail conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="The Cigna Group", slug="cigna", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.cigna.com",
        notes="Candidate pool (Step 4). Large health insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Thermo Fisher Scientific", slug="thermo-fisher-scientific", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.thermofisher.com",
        notes="Candidate pool (Step 4). Large life-sciences/lab equipment company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Boston Scientific", slug="boston-scientific", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.bostonscientific.com",
        notes="Candidate pool (Step 4). Large medical-device company; Workday estimated by analogy to Medtronic (already confirmed Workday). Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Stryker Corporation", slug="stryker", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.stryker.com",
        notes="Candidate pool (Step 4). Large medical-device company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Cardinal Health", slug="cardinal-health", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.cardinalhealth.com",
        notes="Candidate pool (Step 4). Large healthcare distribution company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="McKesson Corporation", slug="mckesson", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.mckesson.com",
        notes="Candidate pool (Step 4). Large healthcare distribution company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Humana Inc.", slug="humana", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.humana.com",
        notes="Candidate pool (Step 4). Large health insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Elevance Health", slug="elevance-health", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.elevancehealth.com",
        notes="Candidate pool (Step 4). Large health insurer (formerly Anthem); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Centene Corporation", slug="centene", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.centene.com",
        notes="Candidate pool (Step 4). Large managed-care health insurer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=4, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="HCA Healthcare", slug="hca-healthcare", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.hcahealthcare.com",
        notes="Candidate pool (Step 4). Large hospital operator; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Danaher Corporation", slug="danaher", industry="Healthcare",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.danaher.com",
        notes="Candidate pool (Step 4). Large diversified life-sciences conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Consumer / CPG ----------------------------------------------------
    CompanyRecord(
        name="Procter & Gamble", slug="procter-and-gamble", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.pg.com",
        notes="Candidate pool (Step 4). Largest US CPG company with one of the most famous structured internship programs (Brand Management, Finance, Sales, Supply Chain); Workday estimated by analogy to Smucker (Tier 1, confirmed Workday). Not independently verified this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=8,
        function_breadth_score=8, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="PepsiCo, Inc.", slug="pepsico", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.pepsico.com",
        notes="Candidate pool (Step 4). Large CPG/food-and-beverage company, well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=9, company_reputation_score=9, internship_volume_score=7,
        function_breadth_score=8, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="The Coca-Cola Company", slug="coca-cola", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.coca-colacompany.com",
        notes="Candidate pool (Step 4). Iconic CPG/beverage company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=10, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Unilever", slug="unilever", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.unilever.com",
        notes="Candidate pool (Step 4). Large global CPG company with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Colgate-Palmolive", slug="colgate-palmolive", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.colgatepalmolive.com",
        notes="Candidate pool (Step 4). Large CPG company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Mondelez International", slug="mondelez", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.mondelezinternational.com",
        notes="Candidate pool (Step 4). Large global snack-food CPG company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Kraft Heinz", slug="kraft-heinz", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.kraftheinzcompany.com",
        notes="Candidate pool (Step 4). Large CPG/food company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="General Mills", slug="general-mills", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.generalmills.com",
        notes="Candidate pool (Step 4). Large CPG/food company; Workday estimated by analogy to Smucker (already confirmed Workday in this same sub-sector). Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Nestle USA", slug="nestle-usa", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.nestleusa.com",
        notes="Candidate pool (Step 4). Large global CPG/food company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Kimberly-Clark", slug="kimberly-clark", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.kimberly-clark.com",
        notes="Candidate pool (Step 4). Large CPG company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Nike, Inc.", slug="nike", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.nike.com",
        notes="Candidate pool (Step 4). Iconic apparel/footwear brand with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=9, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="L'Oreal USA", slug="loreal-usa", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.lorealusa.com",
        notes="Candidate pool (Step 4). Large beauty/CPG company with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Estee Lauder Companies", slug="estee-lauder", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.elcompanies.com",
        notes="Candidate pool (Step 4). Large beauty/CPG company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Church & Dwight", slug="church-and-dwight", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://church-dwight.com",
        notes="Candidate pool (Step 4). Mid-size CPG company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="The Clorox Company", slug="clorox", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.thecloroxcompany.com",
        notes="Candidate pool (Step 4). Mid-size CPG company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="The Hershey Company", slug="hershey", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.thehersheycompany.com",
        notes="Candidate pool (Step 4). Well-known CPG/confectionery company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Campbell's Company", slug="campbells", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.campbells.com",
        notes="Candidate pool (Step 4). Mid-size CPG/food company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Conagra Brands", slug="conagra-brands", industry="Consumer Goods",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.conagrabrands.com",
        notes="Candidate pool (Step 4). Large CPG/food company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Retail / E-commerce ------------------------------------------------
    CompanyRecord(
        name="Walmart Inc.", slug="walmart", industry="Retail",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://corporate.walmart.com",
        notes="Candidate pool (Step 4). Largest US retailer by revenue, well-known large corporate internship program. Custom large-scale proprietary careers platform. Not verified this session.",
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=8,
        function_breadth_score=8, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Target Corporation", slug="target", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://corporate.target.com",
        notes="Candidate pool (Step 4). Large retailer with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=8, internship_volume_score=7,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Costco Wholesale", slug="costco", industry="Retail",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.costco.com",
        notes="Candidate pool (Step 4). Large warehouse-club retailer; smaller/less-structured corporate internship footprint historically. Platform unconfirmed. Not verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="The Home Depot", slug="home-depot", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://corporate.homedepot.com",
        notes="Candidate pool (Step 4). Large home-improvement retailer with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Lowe's Companies", slug="lowes", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://corporate.lowes.com",
        notes="Candidate pool (Step 4). Large home-improvement retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Best Buy Co.", slug="best-buy", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://corporate.bestbuy.com",
        notes="Candidate pool (Step 4). Large electronics retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Macy's, Inc.", slug="macys", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.macysinc.com",
        notes="Candidate pool (Step 4). Large department-store retailer with a historically well-known executive-development internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="TJX Companies", slug="tjx-companies", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.tjx.com",
        notes="Candidate pool (Step 4). Large off-price retailer (TJ Maxx/Marshalls); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Wayfair Inc.", slug="wayfair", industry="Retail",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.wayfair.com",
        notes="Candidate pool (Step 4). E-commerce home-goods retailer with a known structured internship program. Platform uncertain. Not verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Kroger Co.", slug="kroger", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.thekrogerco.com",
        notes="Candidate pool (Step 4). Large grocery retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Albertsons Companies", slug="albertsons", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.albertsonscompanies.com",
        notes="Candidate pool (Step 4). Large grocery retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Nordstrom, Inc.", slug="nordstrom", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.nordstrom.com",
        notes="Candidate pool (Step 4). Large department-store retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Gap Inc.", slug="gap-inc", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.gapinc.com",
        notes="Candidate pool (Step 4). Large apparel retailer with a known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Ross Stores", slug="ross-stores", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.rossstores.com",
        notes="Candidate pool (Step 4). Large off-price retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Dollar General", slug="dollar-general", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.dollargeneral.com",
        notes="Candidate pool (Step 4). Large discount retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=4, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Ulta Beauty", slug="ulta-beauty", industry="Retail",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.ulta.com",
        notes="Candidate pool (Step 4). Beauty specialty retailer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Automotive / Manufacturing -----------------------------------------
    CompanyRecord(
        name="Ford Motor Company", slug="ford-motor", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://corporate.ford.com",
        notes="Candidate pool (Step 4). Major automaker with a well-known large structured internship program (Finance, Marketing, Ops); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="General Motors", slug="general-motors", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.gm.com",
        notes="Candidate pool (Step 4). Major automaker with a well-known large structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="Toyota Motor North America", slug="toyota-north-america", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.toyota.com",
        notes="Candidate pool (Step 4). Major automaker's North American arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="Honda North America", slug="honda-north-america", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.honda.com",
        notes="Candidate pool (Step 4). Major automaker's North American arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="Tesla, Inc.", slug="tesla", industry="Automotive",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.tesla.com",
        notes="Candidate pool (Step 4). High-profile EV maker with a large internship program, but a well-known custom/proprietary careers platform. Not verified this session.",
        business_relevance_score=5, company_reputation_score=9, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Stellantis North America", slug="stellantis-north-america", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.stellantis.com",
        notes="Candidate pool (Step 4). Major automaker (Chrysler/Jeep/Ram parent); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="BMW of North America", slug="bmw-north-america", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.bmwusa.com",
        notes="Candidate pool (Step 4). Major automaker's North American arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="Mercedes-Benz USA", slug="mercedes-benz-usa", industry="Automotive",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.mbusa.com",
        notes="Candidate pool (Step 4). Major automaker's US arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="Caterpillar Inc.", slug="caterpillar", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.caterpillar.com",
        notes="Candidate pool (Step 4). Large heavy-equipment manufacturer with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="John Deere (Deere & Company)", slug="john-deere", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.deere.com",
        notes="Candidate pool (Step 4). Large agricultural-equipment manufacturer with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Honeywell International", slug="honeywell", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.honeywell.com",
        notes="Candidate pool (Step 4). Large diversified industrial conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Siemens USA", slug="siemens-usa", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.usa.siemens.com",
        notes="Candidate pool (Step 4). Large diversified industrial/tech conglomerate's US arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Schneider Electric USA", slug="schneider-electric-usa", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.se.com",
        notes="Candidate pool (Step 4). Large energy-management/automation company's US arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Emerson Electric", slug="emerson-electric", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.emerson.com",
        notes="Candidate pool (Step 4). Large diversified industrial company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Illinois Tool Works", slug="illinois-tool-works", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.itw.com",
        notes="Candidate pool (Step 4). Large diversified industrial conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Parker Hannifin", slug="parker-hannifin", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.parker.com",
        notes="Candidate pool (Step 4). Large motion/control-technologies manufacturer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Eaton Corporation", slug="eaton", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.eaton.com",
        notes="Candidate pool (Step 4). Large power-management industrial company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Cummins Inc.", slug="cummins", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.cummins.com",
        notes="Candidate pool (Step 4). Large engine/power manufacturer; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Energy --------------------------------------------------------
    CompanyRecord(
        name="ExxonMobil Corporation", slug="exxonmobil", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://corporate.exxonmobil.com",
        notes="Candidate pool (Step 4). Largest US oil major with a well-known large structured internship program; Workday estimated by analogy to Chevron/Marathon Petroleum (both already confirmed Workday). Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Shell USA", slug="shell-usa", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.shell.us",
        notes="Candidate pool (Step 4). Major oil company's US arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=7, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="BP America", slug="bp-america", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.bp.com/en_us",
        notes="Candidate pool (Step 4). Major oil company's US arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="ConocoPhillips", slug="conocophillips", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.conocophillips.com",
        notes="Candidate pool (Step 4). Large independent E&P company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Valero Energy", slug="valero-energy", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.valero.com",
        notes="Candidate pool (Step 4). Large refining company; Workday estimated by analogy to Marathon Petroleum (already confirmed Workday in this same sub-sector). Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Phillips 66", slug="phillips-66", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.phillips66.com",
        notes="Candidate pool (Step 4). Large refining/midstream company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="NextEra Energy", slug="nextera-energy", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.nexteraenergy.com",
        notes="Candidate pool (Step 4). Large utility/renewables company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Duke Energy", slug="duke-energy", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.duke-energy.com",
        notes="Candidate pool (Step 4). Large regulated utility; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Occidental Petroleum", slug="occidental-petroleum", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.oxy.com",
        notes="Candidate pool (Step 4). Large independent E&P company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Williams Companies", slug="williams-companies", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.williams.com",
        notes="Candidate pool (Step 4). Large midstream/natural-gas infrastructure company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Kinder Morgan", slug="kinder-morgan", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.kindermorgan.com",
        notes="Candidate pool (Step 4). Large midstream energy infrastructure company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="EOG Resources", slug="eog-resources", industry="Energy",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.eogresources.com",
        notes="Candidate pool (Step 4). Large independent E&P company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Media / Entertainment -----------------------------------------
    CompanyRecord(
        name="NBCUniversal", slug="nbcuniversal", industry="Media & Entertainment",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.nbcuniversal.com",
        notes="Candidate pool (Step 4). Major media conglomerate (Comcast subsidiary) with a well-known structured Page/internship program; Workday estimated by analogy to Disney (already confirmed Workday). Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Warner Bros. Discovery", slug="warner-bros-discovery", industry="Media & Entertainment",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.wbd.com",
        notes="Candidate pool (Step 4). Major media conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Paramount Global", slug="paramount-global", industry="Media & Entertainment",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.paramount.com",
        notes="Candidate pool (Step 4). Major media conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Netflix, Inc.", slug="netflix", industry="Media & Entertainment",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.netflix.com",
        notes="Candidate pool (Step 4). Leading streaming company; well known for a highly custom, culture-driven careers platform rather than a standard ATS board. Not verified this session.",
        business_relevance_score=5, company_reputation_score=9, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=1, evidence_score=2,
    ),
    CompanyRecord(
        name="Sony Pictures Entertainment", slug="sony-pictures", industry="Media & Entertainment",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.sonypictures.com",
        notes="Candidate pool (Step 4). Major film/TV studio; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="ESPN", slug="espn", industry="Media & Entertainment",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.espn.com",
        notes="Candidate pool (Step 4). Major sports media brand (Disney subsidiary); Workday estimated by analogy to parent Disney (already confirmed Workday). Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=8, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Telecommunications ----------------------------------------------
    CompanyRecord(
        name="AT&T Inc.", slug="at-and-t", industry="Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://about.att.com",
        notes="Candidate pool (Step 4). Major telecom carrier; Workday estimated by analogy to Verizon (Tier 2, same platform though currently outage-affected). Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="Comcast Corporation", slug="comcast", industry="Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://corporate.comcast.com",
        notes="Candidate pool (Step 4). Major telecom/media conglomerate (parent of NBCUniversal); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=4, evidence_score=2,
    ),
    CompanyRecord(
        name="Lumen Technologies", slug="lumen-technologies", industry="Telecommunications",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.lumen.com",
        notes="Candidate pool (Step 4). Large telecom/network infrastructure company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=4, evidence_score=2,
    ),

    # --- Logistics / Transportation ----------------------------------------
    CompanyRecord(
        name="United Parcel Service (UPS)", slug="ups", industry="Logistics",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.ups.com",
        notes="Candidate pool (Step 4). Major logistics company with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="FedEx Corporation", slug="fedex", industry="Logistics",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.fedex.com",
        notes="Candidate pool (Step 4). Major logistics company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=6,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Delta Air Lines", slug="delta-air-lines", industry="Transportation",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.delta.com",
        notes="Candidate pool (Step 4). Major airline with a well-known structured internship program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=8, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="United Airlines", slug="united-airlines", industry="Transportation",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.united.com",
        notes="Candidate pool (Step 4). Major airline; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="American Airlines", slug="american-airlines", industry="Transportation",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.aa.com",
        notes="Candidate pool (Step 4). Major airline; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Southwest Airlines", slug="southwest-airlines", industry="Transportation",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.southwest.com",
        notes="Candidate pool (Step 4). Major airline; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="DHL USA", slug="dhl-usa", industry="Logistics",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.dhl.com/us-en",
        notes="Candidate pool (Step 4). Major global logistics company's US arm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Union Pacific Railroad", slug="union-pacific", industry="Transportation",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.up.com",
        notes="Candidate pool (Step 4). Major freight railroad; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Norfolk Southern", slug="norfolk-southern", industry="Transportation",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.norfolksouthern.com",
        notes="Candidate pool (Step 4). Major freight railroad; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="CSX Corporation", slug="csx", industry="Transportation",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.csx.com",
        notes="Candidate pool (Step 4). Major freight railroad; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="J.B. Hunt Transport", slug="jb-hunt", industry="Logistics",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.jbhunt.com",
        notes="Candidate pool (Step 4). Large trucking/logistics company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="XPO, Inc.", slug="xpo", industry="Logistics",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.xpo.com",
        notes="Candidate pool (Step 4). Large trucking/logistics company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=4, internship_volume_score=2,
        function_breadth_score=4, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Real Estate / Professional & Business Services / Other ---------
    CompanyRecord(
        name="CBRE Group", slug="cbre-group", industry="Real Estate",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.cbre.com",
        notes="Candidate pool (Step 4). Largest commercial real-estate services firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Jones Lang LaSalle (JLL)", slug="jll", industry="Real Estate",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.jll.com",
        notes="Candidate pool (Step 4). Large commercial real-estate services firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Cushman & Wakefield", slug="cushman-and-wakefield", industry="Real Estate",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.cushmanwakefield.com",
        notes="Candidate pool (Step 4). Large commercial real-estate services firm; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=8, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Prologis, Inc.", slug="prologis", industry="Real Estate",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.prologis.com",
        notes="Candidate pool (Step 4). Large industrial REIT; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Simon Property Group", slug="simon-property-group", industry="Real Estate",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.simon.com",
        notes="Candidate pool (Step 4). Large retail REIT; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Automatic Data Processing (ADP)", slug="adp", industry="Professional Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.adp.com",
        notes="Candidate pool (Step 4). Large HR/payroll services company with a known structured internship program; Workday estimated by sector analogy (notably, ADP is itself a major HR-tech vendor, which increases confidence somewhat). Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=5,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Paychex, Inc.", slug="paychex", industry="Professional Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.paychex.com",
        notes="Candidate pool (Step 4). Large HR/payroll services company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Gartner, Inc.", slug="gartner", industry="Professional Services",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.gartner.com",
        notes="Candidate pool (Step 4). Large research/advisory firm with a known structured sales/research internship program. Platform uncertain. Not verified this session.",
        business_relevance_score=7, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Nielsen (NielsenIQ)", slug="nielseniq", industry="Professional Services",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://nielseniq.com",
        notes="Candidate pool (Step 4). Large consumer-data/analytics firm. Platform uncertain. Not verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Equifax Inc.", slug="equifax", industry="Professional Services",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.equifax.com",
        notes="Candidate pool (Step 4). Large credit-reporting/data-analytics company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="S&P Global", slug="sp-global", industry="Professional Services",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.spglobal.com",
        notes="Candidate pool (Step 4). Large financial-data/ratings firm with strong Finance-adjacent internship relevance. Platform uncertain. Not verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Moody's Corporation", slug="moodys", industry="Professional Services",
        ats=ATSPlatform.UNKNOWN, tier=CompanyTier.TIER_5, status=CompanyStatus.NEEDS_REVIEW,
        website_url="https://www.moodys.com",
        notes="Candidate pool (Step 4). Large credit-ratings/financial-data firm. Platform uncertain. Not verified this session.",
        business_relevance_score=8, company_reputation_score=7, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=2, evidence_score=2,
    ),
    CompanyRecord(
        name="Archer-Daniels-Midland (ADM)", slug="adm", industry="Agriculture",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.adm.com",
        notes="Candidate pool (Step 4). Large agribusiness company; Workday estimated by analogy to Primient/Saputo (both already confirmed Workday in adjacent food/agriculture sub-sectors). Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Bunge Limited", slug="bunge", industry="Agriculture",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.bunge.com",
        notes="Candidate pool (Step 4). Large agribusiness company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=4, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Corteva, Inc.", slug="corteva", industry="Agriculture",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.corteva.com",
        notes="Candidate pool (Step 4). Large agricultural-science company; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=6, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=5, evidence_score=2,
    ),
    CompanyRecord(
        name="Sherwin-Williams Company", slug="sherwin-williams", industry="Manufacturing",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.sherwin-williams.com",
        notes="Candidate pool (Step 4). Large paints/coatings manufacturer with a well-known structured internship/management-training program; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=7, company_reputation_score=5, internship_volume_score=4,
        function_breadth_score=6, ats_accessibility_score=5, evidence_score=2,
    ),

    # --- Aerospace / Defense ---------------------------------------------
    CompanyRecord(
        name="Lockheed Martin", slug="lockheed-martin", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.lockheedmartin.com",
        notes="Candidate pool (Step 4). Largest US defense contractor with a well-known large structured internship program; Workday estimated by analogy to Boeing/GE Aerospace/Sierra Nevada/Airbus (all already confirmed Workday in this sector). Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=8, internship_volume_score=6,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Northrop Grumman", slug="northrop-grumman", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.northropgrumman.com",
        notes="Candidate pool (Step 4). Major defense contractor; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="RTX Corporation", slug="rtx-corporation", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.rtx.com",
        notes="Candidate pool (Step 4). Major aerospace/defense conglomerate (formerly Raytheon Technologies); Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=7, internship_volume_score=5,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="L3Harris Technologies", slug="l3harris", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.l3harris.com",
        notes="Candidate pool (Step 4). Major defense contractor; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="General Dynamics", slug="general-dynamics", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.gd.com",
        notes="Candidate pool (Step 4). Major defense contractor; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=6, internship_volume_score=4,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
    CompanyRecord(
        name="Textron Inc.", slug="textron", industry="Aerospace",
        ats=ATSPlatform.WORKDAY, tier=CompanyTier.TIER_5, status=CompanyStatus.RESEARCHED,
        website_url="https://www.textron.com",
        notes="Candidate pool (Step 4). Diversified aerospace/defense/industrial conglomerate; Workday estimated by sector analogy. Not independently verified this session.",
        business_relevance_score=5, company_reputation_score=5, internship_volume_score=3,
        function_breadth_score=5, ats_accessibility_score=6, evidence_score=2,
    ),
]


COMPANY_REGISTRY: list[CompanyRecord] = [*_TIER_1, *_TIER_2, *_TIER_3, *_TIER_4, *_TIER_5]


def get_by_status(status: CompanyStatus) -> list[CompanyRecord]:
    return [c for c in COMPANY_REGISTRY if c.status == status]


def get_by_tier(tier: CompanyTier) -> list[CompanyRecord]:
    return [c for c in COMPANY_REGISTRY if c.tier == tier]


def get_by_ats(ats: ATSPlatform) -> list[CompanyRecord]:
    return [c for c in COMPANY_REGISTRY if c.ats == ats]


def get_implemented() -> list[CompanyRecord]:
    return get_by_status(CompanyStatus.IMPLEMENTED)


def top_by_priority(n: int = 50) -> list[CompanyRecord]:
    """Phase 10 Step 4: registry sorted by descending priority_score, for
    the Top-N-by-priority reporting this phase's completion report needs.
    Ties broken by name for determinism."""
    return sorted(COMPANY_REGISTRY, key=lambda c: (-c.priority_score, c.name))[:n]


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
        if c.status == CompanyStatus.IMPLEMENTED and c.tier == CompanyTier.TIER_5:
            raise ValueError(f"{c.slug} is IMPLEMENTED but still tagged TIER_5 (unverified candidate pool)")

        for score_name in (
            "business_relevance_score", "company_reputation_score", "internship_volume_score",
            "function_breadth_score", "ats_accessibility_score", "evidence_score",
        ):
            value = getattr(c, score_name)
            if not (0 <= value <= 10):
                raise ValueError(f"{c.slug}.{score_name}={value} is out of the [0, 10] range")

