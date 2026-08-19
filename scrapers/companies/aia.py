from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class AIAScraper(WorkdayScraper):
    """AIA Group's public Workday job board. Added in Phase 8 (dataset
    expansion) - pan-Asian life insurance group, Insurance industry."""

    base_url = "https://aia.wd3.myworkdayjobs.com"
    tenant = "aia"
    site = "External"
    intern_facet_id = "bd3d6b20175f01ed58af1567352c2c0d"

    company_slug = "aia"
    company_name = "AIA Group Limited"
    career_url = "https://aia.wd3.myworkdayjobs.com/External"
    website_url = "https://www.aia.com"
    industry = "Insurance"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = AIAScraper().run()
    print(run_result.summary())
