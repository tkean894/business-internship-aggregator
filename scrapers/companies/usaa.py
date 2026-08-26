from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class USAAScraper(WorkdayScraper):
    """USAA's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "usaa", site "USAAJOBSWD". No employment-type
    facet value tags interns (only Regular=169). Board is small (169
    total), well under the pagination cap, so it is scanned in full and
    narrowed by the existing client-side title pre-filter alone. USAA
    runs a well-documented structured 10-week summer internship program
    across two recruiting waves (confirmed via usaajobs.com).
    """

    base_url = "https://usaa.wd1.myworkdayjobs.com"
    tenant = "usaa"
    site = "USAAJOBSWD"

    company_slug = "usaa"
    company_name = "USAA"
    career_url = "https://usaa.wd1.myworkdayjobs.com/USAAJOBSWD"
    website_url = "https://www.usaa.com"
    industry = "Insurance"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = USAAScraper().run()
    print(run_result.summary())
