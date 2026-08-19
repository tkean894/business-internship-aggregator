from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PwCScraper(WorkdayScraper):
    """PwC's public Workday job board (Phase 10 Step 2).

    Two live site paths were found for this tenant during research;
    `US_Entry_Level_Careers` returned zero total postings when verified
    (an empty/misconfigured site path, not a real career site right
    now) while `Global_Campus_Careers` returned 1519 total postings, so
    the latter is used here. `intern_facet_id` is a list of two
    `workerSubType` GUIDs on this tenant - "Intern" (72 open postings)
    and "Intern (Trainee)" (410 open postings) at verification time -
    both are genuine internship classifications on this board (PwC
    distinguishes standard summer interns from a separate
    intern/trainee track); `WorkdayScraper.fetch_raw_listings` ORs
    multiple facet values within the same dimension, so both are
    included without any per-company parsing logic.
    """

    base_url = "https://pwc.wd3.myworkdayjobs.com"
    tenant = "pwc"
    site = "Global_Campus_Careers"
    intern_facet_id = [
        "e57e6863118d01e8c8ee4356e52a5e2d",  # "Intern"
        "e57e6863118d01ccc3941a45322bfba2",  # "Intern (Trainee)"
    ]

    company_slug = "pwc"
    company_name = "PwC (PricewaterhouseCoopers)"
    career_url = "https://pwc.wd3.myworkdayjobs.com/Global_Campus_Careers"
    website_url = "https://www.pwc.com"
    industry = "Consulting"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PwCScraper().run()
    print(run_result.summary())
