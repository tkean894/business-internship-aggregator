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
