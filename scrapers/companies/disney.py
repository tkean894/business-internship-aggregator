from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class DisneyScraper(WorkdayScraper):
    """The Walt Disney Company's public Workday job board (Phase 10 Step 2).

    `intern_facet_id` is the `workerSubType` GUID for "Student Program /
    Intern (Fixed Term)" on this tenant, confirmed live before
    implementation (11 open postings at verification time). At
    verification time this facet's open postings skewed toward
    EMEA/German "Werkstudent" and regional student programs rather than
    the US corporate internships (e.g. Accounting & Finance Rotation
    Program) surfaced by web search earlier in Phase 10 Step 1 research
    - that specific posting had since rotated off the live board by
    verification time (postings churn; it is not evidence the facet is
    wrong). This is the same pattern already handled elsewhere in this
    project (Barclays, Chevron): scrape everything the correctly-named
    intern facet returns, and let the existing frontend USA-location
    display filter and shared classifier - both already relied on for
    every multinational company - determine what's actually shown.
    """

    base_url = "https://disney.wd5.myworkdayjobs.com"
    tenant = "disney"
    site = "disneycareer"
    intern_facet_id = "4f84d9e8a0970100aec0ae70150e0000"

    company_slug = "disney"
    company_name = "The Walt Disney Company"
    career_url = "https://disney.wd5.myworkdayjobs.com/disneycareer"
    website_url = "https://www.thewaltdisneycompany.com"
    industry = "Media & Entertainment"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = DisneyScraper().run()
    print(run_result.summary())
