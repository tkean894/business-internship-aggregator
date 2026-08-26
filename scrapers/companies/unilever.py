from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class UnileverScraper(WorkdayScraper):
    """Unilever's public Workday job board (Phase 10 Step 6).

    Live-verified: tenant "unilever", site "Unilever_Early_Careers" -
    the dedicated early-careers/internship site, distinct from the
    separate "Unilever_Experienced_Professionals" site also found
    during research (deliberately not used - it targets experienced
    hires, not students). Only 4 postings total at verification time
    (a real, live snapshot - this tenant's internship recruiting is
    clearly seasonal/cyclical) and no `workerSubType` Intern value, so
    the board is scanned in full. Real internship-titled postings
    directly confirmed via search (Unilever Marketing Internship, 2025
    Summer Formulation Internship, YES Programme 12-month Internship)
    even though the live board is thin right now.
    """

    base_url = "https://unilever.wd3.myworkdayjobs.com"
    tenant = "unilever"
    site = "Unilever_Early_Careers"

    company_slug = "unilever"
    company_name = "Unilever"
    career_url = "https://unilever.wd3.myworkdayjobs.com/Unilever_Early_Careers"
    website_url = "https://www.unilever.com"
    industry = "Consumer Goods"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = UnileverScraper().run()
    print(run_result.summary())
