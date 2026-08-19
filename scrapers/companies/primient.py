from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PrimientScraper(WorkdayScraper):
    """Primient's public Workday job board (Phase 10 Step 3).

    This tenant's `workerSubType` facet has only 1 posting tagged
    "Intern (Fixed Term)" despite several real, confirmed internship
    postings on the board (e.g. "Tax and Treasury Intern", "Digital
    Data and Analytics Intern", "Human Resources Intern", "Food
    Safety/Quality Assurance Intern"). `intern_facet_id`/`search_text`
    are both left unset: the entire (small, 52-total) board is fetched
    and narrowed by the existing client-side `INTERN_TITLE_RE`
    pre-filter instead, same pattern as `scrapers/companies/racetrac.py`.
    """

    base_url = "https://primient.wd1.myworkdayjobs.com"
    tenant = "primient"
    site = "External_Careers"

    company_slug = "primient"
    company_name = "Primient"
    career_url = "https://primient.wd1.myworkdayjobs.com/External_Careers"
    website_url = "https://www.primient.com"
    industry = "Food & Beverage"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PrimientScraper().run()
    print(run_result.summary())
