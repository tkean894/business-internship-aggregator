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
    """

    base_url: str  # e.g. "https://abbott.wd5.myworkdayjobs.com"
    tenant: str
    site: str
    intern_facet_id: str

    def fetch_raw_listings(self) -> list[dict]:
        session = new_session()
        jobs_url = f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}/jobs"

        summaries: list[dict] = []
        seen_paths: set[str] = set()
        offset = 0
        for _ in range(MAX_PAGES):
            response = session.post(
                jobs_url,
                json={
                    "appliedFacets": {"workerSubType": [self.intern_facet_id]},
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "searchText": "",
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
