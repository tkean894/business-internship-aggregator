"""Unit tests for each ATS scraper's parse_listing()/fetch_raw_listings()
logic in isolation, with all external HTTP mocked (Phase 8, Step 24) -
these never depend on a real career site being reachable or unchanged."""

from __future__ import annotations
from datetime import date
from unittest.mock import MagicMock, patch

from backend.models import InternshipCategory
from scrapers.greenhouse import GreenhouseScraper
from scrapers.lever import LeverScraper
from scrapers.workday import WorkdayScraper


class _GHCo(GreenhouseScraper):
    board_token = "testco"
    company_slug = "test-gh-co"
    company_name = "Test GH Co"
    career_url = "https://example.test"


class _WDCo(WorkdayScraper):
    base_url = "https://testco.wd1.myworkdayjobs.com"
    tenant = "testco"
    site = "TestCareers"
    intern_facet_id = "fake-facet-id"
    company_slug = "test-wd-co"
    company_name = "Test WD Co"
    career_url = "https://example.test"


class _LeverCo(LeverScraper):
    site = "testco"
    company_slug = "test-lever-co"
    company_name = "Test Lever Co"
    career_url = "https://example.test"


class _WDCoMultiFacet(WorkdayScraper):
    """Phase 10 Step 2: a tenant needing multiple workerSubType values
    OR'd together (e.g. PwC's separate "Intern" and "Intern (Trainee)")."""

    base_url = "https://testco.wd1.myworkdayjobs.com"
    tenant = "testco"
    site = "TestCareers"
    intern_facet_id = ["facet-a", "facet-b"]
    company_slug = "test-wd-multi-facet-co"
    company_name = "Test WD Multi-Facet Co"
    career_url = "https://example.test"


class _WDCoNoFacet(WorkdayScraper):
    """Phase 10 Step 2: a tenant with no workerSubType facet at all
    (e.g. the Federal Reserve Bank of New York, CIBC, Piper Sandler) -
    the whole (small) board is scanned, relying on the client-side
    INTERN_TITLE_RE pre-filter alone."""

    base_url = "https://testco.wd1.myworkdayjobs.com"
    tenant = "testco"
    site = "TestCareers"
    company_slug = "test-wd-no-facet-co"
    company_name = "Test WD No Facet Co"
    career_url = "https://example.test"


class _WDCoCustomFacetParameter(WorkdayScraper):
    """Phase 10 Step 3: a tenant using a differently-named facet
    dimension for the same "Regular vs. Intern" concept (e.g. Magna
    International's "Worker_Type" instead of "workerSubType")."""

    base_url = "https://testco.wd1.myworkdayjobs.com"
    tenant = "testco"
    site = "TestCareers"
    intern_facet_id = "facet-c"
    facet_parameter = "Worker_Type"
    company_slug = "test-wd-custom-facet-param-co"
    company_name = "Test WD Custom Facet Param Co"
    career_url = "https://example.test"


class _WDCoSearchText(WorkdayScraper):
    """Phase 10 Step 2: a tenant with no workerSubType facet but a
    bounded searchText query (e.g. Guidehouse's search_text="intern")."""

    base_url = "https://testco.wd1.myworkdayjobs.com"
    tenant = "testco"
    site = "TestCareers"
    search_text = "intern"
    company_slug = "test-wd-searchtext-co"
    company_name = "Test WD SearchText Co"
    career_url = "https://example.test"


def test_greenhouse_parse_listing_maps_fields_correctly():
    raw = {
        "title": "Finance Intern",
        "content": "&lt;p&gt;Great role&lt;/p&gt;",
        "absolute_url": "https://job-boards.greenhouse.io/testco/jobs/123",
        "first_published": "2026-08-01T00:00:00Z",
        "application_deadline": None,
        "offices": [{"name": "Chicago, IL"}],
        "location": {"name": "Remote"},
    }
    result = _GHCo().parse_listing(raw)
    assert result is not None
    assert result.title == "Finance Intern"
    assert result.category == InternshipCategory.FINANCE
    assert result.location == "Chicago, IL"  # offices preferred over location
    assert result.description == "Great role"
    assert result.application_url == raw["absolute_url"]
    assert result.posted_date == date(2026, 8, 1)


