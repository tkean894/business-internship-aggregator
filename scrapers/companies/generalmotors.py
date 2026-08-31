from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class GeneralMotorsScraper(WorkdayScraper):
    """General Motors' public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "generalmotors", site "Careers_GM".
    `workerSubType` facet has two genuine student-program values -
    "Intern (Fixed Term) (Trainee)" (14 open postings) and "Co-Op
    (Fixed Term)" (5 open postings) at verification time - both included
    via the existing multi-facet-id OR support (same pattern as PwC/J&J).
    """

    base_url = "https://generalmotors.wd5.myworkdayjobs.com"
    tenant = "generalmotors"
    site = "Careers_GM"
    intern_facet_id = [
        "81219c91208501e94c213185a61a320a",  # "Intern (Fixed Term) (Trainee)"
        "81219c91208501ec00823185a61a360a",  # "Co-Op (Fixed Term)"
    ]

    company_slug = "general-motors"
    company_name = "General Motors"
    career_url = "https://generalmotors.wd5.myworkdayjobs.com/Careers_GM"
    website_url = "https://www.gm.com"
    industry = "Automotive"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = GeneralMotorsScraper().run()
    print(run_result.summary())
