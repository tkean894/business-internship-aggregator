from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class CIBCScraper(WorkdayScraper):
    """CIBC's public Workday "campus" job board (Phase 10 Step 2).

    This tenant's `workerSubType` facet only has "Regular" and
    "Temporary (Fixed Term)" values - no dedicated Intern facet
    (confirmed live before implementation). Its total board is tiny
    (~7 postings on this dedicated campus-recruiting site), so
    `intern_facet_id`/`search_text` are both left unset: the entire
    board is fetched (a single page) and narrowed by the existing
    client-side `INTERN_TITLE_RE` pre-filter, same as
    `scrapers/companies/nyfed.py`. Confirmed at verification time to
    include at least one real internship-labeled posting ("...Winter
    2027 Co-op and Internship Opportunities").
    """

    base_url = "https://cibc.wd3.myworkdayjobs.com"
    tenant = "cibc"
    site = "campus"

    company_slug = "cibc"
    company_name = "CIBC"
    career_url = "https://cibc.wd3.myworkdayjobs.com/campus"
    website_url = "https://www.cibc.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CIBCScraper().run()
    print(run_result.summary())
