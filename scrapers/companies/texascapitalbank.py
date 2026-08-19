from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class TexasCapitalBankScraper(WorkdayScraper):
    """Texas Capital Bank's public Workday job board (Phase 10 Step 2).

    `intern_facet_id` is the `workerSubType` GUID for "Intern (Fixed
    Term) (Trainee)" on this tenant, confirmed live before
    implementation (1 open Intern-facet posting at verification time -
    "2027 Summer Analyst (Internship)" - a real, correctly-labeled
    posting; a small regional bank naturally has a smaller board than a
    Truist or a Barclays, and this project doesn't require a minimum
    posting count to add a company, only a legitimate public data
    source and correct parsing).
    """

    base_url = "https://texascapitalbank.wd12.myworkdayjobs.com"
    tenant = "texascapitalbank"
    site = "College_Career"
    intern_facet_id = "a2a9056096f710012bf10d7b8a530000"

    company_slug = "texas-capital-bank"
    company_name = "Texas Capital Bank"
    career_url = "https://texascapitalbank.wd12.myworkdayjobs.com/College_Career"
    website_url = "https://www.texascapitalbank.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = TexasCapitalBankScraper().run()
    print(run_result.summary())
