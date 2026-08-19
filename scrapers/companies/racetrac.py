from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class RaceTracScraper(WorkdayScraper):
    """RaceTrac Inc.'s public Workday "SSC" (Support Services Center)
    job board (Phase 10 Step 3).

    This tenant's `workerSubType` facet only has a single "Regular"
    value - no dedicated Intern facet (confirmed live before
    implementation). Its total board is small (~51 postings on this
    dedicated corporate-support-office site), so `intern_facet_id`/
    `search_text` are both left unset: the entire board is fetched (a
    few pages) and narrowed by the existing client-side
    `INTERN_TITLE_RE` pre-filter, same pattern as
    `scrapers/companies/nyfed.py`/`cibc.py` from Phase 10 Step 2.
    Confirmed at verification time to include real, diverse business-
    relevant postings: "Human Resources Intern", "Data Science Intern",
    "Retail Accounting Intern", "Pricing and Revenue Intern".
    """

    base_url = "https://racetrac.wd5.myworkdayjobs.com"
    tenant = "racetrac"
    site = "SSC"

    company_slug = "racetrac"
    company_name = "RaceTrac Inc."
    career_url = "https://racetrac.wd5.myworkdayjobs.com/SSC"
    website_url = "https://www.racetrac.com"
    industry = "Retail"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = RaceTracScraper().run()
    print(run_result.summary())
