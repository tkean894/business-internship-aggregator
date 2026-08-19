from __future__ import annotations

import logging

from scrapers.greenhouse import GreenhouseScraper


class SpaceXScraper(GreenhouseScraper):
    """SpaceX's public Greenhouse job board.

    Added in Phase 7 (company expansion). Contributes real "Business
    Operations Internship/Co-op" and HR ("Recruiting Coordinator, Intern
    Program") postings alongside generic "Engineering Internship/Co-op"
    listings, which the Phase 7 classification exclusions correctly
    filter out as technical roles.
    """

    board_token = "spacex"
    company_slug = "spacex"
    company_name = "Space Exploration Technologies Corp."
    career_url = "https://boards.greenhouse.io/spacex"
    website_url = "https://www.spacex.com"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = SpaceXScraper().run()
    print(run_result.summary())
