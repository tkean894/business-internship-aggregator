from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class GuidehouseScraper(WorkdayScraper):
    """Guidehouse's public Workday job board (Phase 10 Step 2).

    This tenant has no `workerSubType` facet at all (only `jobFamily`,
    a functional-area breakdown with no seniority/employment-type
    dimension - confirmed live before implementation). `search_text =
    "intern"` is used instead: Workday's own `searchText` query field
    (the same mechanism the tenant's own career-site search box uses),
    confirmed to return 361 total results for this tenant - large
    compared to a facet-narrowed tenant, but still comfortably within
    `MAX_PAGES` (25 pages of 20 = 500), so pagination completes fully
    rather than silently truncating. Truist (846 results for the same
    query) and TD Bank (1516) were deferred instead of forced through
    the same fallback for exactly that reason - see their `needs_review`
    entries in `scrapers/company_registry.py`. Confirmed at verification
    time to include real, business-relevant postings (e.g. "Intern -
    Commercial Financial Services Advisory - Campus 2026").
    """

    base_url = "https://guidehouse.wd1.myworkdayjobs.com"
    tenant = "guidehouse"
    site = "External"
    search_text = "intern"

    company_slug = "guidehouse"
    company_name = "Guidehouse"
    career_url = "https://guidehouse.wd1.myworkdayjobs.com/External"
    website_url = "https://guidehouse.com"
    industry = "Consulting"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = GuidehouseScraper().run()
    print(run_result.summary())
