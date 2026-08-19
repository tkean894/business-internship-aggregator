from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class AirbusScraper(WorkdayScraper):
    """Airbus' public Workday job board (Phase 10 Step 3).

    This is Airbus's single global Workday tenant, covering every
    Airbus legal entity worldwide (confirmed via its `hiringCompany`
    facet, which lists dozens of entities including "Airbus Americas,
    Inc." and "Airbus Canada Limited Partnership" alongside many
    European/Asian ones) - there is no way to narrow to just the US
    Mobile, AL site via a single facet without missing real US postings
    (a combined workerSubType+hiringCompany query for "Airbus Americas"
    specifically returned only 2 results, far fewer than the US
    postings independently confirmed via direct search - e.g. "Summer
    Internship - Operations" and "Summer Internship - Project Data
    Analyst" in Mobile, AL). `intern_facet_id` is the `workerSubType`
    GUID for "Trainee / Student (Fixed Term)" (124 open postings
    worldwide at verification time). Scrapes globally and relies on the
    existing frontend US/Canada display filter to surface only the
    relevant subset, the same pattern already used for other
    multinational companies (Barclays, Disney) rather than adding a new
    multi-dimension-facet capability for uncertain benefit.
    """

    base_url = "https://ag.wd3.myworkdayjobs.com"
    tenant = "ag"
    site = "Airbus"
    intern_facet_id = "f5811cef9cb50193723ed01d470a6e15"

    company_slug = "airbus"
    company_name = "Airbus"
    career_url = "https://ag.wd3.myworkdayjobs.com/Airbus"
    website_url = "https://www.airbus.com"
    industry = "Aerospace"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = AirbusScraper().run()
    print(run_result.summary())
