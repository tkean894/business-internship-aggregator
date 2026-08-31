from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class AllstateScraper(WorkdayScraper):
    """Allstate Corporation's public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "allstate", site "allstate_careers". No
    `workerSubType` value tags interns (only Regular=464, Fixed Term
    Contract=1). Board is 465 total, within the 500-result pagination
    safety cap, so it is scanned in full and narrowed by the existing
    client-side title pre-filter alone - the same pattern already used
    for BlackRock/Vanguard. Real intern postings directly confirmed via
    search ("Data Science Internship", "Machine Learning Engineer
    Intern" - the latter technical and correctly excluded by the
    existing classifier).
    """

    base_url = "https://allstate.wd5.myworkdayjobs.com"
    tenant = "allstate"
    site = "allstate_careers"

    company_slug = "allstate"
    company_name = "Allstate Corporation"
    career_url = "https://allstate.wd5.myworkdayjobs.com/allstate_careers"
    website_url = "https://www.allstate.com"
    industry = "Insurance"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = AllstateScraper().run()
    print(run_result.summary())
