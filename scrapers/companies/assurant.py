from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class AssurantScraper(WorkdayScraper):
    """Assurant's public Workday job board. Added in Phase 8 (dataset
    expansion) - Insurance industry."""

    base_url = "https://assurant.wd1.myworkdayjobs.com"
    tenant = "assurant"
    site = "Assurant_Careers"
    intern_facet_id = "48706393987501e4fbdb24f7940b8109"

    company_slug = "assurant"
    company_name = "Assurant, Inc."
    career_url = "https://assurant.wd1.myworkdayjobs.com/Assurant_Careers"
    website_url = "https://www.assurant.com"
    industry = "Insurance"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = AssurantScraper().run()
    print(run_result.summary())
