from __future__ import annotations

import logging

from scrapers.greenhouse import GreenhouseScraper


class BrazeScraper(GreenhouseScraper):
    """Braze's public Greenhouse job board.

    Selected for Phase 2B because its one current internship - "Business
    Development Representative Intern" - is a business function (sales/
    growth) that doesn't cleanly match any of the platform's fixed
    categories, surfacing a real gap in the category taxonomy rather
    than a parsing bug (see docs/architecture.md).
    """

    board_token = "braze"
    company_slug = "braze"
    company_name = "Braze, Inc."
    career_url = "https://boards.greenhouse.io/braze"
    website_url = "https://www.braze.com"
    industry = "Technology"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = BrazeScraper().run()
    print(run_result.summary())
