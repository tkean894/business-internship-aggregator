from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PiperSandlerScraper(WorkdayScraper):
    """Piper Sandler Companies' public Workday job board (Phase 10 Step 2).

    This tenant's `workerSubType` facet only has a single "Regular"
    value - no dedicated Intern facet at all (confirmed live before
    implementation). Its total board is small (~43 postings), so
    `intern_facet_id`/`search_text` are both left unset: the entire
    board is fetched (a few pages) and narrowed by the existing
    client-side `INTERN_TITLE_RE` pre-filter, same as
    `scrapers/companies/nyfed.py`/`cibc.py`. This tenant's investment
    banking internships are titled e.g. "Campus Recruiting - 2026
    Investment Banking Summer Analyst - Restructuring NY" with no
    "intern"/"internship" in the title at all - the "summer analyst"
    synonym added to `INTERN_TITLE_RE` in this same phase (see
    `scrapers/classification.py`) is what makes this tenant classify
    correctly rather than yielding zero results despite real open
    internship postings.
    """

    base_url = "https://pipersandler.wd501.myworkdayjobs.com"
    tenant = "pipersandler"
    site = "Piper_Sandler_Careers"

    company_slug = "piper-sandler"
    company_name = "Piper Sandler Companies"
    career_url = "https://pipersandler.wd501.myworkdayjobs.com/Piper_Sandler_Careers"
    website_url = "https://www.pipersandler.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PiperSandlerScraper().run()
    print(run_result.summary())
