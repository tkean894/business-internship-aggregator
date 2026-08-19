from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class BarclaysScraper(WorkdayScraper):
    """Barclays' public Workday job board (Phase 10 Step 2 - Tier 2 expansion).

    `intern_facet_id` is the `workerSubType` GUID for "Intern" on
    Barclays' tenant specifically, confirmed live before implementation
    (14 open Intern-facet postings at verification time, including real
    business-relevant titles like "Quantitative Finance Associate Summer
    Internship Program 2027" and "Banking Analyst Summer Internship
    Program"). Postings span multiple Barclays offices globally (New
    York, Toronto, Singapore, London, etc.) - not filtered by country
    here, matching this project's existing approach (Chevron, AIA, and
    other multinational Tier 1 companies work the same way): scrape
    everything the intern facet returns, let the frontend's USA-location
    display filter and the shared classifier handle relevance.
    """

    base_url = "https://barclays.wd3.myworkdayjobs.com"
    tenant = "barclays"
    site = "External_Career_Site_Barclays"
    intern_facet_id = "6139d325cdcc1001a72ceb63d5d60001"

    company_slug = "barclays"
    company_name = "Barclays"
    career_url = "https://barclays.wd3.myworkdayjobs.com/External_Career_Site_Barclays"
    website_url = "https://www.barclays.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = BarclaysScraper().run()
    print(run_result.summary())
