from __future__ import annotations

import logging

from scrapers.greenhouse import GreenhouseScraper


class RedVenturesScraper(GreenhouseScraper):
    """Red Ventures' public Greenhouse job board.

    Added in Phase 7 (company expansion) - a digital marketing/e-commerce
    company with a "Business Analyst Internship" talent-pipeline posting.
    """

    board_token = "redventures"
    company_slug = "redventures"
    company_name = "Red Ventures"
    career_url = "https://boards.greenhouse.io/redventures"
    website_url = "https://www.redventures.com"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = RedVenturesScraper().run()
    print(run_result.summary())
