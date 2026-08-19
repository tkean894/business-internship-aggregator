from __future__ import annotations

import logging

from scrapers.greenhouse import GreenhouseScraper


class SpotHopperScraper(GreenhouseScraper):
    """SpotHopper's public Greenhouse job board.

    Added in Phase 7 (company expansion) - a restaurant marketing/ordering
    tech company with a "Business Development Internship" posting, one of
    the real-world examples motivating the new Sales category.
    """

    board_token = "spothopper"
    company_slug = "spothopper"
    company_name = "SpotHopper"
    career_url = "https://boards.greenhouse.io/spothopper"
    website_url = "https://www.spothopper.com"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = SpotHopperScraper().run()
    print(run_result.summary())
