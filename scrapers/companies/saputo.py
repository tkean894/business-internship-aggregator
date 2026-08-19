from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class SaputoScraper(WorkdayScraper):
    """Saputo Inc.'s public Workday job board (Phase 10 Step 3).

    This tenant's `workerSubType` facet has no Intern value at all
    (only Regular/Permanent, Temporary variants - confirmed live before
    implementation) despite several real, confirmed internship postings
    on the board (e.g. "Intern, Sales Analyst", "Intern, Finance",
    "Intern, Continuous Improvement", "Intern, Transport and Fleet").
    `intern_facet_id`/`search_text` are both left unset: the entire
    (262-total) board is fetched and narrowed by the existing client-
    side `INTERN_TITLE_RE` pre-filter instead, same pattern as
    `scrapers/companies/racetrac.py`/`abinbev.py`. Saputo is
    headquartered in Montreal, Canada - postings span both the US and
    Canada, which this platform now displays (Phase 10 Step 2 follow-up
    extended the location filter beyond US-only).
    """

    base_url = "https://saputo.wd5.myworkdayjobs.com"
    tenant = "saputo"
    site = "Saputo_External_Careers"

    company_slug = "saputo"
    company_name = "Saputo Inc."
    career_url = "https://saputo.wd5.myworkdayjobs.com/Saputo_External_Careers"
    website_url = "https://www.saputo.com"
    industry = "Food & Beverage"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = SaputoScraper().run()
    print(run_result.summary())
