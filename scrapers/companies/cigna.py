from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class CignaScraper(WorkdayScraper):
    """Cigna's public Workday job board (Phase 10 Step 8).

    Live-verified: tenant "cigna", site "cignacareers" (robots.txt
    explicitly `Allow: /cignacareers/`). `workerSubType` facet has a
    genuine intern value - "CoOp / Intern (Seasonal) (Trainee)" (10 open
    postings at verification time), covering real business-function
    programs (Actuarial, Analytics/AI Leadership Development, MBA
    Finance Leadership Development, Legal, Investment Management).
    """

    base_url = "https://cigna.wd5.myworkdayjobs.com"
    tenant = "cigna"
    site = "cignacareers"
    intern_facet_id = "b7947bbbfff2018a3282f98c340c7508"  # "CoOp / Intern (Seasonal) (Trainee)"

    company_slug = "cigna"
    company_name = "The Cigna Group"
    career_url = "https://cigna.wd5.myworkdayjobs.com/cignacareers"
    website_url = "https://www.thecignagroup.com"
    industry = "Healthcare"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CignaScraper().run()
    print(run_result.summary())
