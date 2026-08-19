from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class AnheuserBuschInBevScraper(WorkdayScraper):
    """Anheuser-Busch InBev's public Workday job board (Phase 10 Step 3).

    Uses the `USA` site specifically (this tenant hosts several
    region-specific sites - EUR, MEX, BCBU, etc. - confirmed live
    before implementation) so this scraper only ever sees US postings.
    This tenant's `workerSubType` facet has only 1 posting tagged
    "Intern (Fixed Term) (Trainee)" despite several real, confirmed
    internship/trainee-program postings on the board (e.g. "MBA Intern
    (Summer 2026)", "Global Supply Chain Masters/MBA/PhD Intern") -
    they're evidently tagged some other way on this tenant.
    `intern_facet_id`/`search_text` are both left unset: the entire
    (small, 143-total) `USA` board is fetched and narrowed by the
    existing client-side `INTERN_TITLE_RE` pre-filter instead, same
    pattern as `scrapers/companies/racetrac.py`.
    """

    base_url = "https://abinbev.wd1.myworkdayjobs.com"
    tenant = "abinbev"
    site = "USA"

    company_slug = "ab-inbev"
    company_name = "Anheuser-Busch InBev"
    career_url = "https://abinbev.wd1.myworkdayjobs.com/USA"
    website_url = "https://www.ab-inbev.com"
    industry = "Food & Beverage"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = AnheuserBuschInBevScraper().run()
    print(run_result.summary())
