from __future__ import annotations

import logging

from scrapers.greenhouse import GreenhouseScraper


class CloudflareScraper(GreenhouseScraper):
    """Cloudflare's public Greenhouse job board.

    Selected for Phase 2B because its Fall 2026 internship postings span
    Accounting, Marketing, and Strategy, plus a "GRC Team Intern" role
    that doesn't fit any fixed category (a useful real test of the OTHER
    fallback) and several "Research Engineer"/"Software Engineer" intern
    postings that must be excluded as technical roles.
    """

    board_token = "cloudflare"
    company_slug = "cloudflare"
    company_name = "Cloudflare, Inc."
    career_url = "https://boards.greenhouse.io/cloudflare"
    website_url = "https://www.cloudflare.com"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CloudflareScraper().run()
    print(run_result.summary())
