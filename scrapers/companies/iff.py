from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class IFFScraper(WorkdayScraper):
    """International Flavors & Fragrances' (IFF) public Workday job
    board (Phase 10 Step 3).

    This tenant has no `workerSubType` facet at all (only a functional-
    area `jobFamilyGroup` breakdown - confirmed live before
    implementation). `search_text = "intern"` narrows the 419-total
    board to 291 results, comfortably within the pagination safety cap.
    Confirmed at verification time to include real business-relevant
    postings alongside scientific/technical ones: "HRBP Intern",
    "CF Marketing Intern", "Intern - Sales Support", "Intern - Marketing
    & Digital Experience" - the existing shared classifier filters out
    the technical/scientific majority (Process Engineering, QA, R&D)
    as usual.
    """

    base_url = "https://iff.wd5.myworkdayjobs.com"
    tenant = "iff"
    site = "IFF_Careers"
    search_text = "intern"

    company_slug = "iff"
    company_name = "International Flavors & Fragrances (IFF)"
    career_url = "https://iff.wd5.myworkdayjobs.com/IFF_Careers"
    website_url = "https://www.iff.com"
    industry = "Food & Beverage"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = IFFScraper().run()
    print(run_result.summary())
