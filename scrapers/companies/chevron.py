from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class ChevronScraper(WorkdayScraper):
    """Chevron's public Workday job board. Added in Phase 8 (dataset
    expansion) - Energy industry."""

    base_url = "https://chevron.wd5.myworkdayjobs.com"
    tenant = "chevron"
    site = "jobs"
    intern_facet_id = "3cd342d9804f01e3bd250104bb00c80e"

    company_slug = "chevron"
    company_name = "Chevron Corporation"
    career_url = "https://chevron.wd5.myworkdayjobs.com/jobs"
    website_url = "https://www.chevron.com"
    industry = "Energy"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = ChevronScraper().run()
    print(run_result.summary())
