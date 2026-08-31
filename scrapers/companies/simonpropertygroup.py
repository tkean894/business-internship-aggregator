from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class SimonPropertyGroupScraper(WorkdayScraper):
    """Simon Property Group's public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "simon", site "Simon". No `workerSubType`
    Intern value (Regular=165, Temporary=7); board is small (172
    total), well under the pagination cap, so it is scanned in full and
    narrowed by the existing client-side title pre-filter alone. Real
    internship program confirmed via the company's own site: Leasing,
    Finance, Accounting, Marketing, IT, Legal, Design, and HR tracks -
    strong retail-real-estate business fit.
    """

    base_url = "https://simon.wd1.myworkdayjobs.com"
    tenant = "simon"
    site = "Simon"

    company_slug = "simon-property-group"
    company_name = "Simon Property Group"
    career_url = "https://simon.wd1.myworkdayjobs.com/Simon"
    website_url = "https://www.simon.com"
    industry = "Real Estate"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = SimonPropertyGroupScraper().run()
    print(run_result.summary())
