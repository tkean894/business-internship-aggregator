from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class GEAerospaceScraper(WorkdayScraper):
    """GE Aerospace's public Workday job board (Phase 10 Step 2).

    `intern_facet_id` is the `workerSubType` GUID for "Co-op/Intern
    (Fixed Term)" on this tenant, confirmed live before implementation
    (108 open Co-op/Intern-facet postings at verification time). The
    board skews heavily toward engineering internships (as expected for
    an aerospace manufacturer) - the existing shared classifier is
    relied on, unmodified, to keep only the business-relevant subset
    (Finance, Supply Chain, Operations, etc.), matching how every other
    engineering-heavy Tier 1 company (Applied Materials, Rocket Lab,
    SpaceX) already works.
    """

    base_url = "https://geaerospace.wd5.myworkdayjobs.com"
    tenant = "geaerospace"
    site = "GE_ExternalSite"
    intern_facet_id = "74cbdbfadb6e1001457c5daa0b900000"

    company_slug = "ge-aerospace"
    company_name = "GE Aerospace"
    career_url = "https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite"
    website_url = "https://www.geaerospace.com"
    industry = "Aerospace"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = GEAerospaceScraper().run()
    print(run_result.summary())