def test_greenhouse_parse_listing_returns_none_for_technical_role():
    raw = {
        "title": "Software Engineer Intern",
        "content": None,
        "absolute_url": "https://job-boards.greenhouse.io/testco/jobs/456",
        "first_published": None,
        "application_deadline": None,
        "offices": [],
        "location": None,
    }
    assert _GHCo().parse_listing(raw) is None


def test_greenhouse_fetch_raw_listings_handles_empty_board():
    with patch("scrapers.greenhouse.new_session") as mock_session_factory:
        mock_response = MagicMock()
        mock_response.json.return_value = {"jobs": []}
        mock_response.raise_for_status.return_value = None
        mock_session_factory.return_value.get.return_value = mock_response

        result = _GHCo().fetch_raw_listings()
        assert result == []


def test_workday_parse_listing_maps_fields_correctly():
    raw = {
        "title": "Finance Intern (MBA)",
        "jobDescription": "<p>Support FP&amp;A</p>",
        "location": "Austin, TX",
        "externalUrl": "https://testco.wd1.myworkdayjobs.com/TestCareers/job/x/Finance-Intern_R123",
        "startDate": "2026-08-15",
    }
    result = _WDCo().parse_listing(raw)
    assert result is not None
    assert result.title == "Finance Intern (MBA)"
    assert result.category == InternshipCategory.FINANCE
    assert result.location == "Austin, TX"
    assert result.description == "Support FP&A"
    assert result.application_url == raw["externalUrl"]
    assert result.posted_date == date(2026, 8, 15)
    assert result.application_deadline is None  # never exposed by Workday


def test_workday_fetch_raw_listings_stops_on_empty_page():
    with patch("scrapers.workday.new_session") as mock_session_factory:
        session = mock_session_factory.return_value
        empty_response = MagicMock()
        empty_response.json.return_value = {"jobPostings": []}
        empty_response.raise_for_status.return_value = None
        session.post.return_value = empty_response

        result = _WDCo().fetch_raw_listings()
        assert result == []
        session.post.assert_called_once()  # stopped after the first empty page, no detail requests


def test_workday_fetch_raw_listings_skips_malformed_posting_missing_external_path():
    # Regression test for a real bug found during Phase 10 Step 3: one
    # of IFF's real Workday postings was `{"bulletFields": ["R21057"]}`
    # with no "title" or "externalPath" at all, crashing the whole
    # company's scrape with a KeyError. Must be skipped and logged, not
    # fatal - the same per-listing error-isolation principle already
    # applied during parsing, one stage earlier (raw fetch/pagination).
    with patch("scrapers.workday.new_session") as mock_session_factory:
        session = mock_session_factory.return_value
        page_response = MagicMock()
        page_response.json.return_value = {
            "jobPostings": [
                {"bulletFields": ["R21057"]},  # malformed - no title, no externalPath
                {"title": "Finance Intern", "externalPath": "/job/finance-intern_R1"},
            ]
        }
        page_response.raise_for_status.return_value = None

        empty_response = MagicMock()
        empty_response.json.return_value = {"jobPostings": []}
        empty_response.raise_for_status.return_value = None

        session.post.side_effect = [page_response, empty_response]

        detail_response = MagicMock()
        detail_response.json.return_value = {"jobPostingInfo": {"title": "Finance Intern"}}
        detail_response.raise_for_status.return_value = None
        session.get.return_value = detail_response

        result = _WDCo().fetch_raw_listings()
        assert result == [{"title": "Finance Intern"}]  # malformed posting silently excluded, real one kept


