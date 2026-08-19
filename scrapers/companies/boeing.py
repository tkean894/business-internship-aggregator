from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class BoeingScraper(WorkdayScraper):
    """The Boeing Company's public Workday job board (Phase 10 Step 2).

    Two live site paths were found for this tenant during research
    (`EXTERNAL_CAREERS` and `INTERN`); `EXTERNAL_CAREERS` was confirmed
    live before implementation as the general external career site (739
    total postings) and is the one used here. `intern_facet_id` is the
    `workerSubType` GUID for "Intern - Paid (Seasonal)" (16 open
    postings at verification time, including real business-relevant
    titles like "Business Operations" and "Program Management"
    alongside engineering roles) - deliberately excludes the separate
    "Intern Fixed Term (Non-US)" facet value on this tenant, keeping
    this scraper focused on the US-based program.
    """

    base_url = "https://boeing.wd1.myworkdayjobs.com"
    tenant = "boeing"
    site = "EXTERNAL_CAREERS"
    intern_facet_id = "8b618a30e00f01dbf217e9650c3fc507"

    company_slug = "boeing"
    company_name = "The Boeing Company"
    career_url = "https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS"
    website_url = "https://www.boeing.com"
    industry = "Aerospace"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = BoeingScraper().run()
    print(run_result.summary())
