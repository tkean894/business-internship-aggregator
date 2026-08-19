from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

REQUEST_TIMEOUT_SECONDS = 30
REQUEST_HEADERS = {"User-Agent": "BusinessInternshipAggregator/0.1 (educational project)"}

# Conservative retry policy for transient failures only: connection
# errors, timeouts, HTTP 429 (rate limited), and temporary 5xx. A plain
# 404 or other 4xx is a permanent failure and is deliberately not
# retried - Retry's default `status_forcelist` behavior already only
# retries the codes listed below, everything else raises immediately.
# backoff_factor=1 with total=3 waits ~1s, 2s, 4s between attempts.
_RETRY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset({"GET", "POST"}),
    raise_on_status=False,
)


def new_session() -> requests.Session:
    """A requests.Session pre-configured with retry/backoff for both
    HTTP(S) and a default timeout header, shared by every ATS scraper
    so retry behavior is defined once instead of per-company."""
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=_RETRY)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(REQUEST_HEADERS)
    return session
