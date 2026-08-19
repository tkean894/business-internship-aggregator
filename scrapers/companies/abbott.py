from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class AbbottScraper(WorkdayScraper):
    """Abbott Laboratories' public Workday job board.

    Added in Phase 7 as this platform's first non-Greenhouse ATS
    integration (Step 1). `intern_facet_id` is Workday's internal GUID
    for the "Intern/Student (Fixed Term) (Trainee)" `workerSubType`
    facet on Abbott's board specifically - found once via that board's
    own facet listing (each Workday tenant has its own GUIDs for the
    same conceptual facet, so this isn't reusable across companies,
    only the WorkdayScraper fetch/parse logic is).
    """

    base_url = "https://abbott.wd5.myworkdayjobs.com"
    tenant = "abbott"
    site = "abbottcareers"
    intern_facet_id = "d0663057a84410077d944a83d8896dd3"

    company_slug = "abbott"
    company_name = "Abbott Laboratories"
    career_url = "https://abbott.wd5.myworkdayjobs.com/abbottcareers"
    website_url = "https://www.abbott.com"
    industry = "Healthcare"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = AbbottScraper().run()
    print(run_result.summary())
