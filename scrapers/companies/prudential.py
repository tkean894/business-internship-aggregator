from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PrudentialScraper(WorkdayScraper):
    """Prudential Financial's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "pru", site "Careers". No employment-type
    facet exists on this tenant at all (only Skills/location facets);
    `searchText="intern"` is noisy (matches "Integrated Disability
    Claims Examiner"). Board is 147 total, well under the pagination
    cap, so it is scanned in full and narrowed by the existing
    client-side title pre-filter alone. Real intern postings directly
    confirmed via search (2026 Sales Internship Program, 2026 Corporate
    Finance Internship Program, Global Retirement & Insurance
    Leadership Development Internship Program) - strong business fit.
    """

    base_url = "https://pru.wd5.myworkdayjobs.com"
    tenant = "pru"
    site = "Careers"

    company_slug = "prudential-financial"
    company_name = "Prudential Financial"
    career_url = "https://pru.wd5.myworkdayjobs.com/Careers"
    website_url = "https://www.prudential.com"
    industry = "Insurance"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PrudentialScraper().run()
    print(run_result.summary())
