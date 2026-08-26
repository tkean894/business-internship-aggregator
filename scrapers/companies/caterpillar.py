from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class CaterpillarScraper(WorkdayScraper):
    """Caterpillar Inc.'s public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "cat", site "CaterpillarCareers". `workerSubType`
    facet has a clean "Intern - Temporary" value (13 open postings at
    verification time). A separate "Student Worker/Grant Worker" value
    (24 postings) was deliberately excluded - not confirmed to be a real
    internship-equivalent classification, unlike the explicitly-named
    Intern value.
    """

    base_url = "https://cat.wd5.myworkdayjobs.com"
    tenant = "cat"
    site = "CaterpillarCareers"
    intern_facet_id = "3ff971b74e64011c93bf033b6e160342"  # "Intern - Temporary"

    company_slug = "caterpillar"
    company_name = "Caterpillar Inc."
    career_url = "https://cat.wd5.myworkdayjobs.com/CaterpillarCareers"
    website_url = "https://www.caterpillar.com"
    industry = "Manufacturing"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CaterpillarScraper().run()
    print(run_result.summary())
