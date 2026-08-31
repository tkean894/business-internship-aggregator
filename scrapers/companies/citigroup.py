from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class CitigroupScraper(WorkdayScraper):
    """Citigroup's public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "citi", site "2" (an unusual but genuine
    numeric site identifier - real intern postings confirmed directly,
    e.g. a Tokyo "Investment Banking, Part-time Intern" listing).
    `workerSubType` facet has a clean but thin "Intern (Paid)" value
    (7 postings); `searchText="summer analyst"` is both cleaner and far
    more complete (66 results, matching Citi's own branding for its
    internship program - "8-16 week Summer Analyst roles") than the
    facet, so that's used instead. Global tenant; relies on the existing
    frontend US/Canada display filter.
    """

    base_url = "https://citi.wd5.myworkdayjobs.com"
    tenant = "citi"
    site = "2"
    search_text = "summer analyst"

    company_slug = "citigroup"
    company_name = "Citigroup"
    career_url = "https://citi.wd5.myworkdayjobs.com/2"
    website_url = "https://www.citigroup.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = CitigroupScraper().run()
    print(run_result.summary())
