from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class AppliedMaterialsScraper(WorkdayScraper):
    """Applied Materials' public Workday job board. Added in Phase 8
    (dataset expansion) - semiconductor equipment manufacturer,
    Manufacturing industry."""

    base_url = "https://amat.wd1.myworkdayjobs.com"
    tenant = "amat"
    site = "External"
    intern_facet_id = "ba9df317f7ac456da2faff4fd6a521c8"

    company_slug = "applied-materials"
    company_name = "Applied Materials, Inc."
    career_url = "https://amat.wd1.myworkdayjobs.com/External"
    website_url = "https://www.appliedmaterials.com"
    industry = "Manufacturing"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = AppliedMaterialsScraper().run()
    print(run_result.summary())
