"""Runs every registered company scraper in one pass.

Invoked manually (`python -m scrapers.scheduler`) or on a schedule via
the GitHub Actions workflow (`.github/workflows/scraper.yml`). Each
company scraper is isolated: one company's scraper raising (e.g. its
career site is down or its API shape changed) is logged and skipped,
never crashing the rest of the run or corrupting other companies' data
(each scraper commits within its own `BaseScraper.run()` transaction).
"""

from __future__ import annotations

import logging
import sys

from scrapers.base_scraper import BaseScraper
from scrapers.companies.abbott import AbbottScraper
from scrapers.companies.aia import AIAScraper
from scrapers.companies.appliedmaterials import AppliedMaterialsScraper
from scrapers.companies.assurant import AssurantScraper
from scrapers.companies.braze import BrazeScraper
from scrapers.companies.chevron import ChevronScraper
from scrapers.companies.cloudflare import CloudflareScraper
from scrapers.companies.hcvt import HCVTScraper
from scrapers.companies.invesco import InvescoScraper
from scrapers.companies.medtronic import MedtronicScraper
from scrapers.companies.redventures import RedVenturesScraper
from scrapers.companies.robinhood import RobinhoodScraper
from scrapers.companies.rocketlab import RocketLabScraper
from scrapers.companies.smucker import SmuckerScraper
from scrapers.companies.spacex import SpaceXScraper
from scrapers.companies.spothopper import SpotHopperScraper

logger = logging.getLogger(__name__)

# Add new company scrapers here - nothing else needs to change to pick
# them up in scheduled/manual runs.
SCRAPERS: list[type[BaseScraper]] = [
    # Greenhouse
    RobinhoodScraper,
    CloudflareScraper,
    BrazeScraper,
    RocketLabScraper,
    SpaceXScraper,
    RedVenturesScraper,
    SpotHopperScraper,
    # Workday
    AbbottScraper,
    MedtronicScraper,
    InvescoScraper,
    AIAScraper,
    AppliedMaterialsScraper,
    ChevronScraper,
    SmuckerScraper,
    AssurantScraper,
    # Lever
    HCVTScraper,
]


def run_all() -> bool:
    """Run every registered scraper. Returns False if any scraper failed outright."""
    any_hard_failure = False

    for scraper_cls in SCRAPERS:
        try:
            result = scraper_cls().run()
            logger.info(result.summary())
        except Exception:  # noqa: BLE001 - one company's scraper failing must not stop the others
            any_hard_failure = True
            logger.exception("%s: scraper run failed outright", scraper_cls.__name__)

    return not any_hard_failure


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    succeeded = run_all()
    return 0 if succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
