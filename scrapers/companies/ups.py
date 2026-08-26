from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class UPSScraper(WorkdayScraper):
    """United Parcel Service's public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "hcmportal", site "Search" - an unusual tenant
    name for UPS, confirmed genuine (not guessed) by real UPS-branded
    postings and locations in the response (e.g. "Accounting Intern" at
    "UPS HOUSE", "GLOBAL BUSINESS SERVICES-GBS" location codes).
    `workerSubType` facet has a clean "Intern" value (17 open postings
    at verification time). Global tenant; relies on the existing
    frontend US/Canada display filter, same pattern as Barclays/P&G/J&J.
    """

    base_url = "https://hcmportal.wd5.myworkdayjobs.com"
    tenant = "hcmportal"
    site = "Search"
    intern_facet_id = "30250de825de0108126de4fb848e0000"  # "Intern"

    company_slug = "ups"
    company_name = "United Parcel Service (UPS)"
    career_url = "https://hcmportal.wd5.myworkdayjobs.com/Search"
    website_url = "https://www.ups.com"
    industry = "Logistics"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = UPSScraper().run()
    print(run_result.summary())
