from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class ICFInternationalScraper(WorkdayScraper):
    """ICF International's public Workday job board (Phase 10 Step 3).

    This tenant has no `workerSubType` facet at all (confirmed live
    before implementation). `search_text = "intern"` narrows the
    378-total board to 132 results, comfortably within the pagination
    safety cap. Confirmed at verification time to include strong
    business-relevant postings: "2026 Summer Intern, Marketing", "2026
    Summer Intern, Business Analyst", "2026 Summer Intern, Energy
    Analyst", "2026 Summer Intern, Program Operations".
    """

    base_url = "https://icf.wd5.myworkdayjobs.com"
    tenant = "icf"
    site = "ICFExternal_Career_Site"
    search_text = "intern"

    company_slug = "icf-international"
    company_name = "ICF International"
    career_url = "https://icf.wd5.myworkdayjobs.com/ICFExternal_Career_Site"
    website_url = "https://www.icf.com"
    industry = "Consulting"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = ICFInternationalScraper().run()
    print(run_result.summary())
