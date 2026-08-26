from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class JLLScraper(WorkdayScraper):
    """Jones Lang LaSalle's public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "jll", site "jllcareers". `workerSubType`
    facet has a clean "Intern (Fixed Term) (Trainee)" value (70 open
    postings at verification time). Real postings directly confirmed via
    search (Capital Markets Summer Internship, Accountant Intern) - a
    strong commercial-real-estate business-function fit. Global tenant;
    relies on the existing frontend US/Canada display filter, same
    pattern as Barclays/Disney/P&G/J&J.
    """

    base_url = "https://jll.wd1.myworkdayjobs.com"
    tenant = "jll"
    site = "jllcareers"
    intern_facet_id = "83c7fa911b4101a0f63c22b2db507809"  # "Intern (Fixed Term) (Trainee)"

    company_slug = "jll"
    company_name = "Jones Lang LaSalle (JLL)"
    career_url = "https://jll.wd1.myworkdayjobs.com/jllcareers"
    website_url = "https://www.jll.com"
    industry = "Real Estate"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = JLLScraper().run()
    print(run_result.summary())
