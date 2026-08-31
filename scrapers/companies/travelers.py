from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class TravelersScraper(WorkdayScraper):
    """The Travelers Companies' public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "travelers", site "External". `workerSubType`
    facet only tags 1 posting as "Intern Program (Fixed Term)" despite
    real, confirmed internship postings appearing directly in the raw
    (unfiltered) results (e.g. "Actuarial Leadership Development
    Program (ALDP) Intern", "Business Insurance Underwriting Program
    Internship", "Summer Intern - Specialty Insurance") - the facet
    clearly undercounts real interns, the same pattern already seen at
    AB InBev/Saputo/Primient. Board is small enough (354 total, under
    the pagination cap) to scan in full instead, relying on the
    existing client-side title pre-filter to catch every real posting
    regardless of how this tenant tags employment type.
    """

    base_url = "https://travelers.wd5.myworkdayjobs.com"
    tenant = "travelers"
    site = "External"

    company_slug = "travelers"
    company_name = "The Travelers Companies"
    career_url = "https://travelers.wd5.myworkdayjobs.com/External"
    website_url = "https://www.travelers.com"
    industry = "Insurance"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = TravelersScraper().run()
    print(run_result.summary())
