from __future__ import annotations

import logging

from scrapers.greenhouse import GreenhouseScraper


class RobinhoodScraper(GreenhouseScraper):
    """Robinhood's public Greenhouse job board.

    See scrapers/greenhouse.py for why Greenhouse's public API is used
    directly instead of Playwright, and for the shared fetch/parse logic.
    """

    board_token = "robinhood"
    company_slug = "robinhood"
    company_name = "Robinhood Markets, Inc."
    career_url = "https://boards.greenhouse.io/robinhood"
    website_url = "https://robinhood.com"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = RobinhoodScraper().run()
    print(run_result.summary())
