from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MarshMcLennanScraper(WorkdayScraper):
    """Marsh McLennan's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "mmc", site "MMC". `workerSubType` facet has
    a clean "Intern (Fixed Term) (Trainee)" value (47 open postings at
    verification time). Real postings directly confirmed via search
    (Accounting Intern, Analytics Solutions Intern, Mercer Marsh
    Benefits Consulting Summer Internship Programme, Career Consulting
    Summer Associate - MBA track) - strong insurance-broking/consulting
    business fit. Global tenant; relies on the existing frontend
    US/Canada display filter.
    """

    base_url = "https://mmc.wd1.myworkdayjobs.com"
    tenant = "mmc"
    site = "MMC"
    intern_facet_id = "840296504fcf01ec4132442dab4aa60e"  # "Intern (Fixed Term) (Trainee)"

    company_slug = "marsh-mclennan"
    company_name = "Marsh McLennan"
    career_url = "https://mmc.wd1.myworkdayjobs.com/MMC"
    website_url = "https://www.marshmclennan.com"
    industry = "Insurance"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MarshMcLennanScraper().run()
    print(run_result.summary())
