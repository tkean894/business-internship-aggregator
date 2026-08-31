from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PrologisScraper(WorkdayScraper):
    """Prologis, Inc.'s public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "prologis", site "Prologis_External_Careers".
    No employment-type facet exists on this tenant; board is small (67
    total), well under the pagination cap, so it is scanned in full and
    narrowed by the existing client-side title pre-filter alone. Real
    intern postings directly confirmed via search ("Intern, Real Estate
    Operations", "Prologis Summer Internship Program", "Intern, Energy",
    "Intern, Capital Deployment/Entitlement") - strong commercial
    real-estate business fit.
    """

    base_url = "https://prologis.wd5.myworkdayjobs.com"
    tenant = "prologis"
    site = "Prologis_External_Careers"

    company_slug = "prologis"
    company_name = "Prologis, Inc."
    career_url = "https://prologis.wd5.myworkdayjobs.com/Prologis_External_Careers"
    website_url = "https://www.prologis.com"
    industry = "Real Estate"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PrologisScraper().run()
    print(run_result.summary())
