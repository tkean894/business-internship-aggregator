"""Runs every registered company scraper in one pass, in parallel.

Invoked manually (`python -m scrapers.scheduler`) or on a schedule via
the GitHub Actions workflow (`.github/workflows/scraper.yml`). Each
company scraper is isolated: one company's scraper raising (e.g. its
career site is down or its API shape changed) is logged and skipped,
never crashing the rest of the run or corrupting other companies' data
(each scraper commits within its own `BaseScraper.run()` transaction).

Parallel by design (Phase 10 Step 5 follow-up): a fully sequential run
of 40 companies measured ~12-13 minutes; adding 8 more pushed a real
run past GitHub Actions' job timeout and it was hard-canceled mid-run.
Rather than keep raising the timeout as the registry grows toward
~200 companies, scrapers run concurrently in a bounded thread pool.
This is safe because `BaseScraper.run()` is fully self-contained per
company - its own `requests.Session` (`scrapers/http_utils.new_session()`
is called fresh inside `fetch_raw_listings()`, never shared across
scrapers) and its own short-lived SQLAlchemy session/transaction
(`backend/database/session.SessionLocal()`, opened and committed/closed
entirely within that one company's `run()`) - so concurrent scrapers
never share mutable state or a DB connection. Different companies also
almost always live on entirely different hosts (different Workday
tenants, different Greenhouse boards), so running them concurrently
does not increase request pressure on any single company's career site
beyond what that one company's own scraper already does by itself.
"""

from __future__ import annotations

import concurrent.futures
import logging
import sys

