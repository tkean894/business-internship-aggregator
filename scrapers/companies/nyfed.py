from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class NewYorkFedScraper(WorkdayScraper):
    """Federal Reserve Bank of New York's public Workday job board
    (Phase 10 Step 2).

    This tenant's `workerSubType` facet only has "Regular" and
    "Temporary" values - no dedicated Intern/Student facet at all
    (confirmed live before implementation, unlike every other Tier 2
    Workday tenant). Its total board is small (~105 postings), so
    `intern_facet_id`/`search_text` are both left unset: the entire
    board is fetched (a handful of pages, well within `MAX_PAGES`) and
    narrowed purely by the existing client-side `INTERN_TITLE_RE`
    pre-filter, the same mechanism every other tenant already relies on
    as a second-stage filter - here it's just the only stage. At
    verification time zero currently-open postings matched (the "2026
    Summer Intern - Corporate Group - Junior" posting found during
    Phase 10 Step 1 research had since closed) - a legitimate live
    result, not a scraper defect; the standard scraper lifecycle will
    pick up new intern postings automatically whenever they reopen.
    """

    base_url = "https://rb.wd5.myworkdayjobs.com"
    tenant = "rb"
    site = "FRS"

    company_slug = "ny-fed"
    company_name = "Federal Reserve Bank of New York"
    career_url = "https://rb.wd5.myworkdayjobs.com/FRS"
    website_url = "https://www.newyorkfed.org"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = NewYorkFedScraper().run()
    print(run_result.summary())
