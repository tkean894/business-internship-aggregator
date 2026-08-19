from __future__ import annotations

import logging

from scrapers.greenhouse import GreenhouseScraper


class RocketLabScraper(GreenhouseScraper):
    """Rocket Lab's public Greenhouse job board.

    Added in Phase 7 (company expansion). Real business-function
    internships exist alongside a large volume of aerospace-hardware
    engineering internships (Avionics, Manufacturing Engineering, etc.)
    - the latter drove several EXCLUDE_KEYWORDS additions in
    scrapers/classification.py so they're correctly excluded rather
    than falling into OTHER as if unclassified business roles.
    """

    board_token = "rocketlab"
    company_slug = "rocketlab"
    company_name = "Rocket Lab USA, Inc."
    career_url = "https://boards.greenhouse.io/rocketlab"
    website_url = "https://www.rocketlabusa.com"
    industry = "Aerospace"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = RocketLabScraper().run()
    print(run_result.summary())
