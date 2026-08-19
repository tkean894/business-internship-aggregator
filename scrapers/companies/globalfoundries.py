from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class GlobalFoundriesScraper(WorkdayScraper):
    """GlobalFoundries' public Workday job board (Phase 10 Step 3).

    `intern_facet_id` is the `workerSubType` GUID for "Intern (With Pay)
    (Fixed Term) (Trainee)" on this tenant, confirmed live before
    implementation (62 open postings at verification time, including
    real business-relevant titles like "Investor Relations Intern",
    "Finance & Business Operations Intern", "Legal Corporate Affairs
    Intern", and "Strategic Finance and Operations Intern" alongside
    engineering roles). Deliberately excludes the separate, much
    smaller "Intern (Without Pay)" facet value (5 postings) to keep
    this scraper focused on standard paid internships.
    """

    base_url = "https://globalfoundries.wd1.myworkdayjobs.com"
    tenant = "globalfoundries"
    site = "External"
    intern_facet_id = "51f993b53bda010524990ac0ea5d0004"

    company_slug = "globalfoundries"
    company_name = "GlobalFoundries"
    career_url = "https://globalfoundries.wd1.myworkdayjobs.com/External"
    website_url = "https://gf.com"
    industry = "Manufacturing"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = GlobalFoundriesScraper().run()
    print(run_result.summary())
