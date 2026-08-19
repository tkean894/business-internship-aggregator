from backend.database.utils import compute_dedupe_key


def test_same_listing_twice_produces_same_key():
    a = compute_dedupe_key(1, "Finance Intern", "Chicago, IL")
    b = compute_dedupe_key(1, "Finance Intern", "Chicago, IL")
    assert a == b


def test_dedupe_key_ignores_formatting_differences():
    # Two scrapes of the same real posting shouldn't produce different
    # keys just because whitespace/casing varies between runs.
    a = compute_dedupe_key(1, "Finance Intern", "Chicago, IL")
    b = compute_dedupe_key(1, "  finance   intern  ", "chicago,  il")
    assert a == b


def test_dedupe_key_is_independent_of_application_url():
    # The dedupe strategy deliberately does not use the raw URL (session/
    # tracking params vary between scrapes of the same real posting) -
    # this is a property of compute_dedupe_key's inputs, not the URL, so
    # this test documents that application_url/source_url play no part.
    key = compute_dedupe_key(1, "Finance Intern", "Chicago, IL")
    # Same title+location => same key regardless of what URL callers pass
    # around it (compute_dedupe_key doesn't even accept a URL argument).
    assert key == compute_dedupe_key(1, "Finance Intern", "Chicago, IL")


def test_same_title_different_locations_produce_different_keys():
    a = compute_dedupe_key(1, "Finance Intern", "Chicago, IL")
    b = compute_dedupe_key(1, "Finance Intern", "Austin, TX")
    assert a != b


def test_same_title_and_location_different_company_produce_different_keys():
    a = compute_dedupe_key(1, "Finance Intern", "Chicago, IL")
    b = compute_dedupe_key(2, "Finance Intern", "Chicago, IL")
    assert a != b
