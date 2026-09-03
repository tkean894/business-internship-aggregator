from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class DeutscheBankScraper(WorkdayScraper):
    """Deutsche Bank's public Workday job board (Phase 10 Step 8).

    Live-verified: tenant "db", site "DBWebsite" (robots.txt explicitly
    `Allow: /DBWebsite/`). `workerSubType` facet has a genuine intern
    value - "Q (Interns / Practical Work Exp.) (Fixed Term)" (27 open
    postings at verification time). Postings skew international
    (Milan, Sao Paulo, Luxembourg, Shanghai, Beijing); relies on the
    existing frontend US/Canada display filter like other global tenants.
    """

    base_url = "https://db.wd3.myworkdayjobs.com"
    tenant = "db"
    site = "DBWebsite"
    intern_facet_id = "645e861bc53a01f8c083feaefb3a1c09"  # "Q (Interns / Practical Work Exp.) (Fixed Term)"

    company_slug = "deutsche-bank"
    company_name = "Deutsche Bank"
    career_url = "https://db.wd3.myworkdayjobs.com/DBWebsite"
    website_url = "https://www.db.com"
    industry = "Financial Services"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = DeutscheBankScraper().run()
    print(run_result.summary())
