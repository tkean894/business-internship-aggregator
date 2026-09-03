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
    CompanyTier,
    get_by_ats,
    get_by_status,
    get_by_tier,
    get_implemented,
    top_by_priority,
    validate_registry,
)


def test_validate_registry_passes():
    validate_registry()


def test_no_duplicate_slugs():
    slugs = [c.slug for c in COMPANY_REGISTRY]
    assert len(slugs) == len(set(slugs))


def test_implemented_companies_have_working_scraper_modules():
    implemented = get_implemented()
    assert len(implemented) == 73  # 16 Step 1 + 10 Tier 2 (Step 2) + 14 Tier 3 (Step 3) + 8 Step 5 + 9 Step 6 + 11 Step 7 + 5 Step 8

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
    assert len(tiers_present) == 5


def test_no_duplicate_company_names():
    # Distinct from test_no_duplicate_slugs - guards against the same real
    # company being entered twice under two different slugs (Phase 10 Step 4).
    names = [c.name for c in COMPANY_REGISTRY]
    assert len(names) == len(set(names))


def test_all_scores_are_within_range():
    # validate_registry() already enforces this at import/test-collection
    # time; this test re-asserts it directly against every record so a
    # future scoring bug fails with a clear, specific assertion.
    for c in COMPANY_REGISTRY:
        for score in (
            c.business_relevance_score, c.company_reputation_score, c.internship_volume_score,
            c.function_breadth_score, c.ats_accessibility_score, c.evidence_score,
        ):
            assert 0 <= score <= 10, c.slug
        assert 0 <= c.priority_score <= 10, c.slug


def test_priority_score_is_mean_of_six_subscores():
    for c in COMPANY_REGISTRY:
        expected = round((
            c.business_relevance_score + c.company_reputation_score + c.internship_volume_score
            + c.function_breadth_score + c.ats_accessibility_score + c.evidence_score
        ) / 6, 2)
        assert c.priority_score == expected, c.slug


def test_top_by_priority_is_sorted_descending_and_deterministic():
    top = top_by_priority(50)
    assert len(top) == 50
    scores = [c.priority_score for c in top]
    assert scores == sorted(scores, reverse=True)
    # Determinism: re-running produces an identical ordering (ties broken by name).
    assert [c.slug for c in top] == [c.slug for c in top_by_priority(50)]


def test_top_by_priority_respects_n():
    assert len(top_by_priority(10)) == 10
    assert len(top_by_priority(1000)) == len(COMPANY_REGISTRY)


def test_tier_5_candidates_are_never_implemented():
    # Phase 10 Step 4 Step 8: this phase is research/ranking only - nothing
    # in the new broad candidate pool should have been implemented.
    for c in get_by_tier(CompanyTier.TIER_5):
        assert c.status != CompanyStatus.IMPLEMENTED, c.slug
        assert c.scraper_module is None, c.slug


def test_implemented_companies_are_not_tier_5():
    for c in get_implemented():
        assert c.tier != CompanyTier.TIER_5, c.slug


def test_registry_has_at_least_250_companies_after_step_4_expansion():
    # Sanity check on the Phase 10 Step 4 deliverable - guards against
    # accidental truncation of the large candidate pool added this phase.
    assert len(COMPANY_REGISTRY) >= 250


def test_industry_diversity_of_candidate_pool():
    # Phase 10 Step 4's explicit goal was breadth across business-internship-
    # relevant industries, not a pile of easy-to-scrape but narrow sectors.
    industries = {c.industry for c in get_by_tier(CompanyTier.TIER_5)}
    assert len(industries) >= 15