def test_workday_multi_facet_id_ors_values_in_one_request():
    with patch("scrapers.workday.new_session") as mock_session_factory:
        session = mock_session_factory.return_value
        empty_response = MagicMock()
        empty_response.json.return_value = {"jobPostings": []}
        empty_response.raise_for_status.return_value = None
        session.post.return_value = empty_response

        result = _WDCoMultiFacet().fetch_raw_listings()
        assert result == []
        _, kwargs = session.post.call_args
        assert kwargs["json"]["appliedFacets"] == {"workerSubType": ["facet-a", "facet-b"]}


def test_workday_custom_facet_parameter_is_used_as_dict_key():
    with patch("scrapers.workday.new_session") as mock_session_factory:
        session = mock_session_factory.return_value
        empty_response = MagicMock()
        empty_response.json.return_value = {"jobPostings": []}
        empty_response.raise_for_status.return_value = None
        session.post.return_value = empty_response

        result = _WDCoCustomFacetParameter().fetch_raw_listings()
        assert result == []
        _, kwargs = session.post.call_args
        assert kwargs["json"]["appliedFacets"] == {"Worker_Type": ["facet-c"]}


def test_workday_no_facet_scans_whole_board_with_empty_search():
    with patch("scrapers.workday.new_session") as mock_session_factory:
        session = mock_session_factory.return_value
        empty_response = MagicMock()
        empty_response.json.return_value = {"jobPostings": []}
        empty_response.raise_for_status.return_value = None
        session.post.return_value = empty_response

        result = _WDCoNoFacet().fetch_raw_listings()
        assert result == []
        _, kwargs = session.post.call_args
        assert kwargs["json"]["appliedFacets"] == {}
        assert kwargs["json"]["searchText"] == ""


def test_workday_search_text_fallback_is_sent_as_search_query():
    with patch("scrapers.workday.new_session") as mock_session_factory:
        session = mock_session_factory.return_value
        empty_response = MagicMock()
        empty_response.json.return_value = {"jobPostings": []}
        empty_response.raise_for_status.return_value = None
        session.post.return_value = empty_response

        result = _WDCoSearchText().fetch_raw_listings()
        assert result == []
        _, kwargs = session.post.call_args
        assert kwargs["json"]["appliedFacets"] == {}
        assert kwargs["json"]["searchText"] == "intern"


def test_lever_parse_listing_maps_fields_correctly():
    raw = {
        "text": "Tax Internship - Summer 2027",
        "description": "<div>Join our tax team</div>",
        "categories": {"location": "Pasadena, CA"},
        "hostedUrl": "https://jobs.lever.co/testco/abc-123",
        "applyUrl": "https://jobs.lever.co/testco/abc-123/apply",
        "createdAt": 1756248007896,  # ms since epoch
    }
    result = _LeverCo().parse_listing(raw)
    assert result is not None
    assert result.title == "Tax Internship - Summer 2027"
    assert result.category == InternshipCategory.ACCOUNTING
    assert result.location == "Pasadena, CA"
    assert result.description == "Join our tax team"
    assert result.application_url == raw["applyUrl"]
    assert result.source_url == raw["hostedUrl"]
    assert result.posted_date is not None


def test_lever_fetch_raw_listings_returns_full_list_in_one_call():
    with patch("scrapers.lever.new_session") as mock_session_factory:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"text": "A Intern"}, {"text": "B Intern"}]
        mock_response.raise_for_status.return_value = None
        mock_session_factory.return_value.get.return_value = mock_response

        result = _LeverCo().fetch_raw_listings()
        assert len(result) == 2


def test_lever_parse_listing_handles_missing_description_gracefully():
    raw = {
        "text": "Audit Internship - Winter 2027",
        "description": None,
        "categories": {},
        "hostedUrl": "https://jobs.lever.co/testco/def-456",
        "applyUrl": None,
        "createdAt": None,
    }
    result = _LeverCo().parse_listing(raw)
    assert result is not None
    assert result.description is None
    assert result.location is None
    assert result.posted_date is None
    assert result.application_url == raw["hostedUrl"]  # falls back to hostedUrl when applyUrl is missing
