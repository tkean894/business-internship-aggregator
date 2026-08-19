from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MedtronicScraper(WorkdayScraper):
    """Medtronic's public Workday job board. Added in Phase 8 (dataset
    expansion) - medical device manufacturer, Healthcare industry."""

    base_url = "https://medtronic.wd1.myworkdayjobs.com"
    tenant = "medtronic"
    site = "MedtronicCareers"
    intern_facet_id = "6726e368deda465eb362a1203261d1e5"

    company_slug = "medtronic"
    company_name = "Medtronic plc"
    career_url = "https://medtronic.wd1.myworkdayjobs.com/MedtronicCareers"
    website_url = "https://www.medtronic.com"
    industry = "Healthcare"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MedtronicScraper().run()
    print(run_result.summary())
