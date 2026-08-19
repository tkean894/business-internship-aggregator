from __future__ import annotations

import logging

from scrapers.lever import LeverScraper


class HCVTScraper(LeverScraper):
    """HCVT's public Lever job board. Added in Phase 8 as the platform's
    first Lever-hosted company - a tax/accounting/advisory firm whose
    Audit/Tax/M&A Advisory internships also motivated adding "tax" as an
    Accounting keyword (see scrapers/classification.py)."""

    site = "hcvt"
    company_slug = "hcvt"
    company_name = "HCVT LLP"
    career_url = "https://jobs.lever.co/hcvt"
    website_url = "https://www.hcvt.com"
    industry = "Consulting"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = HCVTScraper().run()
    print(run_result.summary())
