from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class CocaColaScraper(WorkdayScraper):
    """The Coca-Cola Company's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "coke", site "coca-cola-careers". No
    `workerSubType` facet exists on this tenant; `searchText="intern"`
    narrows the 226-total board to 130, within the pagination safety
    cap, and returns genuinely relevant real titles (e.g. "Coca-Cola
    Ignite Intern - Strategy", "Finance Intern - Graduate") - a clean
    fallback, not a noisy substring match.
    """

    base_url = "https://coke.wd1.myworkdayjobs.com"
    tenant = "coke"
    site = "coca-cola-careers"
    search_text = "intern"

    company_slug = "coca-cola"
    company_name = "The Coca-Cola Company"
    career_url = "https://coke.wd1.myworkdayjobs.com/coca-cola-careers"
    website_url = "https://www.coca-colacompany.com"
    industry = "Consumer Goods"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CocaColaScraper().run()
    print(run_result.summary())
