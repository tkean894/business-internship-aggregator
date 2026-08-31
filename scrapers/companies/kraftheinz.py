from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class KraftHeinzScraper(WorkdayScraper):
    """Kraft Heinz's public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "heinz", site "KraftHeinz_Careers_UR" - the
    dedicated University Recruiting site (distinct from the general
    "KraftHeinz_Careers" site also found during research, deliberately
    not used - targets experienced hires). `workerSubType` facet has a
    clean "Student" value (42 open postings at verification time). Real
    posting directly confirmed via search ("2027 US Internship Program -
    Sales").
    """

    base_url = "https://heinz.wd1.myworkdayjobs.com"
    tenant = "heinz"
    site = "KraftHeinz_Careers_UR"
    intern_facet_id = "177d1fb9ae621014944d7dbd842aef99"  # "Student"

    company_slug = "kraft-heinz"
    company_name = "Kraft Heinz"
    career_url = "https://heinz.wd1.myworkdayjobs.com/KraftHeinz_Careers_UR"
    website_url = "https://www.kraftheinzcompany.com"
    industry = "Consumer Goods"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = KraftHeinzScraper().run()
    print(run_result.summary())
