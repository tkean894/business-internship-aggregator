from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class BoozAllenScraper(WorkdayScraper):
    """Booz Allen Hamilton's public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "bah", site "BAH_Jobs". `workerSubType`
    facet has a clean "Intern - Paid" value (24 open postings at
    verification time). Board skews government/defense-consulting
    heavy (e.g. "Nuclear Systems Analyst"), but the company's own site
    confirms structured internship programs (Summer Games virtual
    program, in-person "summer hire" program) - business-relevant roles
    (consulting, analytics) filtered by the existing shared classifier
    as usual.
    """

    base_url = "https://bah.wd1.myworkdayjobs.com"
    tenant = "bah"
    site = "BAH_Jobs"
    intern_facet_id = "12aea2bdfbdb10dbf53be9b8e38a2a1d"  # "Intern - Paid"

    company_slug = "booz-allen-hamilton"
    company_name = "Booz Allen Hamilton"
    career_url = "https://bah.wd1.myworkdayjobs.com/BAH_Jobs"
    website_url = "https://www.boozallen.com"
    industry = "Consulting"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = BoozAllenScraper().run()
    print(run_result.summary())
