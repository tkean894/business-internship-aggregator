from __future__ import annotations

import logging
import time

from scrapers.base_scraper import BaseScraper
from scrapers.classification import INTERN_TITLE_RE, classify_internship
from scrapers.http_utils import REQUEST_TIMEOUT_SECONDS, new_session
from scrapers.schemas import NormalizedInternship
from scrapers.text_utils import clean_html_description, normalize_location, parse_date_safe

logger = logging.getLogger(__name__)

PAGE_SIZE = 20  # Workday's CXS API rejects any larger `limit` (HTTP 400) - confirmed by testing.
MAX_PAGES = 25  # Hard safety cap (500 listings) against an unexpected infinite-pagination bug.
REQUEST_DELAY_SECONDS = 0.3  # Small politeness delay between requests (Step 13 - rate limiting).


class WorkdayScraper(BaseScraper):
    """Shared scraper for any company hosted on Workday (myworkdayjobs.com).

    Workday's own career-site frontend calls a public, unauthenticated
    JSON API (`/wday/cxs/{tenant}/{site}/jobs`) to render its own search
    results - the same mechanism Greenhouse's board API provides, just a
    different ATS and a different JSON shape. Confirmed via each
    tenant's robots.txt (e.g. Abbott's explicitly `Allow: /abbottcareers/`,
    disallowing only `/nonpublic/` and `/refreshFacet/`) that this is
    within the site's own stated access rules - no authentication,
    CAPTCHA, or anti-bot measure is bypassed.

    Unlike Greenhouse (one request returns every job on the board),
    Workday only returns 20 results per page and only a title/location
    summary per job - the full description requires a second request
    per job. To keep total request volume reasonable (Step 13), this
    scraper narrows the *server-side* query to Workday's own
    `workerSubType` facet for "Intern/Student" postings (a GUID that is
    specific to each Workday tenant, found once via that tenant's own
    facet listing and set as `intern_facet_id` in the company config)
    rather than paginating the company's entire job board, and further
    filters by title with the same `INTERN_TITLE_RE` the ATS-agnostic
    classifier uses before paying for a second (detail) request per job.

    A company config only needs to set `base_url`, `tenant`, `site`, and
    `intern_facet_id` plus the usual BaseScraper fields - all fetching,
    pagination, and classification is shared here, mirroring how
    GreenhouseScraper factors out the Greenhouse-specific equivalent.

    Not every Workday tenant exposes a `workerSubType` facet at all, and
    even when one exists its meaning isn't guaranteed - confirmed for
    real during Phase 10 Step 2 (Accenture's tenant reuses the
    `workerSubType` facet *parameter* to carry a "Skills" facet instead
    of job type). Two additional narrowing strategies exist for exactly
    those cases, chosen per company based on what that tenant's board
    actually supports (never guessed):

    - `search_text`: passed as Workday's own `searchText` query field
      (the same mechanism the tenant's own career-site search box uses -
      not a bypass of anything). Only appropriate when the resulting
      result count is small enough to fully paginate within `MAX_PAGES`
      (confirmed per-tenant before use, e.g. Guidehouse's ~361-result
      "intern" query fits; Truist's 846-result and TD's 1516-result
      equivalents do not and were deferred instead of forced).
    - Neither `intern_facet_id` nor `search_text` set: the tenant's
      entire board is fetched with no server-side narrowing at all,
      relying solely on the existing client-side `INTERN_TITLE_RE`
      pre-filter below. Only appropriate for a tenant whose total board
      size is small enough that this is itself bounded and cheap (e.g.
      the Federal Reserve Bank of New York's ~105-job board, CIBC's
      ~7-job board, Piper Sandler's ~43-job board) - never used for a
      large board lacking a facet, which is instead deferred.

    `intern_facet_id` may be a single GUID or a list of GUIDs (Workday
    ORs multiple values within the same facet dimension) - needed when
    a tenant splits interns across more than one `workerSubType` value
    (e.g. PwC's separate "Intern" and "Intern (Trainee)" facets).
    """

    base_url: str  # e.g. "https://abbott.wd5.myworkdayjobs.com"
    tenant: str
    site: str
    intern_facet_id: str | list[str] | None = None
    search_text: str = ""

    def fetch_raw_listings(self) -> list[dict]:
        session = new_session()
        jobs_url = f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}/jobs"

        applied_facets: dict[str, list[str]] = {}
        if self.intern_facet_id:
            facet_ids = (
                [self.intern_facet_id]
                if isinstance(self.intern_facet_id, str)
                else list(self.intern_facet_id)
            )
            applied_facets["workerSubType"] = facet_ids

        summaries: list[dict] = []
        seen_paths: set[str] = set()
        offset = 0
        for _ in range(MAX_PAGES):
            response = session.post(
                jobs_url,
                json={
                    "appliedFacets": applied_facets,
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "searchText": self.search_text,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            postings = response.json().get("jobPostings", [])
            # Workday's own `total` field is unreliable past the first
            # page (confirmed by testing - it silently drops to 0 on
            # subsequent pages while jobPostings still has real data), so
            # pagination stops on an empty/all-seen page instead.
            new_postings = [p for p in postings if p.get("externalPath") not in seen_paths]
            if not new_postings:
                break
            for posting in new_postings:
                seen_paths.add(posting["externalPath"])
            summaries.extend(new_postings)
            offset += PAGE_SIZE
            time.sleep(REQUEST_DELAY_SECONDS)

        # Cheap pre-filter before paying for a detail request per job -
        # not a business-classification decision (that stays in
        # classify_internship/parse_listing), just "is this even
        # titled like an internship" to avoid fetching descriptions for
        # postings that will be discarded anyway.
        candidates = [p for p in summaries if INTERN_TITLE_RE.search(p.get("title", ""))]

        raw_listings: list[dict] = []
        for posting in candidates:
            detail_url = f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}{posting['externalPath']}"
            response = session.get(detail_url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            info = response.json().get("jobPostingInfo", {})
            if info:
                raw_listings.append(info)
            time.sleep(REQUEST_DELAY_SECONDS)

        return raw_listings

    def parse_listing(self, raw: dict) -> NormalizedInternship | None:
        title = raw["title"].strip()

        category = classify_internship(title)
        if category is None:
            return None

        return NormalizedInternship(
            title=title,
            description=clean_html_description(raw.get("jobDescription")),
            category=category,
            location=normalize_location(raw.get("location")),
            application_url=raw["externalUrl"],
            source_url=raw["externalUrl"],
            posted_date=parse_date_safe(raw.get("startDate")),
            application_deadline=None,  # not exposed by Workday's job posting detail endpoint
        )
