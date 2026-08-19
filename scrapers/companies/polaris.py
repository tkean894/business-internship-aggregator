from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PolarisScraper(WorkdayScraper):
    """Polaris Inc.'s public Workday job board (Phase 10 Step 3).

    `intern_facet_id` is the `workerSubType` GUID for "Intern/Co-op" on
    this tenant, confirmed live before implementation (4 open postings
    at verification time, including real business-relevant titles like
    "Marketing Internship" and "Finance Internship" alongside
    engineering roles).
    """

    base_url = "https://polaris.wd5.myworkdayjobs.com"
    tenant = "polaris"
    site = "PolarisJobs"
    intern_facet_id = "6236a7dc0277102c2f7cc69ac6a45817"

    company_slug = "polaris-inc"
    company_name = "Polaris Inc."
    career_url = "https://polaris.wd5.myworkdayjobs.com/PolarisJobs"
    website_url = "https://www.polaris.com"
    industry = "Manufacturing"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PolarisScraper().run()
    print(run_result.summary())
