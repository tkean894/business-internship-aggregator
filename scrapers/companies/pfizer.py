from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class PfizerScraper(WorkdayScraper):
    """Pfizer's public Workday job board (Phase 10 Step 8).

    Live-verified: tenant "pfizer", site "PfizerCareers" (robots.txt
    explicitly `Allow: /PfizerCareers/`). The `workerSubType` facet has
    no clean "Intern" value (only "Regular"/"Fixed Term"/"Temporary"/a
    single "Trainee"), and the whole board (523 postings) is over the
    500-result pagination cap, so `search_text = "intern"` is used
    instead - confirmed to return 231 total results, comfortably within
    `MAX_PAGES`. The raw search also surfaces unrelated "Internal
    Medicine" titles (Workday's own text search, not a substring match),
    but the existing client-side `INTERN_TITLE_RE` word-boundary filter
    already excludes those (`\\bintern\\b` does not match "Internal") -
    confirmed real business-relevant postings remain (e.g. "Pharmacy
    Intern, Medical Affairs", "2027 Internship - Pfizer, Grange Castle").
    """

    base_url = "https://pfizer.wd1.myworkdayjobs.com"
    tenant = "pfizer"
    site = "PfizerCareers"
    search_text = "intern"

    company_slug = "pfizer"
    company_name = "Pfizer Inc."
    career_url = "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers"
    website_url = "https://www.pfizer.com"
    industry = "Healthcare"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = PfizerScraper().run()
    print(run_result.summary())
