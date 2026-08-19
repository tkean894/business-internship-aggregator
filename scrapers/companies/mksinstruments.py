from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class MKSInstrumentsScraper(WorkdayScraper):
    """MKS Instruments' public Workday job board (Phase 10 Step 3).

    Uses the `MKSCareersUniversity` site specifically (a separate,
    smaller early-career/university-recruiting site from the general
    `MKSCareersEMEA` site found during research) - confirmed live
    before implementation. `intern_facet_id` is the `workerSubType`
    GUID for "Intern / Co-Op / Student (Fixed Term)" (8 open postings
    at verification time).
    """

    base_url = "https://mksinst.wd1.myworkdayjobs.com"
    tenant = "mksinst"
    site = "MKSCareersUniversity"
    intern_facet_id = "9f854d39924a0175398333d9e3072e69"

    company_slug = "mks-instruments"
    company_name = "MKS Instruments"
    career_url = "https://mksinst.wd1.myworkdayjobs.com/MKSCareersUniversity"
    website_url = "https://www.mks.com"
    industry = "Manufacturing"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = MKSInstrumentsScraper().run()
    print(run_result.summary())
