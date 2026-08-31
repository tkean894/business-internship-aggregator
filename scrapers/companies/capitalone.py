from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class CapitalOneScraper(WorkdayScraper):
    """Capital One's public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "capitalone", site "Capital_One" - hosted on
    an unusual pod (wd12, confirmed real; Capital One's own search
    results note a September migration to this URL). `workerSubType`
    facet has a clean "Intern" value (12 open postings at verification
    time). Real postings directly confirmed via search ("Product
    Development Internship Program - Summer 2027", "Analyst Early
    Internship Program - Summer 2027") - strong business fit.
    """

    base_url = "https://capitalone.wd12.myworkdayjobs.com"
    tenant = "capitalone"
    site = "Capital_One"
    intern_facet_id = "a12c70bf789e10572aab83c4780919ad"  # "Intern"

    company_slug = "capital-one"
    company_name = "Capital One"
    career_url = "https://capitalone.wd12.myworkdayjobs.com/Capital_One"
    website_url = "https://www.capitalone.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CapitalOneScraper().run()
    print(run_result.summary())