from scrapers.base_scraper import BaseScraper, ScraperRunResult
from scrapers.companies.abbott import AbbottScraper
from scrapers.companies.abinbev import AnheuserBuschInBevScraper
from scrapers.companies.aia import AIAScraper
from scrapers.companies.airbus import AirbusScraper
from scrapers.companies.allstate import AllstateScraper
from scrapers.companies.appliedmaterials import AppliedMaterialsScraper
from scrapers.companies.assurant import AssurantScraper
from scrapers.companies.barclays import BarclaysScraper
from scrapers.companies.blackrock import BlackRockScraper
from scrapers.companies.boeing import BoeingScraper
from scrapers.companies.boozallen import BoozAllenScraper
from scrapers.companies.braze import BrazeScraper
from scrapers.companies.capitalone import CapitalOneScraper
from scrapers.companies.caterpillar import CaterpillarScraper
from scrapers.companies.chevron import ChevronScraper
from scrapers.companies.cibc import CIBCScraper
from scrapers.companies.citigroup import CitigroupScraper
from scrapers.companies.cloudflare import CloudflareScraper
from scrapers.companies.cocacola import CocaColaScraper
from scrapers.companies.cox import CoxEnterprisesScraper
from scrapers.companies.disney import DisneyScraper
from scrapers.companies.fidelity import FidelityScraper
from scrapers.companies.geaerospace import GEAerospaceScraper
from scrapers.companies.generalmotors import GeneralMotorsScraper
from scrapers.companies.globalfoundries import GlobalFoundriesScraper
from scrapers.companies.guidehouse import GuidehouseScraper
from scrapers.companies.hcvt import HCVTScraper
from scrapers.companies.icf import ICFInternationalScraper
from scrapers.companies.iff import IFFScraper
from scrapers.companies.invesco import InvescoScraper
from scrapers.companies.jll import JLLScraper
from scrapers.companies.jnj import JNJScraper
from scrapers.companies.kraftheinz import KraftHeinzScraper
from scrapers.companies.magna import MagnaScraper
from scrapers.companies.marathonpetroleum import MarathonPetroleumScraper
from scrapers.companies.marshmclennan import MarshMcLennanScraper
from scrapers.companies.medline import MedlineScraper
from scrapers.companies.medtronic import MedtronicScraper
from scrapers.companies.merck import MerckScraper
from scrapers.companies.mksinstruments import MKSInstrumentsScraper
from scrapers.companies.mondelez import MondelezScraper
from scrapers.companies.nyfed import NewYorkFedScraper
from scrapers.companies.pipersandler import PiperSandlerScraper
from scrapers.companies.pnc import PNCScraper
from scrapers.companies.polaris import PolarisScraper
from scrapers.companies.primient import PrimientScraper
from scrapers.companies.procterandgamble import ProcterAndGambleScraper
from scrapers.companies.prologis import PrologisScraper
from scrapers.companies.prudential import PrudentialScraper
from scrapers.companies.pwc import PwCScraper
from scrapers.companies.racetrac import RaceTracScraper
from scrapers.companies.redventures import RedVenturesScraper
from scrapers.companies.robinhood import RobinhoodScraper
from scrapers.companies.rocketlab import RocketLabScraper
from scrapers.companies.saputo import SaputoScraper
from scrapers.companies.simonpropertygroup import SimonPropertyGroupScraper
from scrapers.companies.smucker import SmuckerScraper
from scrapers.companies.spacex import SpaceXScraper
from scrapers.companies.spothopper import SpotHopperScraper
from scrapers.companies.target import TargetScraper
from scrapers.companies.texascapitalbank import TexasCapitalBankScraper
from scrapers.companies.travelers import TravelersScraper
from scrapers.companies.troweprice import TRowePriceScraper
from scrapers.companies.unilever import UnileverScraper
from scrapers.companies.ups import UPSScraper
from scrapers.companies.usaa import USAAScraper
from scrapers.companies.vanguard import VanguardScraper
from scrapers.companies.wellsfargo import WellsFargoScraper

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
    # Workday (Phase 10 Step 2 - Tier 2 expansion)
    BarclaysScraper,
    TexasCapitalBankScraper,
    GEAerospaceScraper,
    BoeingScraper,
    DisneyScraper,
    PwCScraper,
    NewYorkFedScraper,
    CIBCScraper,
    PiperSandlerScraper,
    GuidehouseScraper,
    # Workday (Phase 10 Step 3 - Tier 3 expansion)
    MagnaScraper,
    PolarisScraper,
    GlobalFoundriesScraper,
    MKSInstrumentsScraper,
    RaceTracScraper,
    CoxEnterprisesScraper,
    AnheuserBuschInBevScraper,
    IFFScraper,
    SaputoScraper,
    PrimientScraper,
    MarathonPetroleumScraper,
    MedlineScraper,
    AirbusScraper,
    ICFInternationalScraper,
    # Workday (Phase 10 Step 5 - high-priority company batch)
    ProcterAndGambleScraper,
    JNJScraper,
    TargetScraper,
    JLLScraper,
    BlackRockScraper,
    CaterpillarScraper,
    FidelityScraper,
    UPSScraper,
    # Workday (Phase 10 Step 6 - top business internship employer batch)
    CocaColaScraper,
    TRowePriceScraper,
    MarshMcLennanScraper,
    WellsFargoScraper,
    VanguardScraper,
    PrudentialScraper,
    USAAScraper,
    UnileverScraper,
    PNCScraper,
    # Workday (Phase 10 Step 7 - high-value company batch)
    CitigroupScraper,
    GeneralMotorsScraper,
    AllstateScraper,
    MondelezScraper,
    CapitalOneScraper,
    BoozAllenScraper,
    PrologisScraper,
    SimonPropertyGroupScraper,
    KraftHeinzScraper,
    MerckScraper,
    TravelersScraper,
    # Lever
    HCVTScraper,
]


# Bounded rather than "one thread per scraper": each concurrently-running
# scraper holds at most one DB connection at a time (see backend/database/
# session.py's pool_size/max_overflow, sized to comfortably exceed this),
# and this is deliberately well under what a free-tier Postgres instance
# is expected to tolerate. Raise this only alongside the DB pool size.
MAX_PARALLEL_SCRAPERS = 8


def _run_one(scraper_cls: type[BaseScraper]) -> ScraperRunResult:
    return scraper_cls().run()


def run_all() -> bool:
    """Run every registered scraper, concurrently (bounded by
    MAX_PARALLEL_SCRAPERS). Returns False if any scraper failed outright.
    Blocks until every scraper has finished, same as the old sequential
    version - callers don't need to change."""
    any_hard_failure = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL_SCRAPERS) as executor:
        future_to_cls = {executor.submit(_run_one, scraper_cls): scraper_cls for scraper_cls in SCRAPERS}
        for future in concurrent.futures.as_completed(future_to_cls):
            scraper_cls = future_to_cls[future]
            try:
                result = future.result()
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
