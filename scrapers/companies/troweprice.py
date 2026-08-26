from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class TRowePriceScraper(WorkdayScraper):
    """T. Rowe Price's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "troweprice", site "TRowePrice". No
    `workerSubType` facet exists; `searchText="intern"` returns noisy
    matches (e.g. "Internal Consultant" - a substring match on
    "Internal", not a real filter). Board is small (128 total), well
    under the pagination cap, so it is scanned in full and narrowed by
    the existing client-side title pre-filter alone - the same pattern
    already used for BlackRock/RaceTrac/AB InBev. Real intern postings
    directly confirmed via search (Equity Research Associate Analyst
    Internship, Global Product Internship Program, Client Services
    Internship Program) - strong investment-management business fit.
    """

    base_url = "https://troweprice.wd5.myworkdayjobs.com"
    tenant = "troweprice"
    site = "TRowePrice"

    company_slug = "t-rowe-price"
    company_name = "T. Rowe Price"
    career_url = "https://troweprice.wd5.myworkdayjobs.com/TRowePrice"
    website_url = "https://www.troweprice.com"
    industry = "Investment Management"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = TRowePriceScraper().run()
    print(run_result.summary())
