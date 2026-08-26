from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class BlackRockScraper(WorkdayScraper):
    """BlackRock's public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "blackrock", site "BlackRock_Professional".
    No `workerSubType` value tags interns specifically (only "Fixed
    Term"=6 and "Regular"=309), and `searchText="intern"` provides no
    real narrowing (200 of 315 total, dominated by unrelated "Associate"
    titles). The board itself is small (315 total), so it is scanned in
    full and narrowed by the existing client-side title pre-filter alone
    - the same pattern already used for RaceTrac/AB InBev/Saputo.
    """

    base_url = "https://blackrock.wd1.myworkdayjobs.com"
    tenant = "blackrock"
    site = "BlackRock_Professional"

    company_slug = "blackrock"
    company_name = "BlackRock, Inc."
    career_url = "https://blackrock.wd1.myworkdayjobs.com/BlackRock_Professional"
    website_url = "https://www.blackrock.com"
    industry = "Investment Management"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = BlackRockScraper().run()
    print(run_result.summary())
