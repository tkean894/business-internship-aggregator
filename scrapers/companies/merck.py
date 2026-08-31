from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MerckScraper(WorkdayScraper):
    """Merck & Co.'s public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "msd" (Merck's international/pharma entity
    name, "Merck Sharp & Dohme" - confirmed genuine via real postings,
    not guessed), site "SearchJobs". `workerSubType` facet has two
    genuine student-program values - "Intern/Co-op (Fixed Term)" (42
    open postings) and "Intern/Co-Op" (1 open posting) at verification
    time - both included via the existing multi-facet-id OR support.
    Global tenant; relies on the existing frontend US/Canada display
    filter.
    """

    base_url = "https://msd.wd5.myworkdayjobs.com"
    tenant = "msd"
    site = "SearchJobs"
    intern_facet_id = [
        "778f59ec4f0a0198986b520b021105b1",  # "Intern/Co-op (Fixed Term)"
        "778f59ec4f0a017df770c73a021144b1",  # "Intern/Co-Op"
    ]

    company_slug = "merck"
    company_name = "Merck & Co."
    career_url = "https://msd.wd5.myworkdayjobs.com/SearchJobs"
    website_url = "https://www.merck.com"
    industry = "Healthcare"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MerckScraper().run()
    print(run_result.summary())
