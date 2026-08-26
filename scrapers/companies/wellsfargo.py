from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class WellsFargoScraper(WorkdayScraper):
    """Wells Fargo's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "wf", site "WellsFargoJobs". `workerSubType`
    facet has a clean "Intern (Fixed Term) (Trainee)" value (19 open
    postings at verification time). Real postings directly confirmed
    via search (2027 Summer Internship - Corporate & Investment
    Banking COO, 2026 Finance Internship Program, 2026 Commercial
    Banking Summer Internship) - strong banking business fit.
    """

    base_url = "https://wf.wd1.myworkdayjobs.com"
    tenant = "wf"
    site = "WellsFargoJobs"
    intern_facet_id = "2d264dd4beb00100f05a7d60652a0000"  # "Intern (Fixed Term) (Trainee)"

    company_slug = "wells-fargo"
    company_name = "Wells Fargo"
    career_url = "https://wf.wd1.myworkdayjobs.com/WellsFargoJobs"
    website_url = "https://www.wellsfargo.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = WellsFargoScraper().run()
    print(run_result.summary())
