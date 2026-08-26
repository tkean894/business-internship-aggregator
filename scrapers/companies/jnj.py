from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class JNJScraper(WorkdayScraper):
    """Johnson & Johnson's public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "jj", site "JJ". `workerSubType` facet has two
    genuine student-program values - "Intern (Fixed Term)" (42 open
    postings) and "Co-Op (Fixed Term)" (18 open postings) at verification
    time - both included via the existing multi-facet-id OR support
    (same pattern as PwC's "Intern"/"Intern (Trainee)" split). Strong
    business-function breadth confirmed via `jobFamilyGroup`: Finance
    (136), Marketing (62), Human Resources (34), Strategy & Corporate
    Development (14), Procurement (30), alongside the expected
    life-sciences roles. Global tenant; relies on the existing frontend
    US/Canada display filter, same pattern as Barclays/Disney/P&G.
    """

    base_url = "https://jj.wd5.myworkdayjobs.com"
    tenant = "jj"
    site = "JJ"
    intern_facet_id = [
        "ca32b336cc4a472a863c62c03f6e63b6",  # "Intern (Fixed Term)"
        "c8cdc206cb91013d31d96bb30f801468",  # "Co-Op (Fixed Term)"
    ]

    company_slug = "johnson-and-johnson"
    company_name = "Johnson & Johnson"
    career_url = "https://jj.wd5.myworkdayjobs.com/JJ"
    website_url = "https://www.jnj.com"
    industry = "Healthcare"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = JNJScraper().run()
    print(run_result.summary())
