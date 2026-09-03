from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class BlackstoneScraper(WorkdayScraper):
    """Blackstone's public Workday campus-recruiting job board (Phase 10 Step 8).

    Live-verified: tenant "blackstone", site "Blackstone_Campus_Careers"
    (robots.txt explicitly `Allow: /Blackstone_Campus_Careers/`) - a
    separate, smaller board from the general "Blackstone_Careers" site,
    dedicated to campus/internship recruiting (28 open postings total at
    verification time, small enough to fetch whole-board with no facet
    needed, same pattern as CIBC/Piper Sandler). Covers Private Equity,
    Credit & Insurance, Real Estate, Private Wealth, and Finance/Internal
    Audit internship tracks; a few technical postings (Data Engineer,
    Software Engineer, Cybersecurity Summer Analyst) are present too and
    correctly excluded by the existing technical-exclusion keywords.
    """

    base_url = "https://blackstone.wd1.myworkdayjobs.com"
    tenant = "blackstone"
    site = "Blackstone_Campus_Careers"

    company_slug = "blackstone"
    company_name = "Blackstone Inc."
    career_url = "https://blackstone.wd1.myworkdayjobs.com/Blackstone_Campus_Careers"
    website_url = "https://www.blackstone.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = BlackstoneScraper().run()
    print(run_result.summary())
