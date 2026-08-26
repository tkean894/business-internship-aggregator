from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class VanguardScraper(WorkdayScraper):
    """The Vanguard Group's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "vanguard", site "vanguard_external". No
    `workerSubType` facet value tags interns (only Regular=435,
    Contractor=13), and `searchText="intern"` is noisy (matches
    "International Tax Specialist", "Senior Internal Auditor" - a
    substring match, not a real filter). Board is 448 total, within the
    500-result pagination safety cap, so it is scanned in full and
    narrowed by the existing client-side title pre-filter alone - the
    same pattern already used for BlackRock. Real intern postings
    directly confirmed via search ("College to Corporate Internship -
    Investment Systems", "College to Corporate IT Internship - Data
    Science").
    """

    base_url = "https://vanguard.wd5.myworkdayjobs.com"
    tenant = "vanguard"
    site = "vanguard_external"

    company_slug = "vanguard"
    company_name = "The Vanguard Group"
    career_url = "https://vanguard.wd5.myworkdayjobs.com/vanguard_external"
    website_url = "https://www.vanguard.com"
    industry = "Investment Management"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = VanguardScraper().run()
    print(run_result.summary())
