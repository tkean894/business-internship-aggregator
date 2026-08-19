from backend.models import InternshipCategory
from scrapers.classification import classify_internship


def test_valid_business_internship_gets_specific_category():
    assert classify_internship("Finance Intern") == InternshipCategory.FINANCE
    assert classify_internship("Accounting Intern (Fall 2026)") == InternshipCategory.ACCOUNTING
    assert classify_internship("Supply Chain Intern") == InternshipCategory.SUPPLY_CHAIN


def test_technical_internships_are_excluded():
    assert classify_internship("Software Engineer Intern") is None
    assert classify_internship("Research Engineer Intern") is None
    assert classify_internship("Data Scientist Intern") is None
    # Phase 7 additions - aerospace/hardware roles from Rocket Lab/SpaceX.
    assert classify_internship("Avionics Development Intern - Electron") is None
    assert classify_internship("Manufacturing Engineering Intern") is None
    assert classify_internship("Spring 2027 Civil Engineering Internship") is None
    assert classify_internship("RF Test Engineer Intern") is None


def test_non_internship_titles_return_none():
    # "International"/"Internal" must not false-positive on the substring "intern".
    assert classify_internship("International Product Manager") is None
    assert classify_internship("Internal Communications Director") is None
    assert classify_internship("Senior Finance Manager") is None


def test_specific_phrase_outranks_generic_phrase():
    # Real Phase 2 bug: "strategy" (generic) would otherwise beat
    # "market research" (specific) purely due to list order.
    assert classify_internship("Market Research Strategy Intern") == InternshipCategory.BUSINESS_ANALYTICS
    assert classify_internship("Network Strategy Intern") == InternshipCategory.STRATEGY


def test_unmatched_business_internship_falls_back_to_other():
    assert classify_internship("GRC Team Intern") == InternshipCategory.OTHER


def test_sales_category_matches_real_observed_titles():
    assert classify_internship("Business Development Representative Intern") == InternshipCategory.SALES
    assert classify_internship("Commercial Excellence Intern") == InternshipCategory.SALES
    assert classify_internship("Business Development Internship") == InternshipCategory.SALES


def test_sales_keyword_does_not_substring_match_salesforce():
    # Regression test for a real bug found during Phase 7 testing: a
    # plain `"sales" in title.lower()` check matched inside "Salesforce".
    result = classify_internship("Salesforce Administrator Intern")
    assert result != InternshipCategory.SALES
    assert result == InternshipCategory.OTHER  # still a real internship, just uncategorized


def test_learning_and_development_maps_to_human_resources():
    assert classify_internship("Learning & Development Intern") == InternshipCategory.HUMAN_RESOURCES


def test_engineering_intern_exclusion_matches_internship_suffix():
    # "engineering intern" must also match "...Engineering Internship"
    # (the word continues into "-ship"), not just the bare "Intern" form.
    assert classify_internship("Spring 2027 Silicon Engineering Internship/Co-op") is None
    assert classify_internship("Spring 2027 Graduate Engineer Internship/Co-op") is None


def test_business_operations_is_not_excluded_by_engineering_keywords():
    assert classify_internship("Summer 2027 Business Operations Internship/Co-op") == InternshipCategory.OPERATIONS
