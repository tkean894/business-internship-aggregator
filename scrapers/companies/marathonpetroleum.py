from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MarathonPetroleumScraper(WorkdayScraper):
    """Marathon Petroleum Corporation's public Workday job board
    (Phase 10 Step 3).

    `intern_facet_id` is the `workerSubType` GUID for "Intern" on this
    tenant, confirmed live before implementation (17 open postings at
    verification time, including real business-relevant titles like
    "Intern/Co-op - Finance" and "Intern/Co-op - Commercial" alongside
    engineering roles).
    """

    base_url = "https://mpc.wd1.myworkdayjobs.com"
    tenant = "mpc"
    site = "MPCCareers"
    intern_facet_id = "762d3bc5687201008504b33faf520000"

    company_slug = "marathon-petroleum"
    company_name = "Marathon Petroleum Corporation"
    career_url = "https://mpc.wd1.myworkdayjobs.com/MPCCareers"
    website_url = "https://www.marathonpetroleum.com"
    industry = "Energy"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MarathonPetroleumScraper().run()
    print(run_result.summary())
