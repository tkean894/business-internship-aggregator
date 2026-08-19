from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MagnaScraper(WorkdayScraper):
    """Magna International's public Workday job board (Phase 10 Step 3).

    This tenant's employment-type facet dimension is named `Worker_Type`
    rather than the usual `workerSubType` (confirmed live by inspecting
    the facet's own `descriptor` field, which read "Job Type" - the same
    concept, just a different parameter name). `intern_facet_id` is the
    `Worker_Type` GUID for "Intern (Fixed Term) (Trainee)" (13 open
    postings at verification time). Board skews engineering/robotics-
    heavy - the existing shared classifier filters to the business-
    relevant subset, same as every other engineering-heavy Tier 1/2
    company (GE Aerospace, Applied Materials).
    """

    base_url = "https://magna.wd3.myworkdayjobs.com"
    tenant = "magna"
    site = "Magna"
    facet_parameter = "Worker_Type"
    intern_facet_id = "5aaaed564f43016878b0b7f1c60258d1"

    company_slug = "magna-international"
    company_name = "Magna International"
    career_url = "https://magna.wd3.myworkdayjobs.com/Magna"
    website_url = "https://www.magna.com"
    industry = "Automotive"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MagnaScraper().run()
    print(run_result.summary())
