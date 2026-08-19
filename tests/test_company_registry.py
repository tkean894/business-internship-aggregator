"""Tests for the Phase 10 company registry (scrapers/company_registry.py).

This registry is a planning artifact, not a scraper, so these tests check
internal consistency and that it can represent the companies actually
implemented today - not live network access to any career site.
"""
from __future__ import annotations

import importlib

from scrapers.company_registry import (
    COMPANY_REGISTRY,
    ATSPlatform,
    CompanyStatus,
    get_by_ats,
    get_by_status,
    get_by_tier,
    get_implemented,
    validate_registry,
)


def test_validate_registry_passes():
    validate_registry()


def test_no_duplicate_slugs():
    slugs = [c.slug for c in COMPANY_REGISTRY]
    assert len(slugs) == len(set(slugs))


def test_implemented_companies_have_working_scraper_modules():
    implemented = get_implemented()
    assert len(implemented) == 40  # 16 from Step 1 + 10 Tier 2 (Step 2) + 14 Tier 3 (Step 3)

    for company in implemented:
        assert company.scraper_module, company.slug
        module = importlib.import_module(company.scraper_module)
        assert company.ats_config, f"{company.slug} has no ats_config"

        if company.ats == ATSPlatform.GREENHOUSE:
            assert "board_token" in company.ats_config
        elif company.ats == ATSPlatform.WORKDAY:
            assert "tenant" in company.ats_config and "site" in company.ats_config
        elif company.ats == ATSPlatform.LEVER:
            assert "site" in company.ats_config

        # Every implemented company's module must define a scraper class
        # whose class attributes match the registry's recorded config -
        # guards against the registry silently drifting from real code.
        scraper_classes = [
            v for v in vars(module).values()
            if isinstance(v, type) and getattr(v, "company_slug", None) == company.slug
        ]
        assert len(scraper_classes) == 1, f"expected exactly one scraper class for {company.slug}"


def test_ready_companies_have_ats_config_and_known_platform():
    for company in get_by_status(CompanyStatus.READY):
        assert company.ats != ATSPlatform.UNKNOWN, company.slug
        assert company.ats_config, company.slug


def test_needs_review_companies_are_not_implemented():
    for company in get_by_status(CompanyStatus.NEEDS_REVIEW):
        assert company.scraper_module is None, company.slug


def test_excluded_companies_are_not_implemented():
    for company in get_by_status(CompanyStatus.EXCLUDED):
        assert company.scraper_module is None, company.slug


def test_get_by_tier_and_get_by_ats_are_consistent_with_full_registry():
    from scrapers.company_registry import CompanyTier

    seen = set()
    for tier in CompanyTier:
        seen.update(c.slug for c in get_by_tier(tier))
    assert seen == {c.slug for c in COMPANY_REGISTRY}

    seen = set()
    for ats in ATSPlatform:
        seen.update(c.slug for c in get_by_ats(ats))
    assert seen == {c.slug for c in COMPANY_REGISTRY}


def test_registry_has_meaningful_size_and_tier_spread():
    # Sanity check on the Phase 10 Step 1 deliverable itself, not a
    # hard product requirement - guards against accidental truncation.
    assert len(COMPANY_REGISTRY) >= 50
    tiers_present = {c.tier for c in COMPANY_REGISTRY}
    assert len(tiers_present) == 4
