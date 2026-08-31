from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MondelezScraper(WorkdayScraper):
    """Mondelez International's public Workday job board (Phase 10 Step 7).

    Live-verified: tenant "mdlz", site "External". `workerSubType`
    facet has a clean "Intern (Fixed Term)" value (51 open postings at
    verification time). Real posting directly confirmed via search
    ("Internship Mondelez ... Sales - Category Management & Trade
    Promotion Assistant"). Mondelez runs a branded "Taste The Future"
    US internship program (Sales, Supply Chain, Brand Management -
    strong business fit, ~90-100 interns/year per the company's own
    site). Global tenant; relies on the existing frontend US/Canada
    display filter.
    """

    base_url = "https://mdlz.wd3.myworkdayjobs.com"
    tenant = "mdlz"
    site = "External"
    intern_facet_id = "05fb736b3afb0194b97ef64ab8003784"  # "Intern (Fixed Term)"

    company_slug = "mondelez"
    company_name = "Mondelez International"
    career_url = "https://mdlz.wd3.myworkdayjobs.com/External"
    website_url = "https://www.mondelezinternational.com"
    industry = "Consumer Goods"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MondelezScraper().run()
    print(run_result.summary())
