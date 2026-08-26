from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class TargetScraper(WorkdayScraper):
    """Target Corporation's public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "target", site "targetcareers". `workerSubType`
    facet has a clean "Intern" value (104 open postings at verification
    time, out of a 2000-display-capped total board). US retailer, so no
    global-scope caveat needed here.
    """

    base_url = "https://target.wd5.myworkdayjobs.com"
    tenant = "target"
    site = "targetcareers"
    intern_facet_id = "daccab9f1d25019dc0cd608d3157bd05"  # "Intern"

    company_slug = "target"
    company_name = "Target Corporation"
    career_url = "https://target.wd5.myworkdayjobs.com/targetcareers"
    website_url = "https://corporate.target.com"
    industry = "Retail"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = TargetScraper().run()
    print(run_result.summary())
