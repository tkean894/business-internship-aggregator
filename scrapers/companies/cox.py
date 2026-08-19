from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class CoxEnterprisesScraper(WorkdayScraper):
    """Cox Enterprises' public Workday job board (Phase 10 Step 3).

    This tenant's `workerSubType` facet only has a single "Regular"
    value (681 total) - real intern postings confirmed via search exist
    on this same site but aren't tagged with a dedicated facet value.
    `search_text = "intern"` narrows the board to 111 total results,
    comfortably within the pagination safety cap. Confirmed at
    verification time to include real, diverse business-relevant
    postings: "Analytics Intern", "Talent Acquisition Intern",
    "Corporate Social Responsibility Intern", "Dashboarding & Reporting
    Intern", "Finance & IT Intern".
    """

    base_url = "https://cox.wd1.myworkdayjobs.com"
    tenant = "cox"
    site = "Cox_External_Career_Site_1"
    search_text = "intern"

    company_slug = "cox-enterprises"
    company_name = "Cox Enterprises"
    career_url = "https://cox.wd1.myworkdayjobs.com/Cox_External_Career_Site_1"
    website_url = "https://www.coxenterprises.com"
    industry = "Media & Telecommunications"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CoxEnterprisesScraper().run()
    print(run_result.summary())
