from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PNCScraper(WorkdayScraper):
    """PNC Financial Services' public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "pnc", site "External". `workerSubType`
    facet has a clean "Intern (Seasonal) (Trainee)" value (24 open
    postings at verification time, out of a 2000-display-capped total
    board). Real posting directly confirmed via search ("Asset
    Management Group Undergraduate Intern") - strong banking business
    fit.
    """

    base_url = "https://pnc.wd5.myworkdayjobs.com"
    tenant = "pnc"
    site = "External"
    intern_facet_id = "212fee894bd90147f848029e0a07d40c"  # "Intern (Seasonal) (Trainee)"

    company_slug = "pnc-financial"
    company_name = "The PNC Financial Services Group"
    career_url = "https://pnc.wd5.myworkdayjobs.com/External"
    website_url = "https://www.pnc.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PNCScraper().run()
    print(run_result.summary())
