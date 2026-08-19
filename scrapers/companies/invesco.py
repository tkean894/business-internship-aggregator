from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class InvescoScraper(WorkdayScraper):
    """Invesco's public Workday job board. Added in Phase 8 (dataset
    expansion) - global investment management firm; the primary source
    for this platform's new Real Estate category and several Finance
    keyword additions (Investments, Risk)."""

    base_url = "https://invesco.wd1.myworkdayjobs.com"
    tenant = "invesco"
    site = "ivzearlycareers"
    intern_facet_id = "97a56ab3ad0b10186c046d05f3ee0001"

    company_slug = "invesco"
    company_name = "Invesco Ltd."
    career_url = "https://invesco.wd1.myworkdayjobs.com/ivzearlycareers"
    website_url = "https://www.invesco.com"
    industry = "Investment Management"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = InvescoScraper().run()
    print(run_result.summary())
