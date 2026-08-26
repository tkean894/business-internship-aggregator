from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class FidelityScraper(WorkdayScraper):
    """Fidelity Investments' public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "fmr", site "FidelityCareers". No
    `workerSubType` facet exists on this tenant at all (only
    jobFamilyGroup/location/timeType); `searchText="intern"` narrows the
    532-total board to 168, within the pagination safety cap - used as
    the fallback per the existing `search_text` config mechanism.
    """

    base_url = "https://fmr.wd1.myworkdayjobs.com"
    tenant = "fmr"
    site = "FidelityCareers"
    search_text = "intern"

    company_slug = "fidelity-investments"
    company_name = "Fidelity Investments"
    career_url = "https://fmr.wd1.myworkdayjobs.com/FidelityCareers"
    website_url = "https://www.fidelity.com"
    industry = "Investment Management"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = FidelityScraper().run()
    print(run_result.summary())
