from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class SmuckerScraper(WorkdayScraper):
    """The J.M. Smucker Company's public Workday job board. Added in
    Phase 8 (dataset expansion) - Food & Beverage industry."""

    base_url = "https://smucker.wd5.myworkdayjobs.com"
    tenant = "smucker"
    site = "US_External_Careers"
    intern_facet_id = "900f59dd9b82101e1295ecea2e0d8b34"

    company_slug = "smucker"
    company_name = "The J.M. Smucker Company"
    career_url = "https://smucker.wd5.myworkdayjobs.com/US_External_Careers"
    website_url = "https://www.jmsmucker.com"
    industry = "Food & Beverage"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = SmuckerScraper().run()
    print(run_result.summary())
