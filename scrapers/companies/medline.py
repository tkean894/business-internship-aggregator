from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MedlineScraper(WorkdayScraper):
    """Medline Industries' public Workday job board (Phase 10 Step 3).

    `intern_facet_id` is the `workerSubType` GUID for "Intern (Fixed
    Term) (Trainee)" on this tenant, confirmed live before
    implementation (7 open postings at verification time, including
    strong business-relevant titles: "Product Management Intern",
    "Supply Chain Intern", "Sales Intern", "Business Operations Intern").
    """

    base_url = "https://medline.wd5.myworkdayjobs.com"
    tenant = "medline"
    site = "Medline"
    intern_facet_id = "a71dfaf3f3d31000c6fcb5c805bd0001"

    company_slug = "medline"
    company_name = "Medline Industries"
    career_url = "https://medline.wd5.myworkdayjobs.com/Medline"
    website_url = "https://www.medline.com"
    industry = "Healthcare"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MedlineScraper().run()
    print(run_result.summary())
