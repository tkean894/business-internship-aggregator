from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class NorthernTrustScraper(WorkdayScraper):
    """Northern Trust's public Workday job board (Phase 10 Step 8).

    Live-verified: tenant "ntrs", site "northerntrust" (robots.txt
    explicitly `Allow: /northerntrust/`). `workerSubType` facet has a
    genuine intern value - "Intern (Fixed Term) (Trainee)" (19 open
    postings at verification time), covering Asset Servicing, Asset
    Management, Wealth Management, Corporate Finance, and HR. (A
    separate "ntcampus" site on the same tenant returns the same 19
    postings pre-filtered - this scraper uses the main site + facet, the
    established pattern for every other Workday company here.)
    """

    base_url = "https://ntrs.wd1.myworkdayjobs.com"
    tenant = "ntrs"
    site = "northerntrust"
    intern_facet_id = "333f5ad2433c1000f77c32732b4a0000"  # "Intern (Fixed Term) (Trainee)"

    company_slug = "northern-trust"
    company_name = "Northern Trust Corporation"
    career_url = "https://ntrs.wd1.myworkdayjobs.com/northerntrust"
    website_url = "https://www.northerntrust.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = NorthernTrustScraper().run()
    print(run_result.summary())
