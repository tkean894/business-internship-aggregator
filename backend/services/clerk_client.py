from __future__ import annotations

import os

import requests

CLERK_API_BASE = "https://api.clerk.com/v1"
REQUEST_TIMEOUT_SECONDS = 10


def _secret_key() -> str:
    key = os.environ.get("CLERK_SECRET_KEY")
    if not key:
        raise RuntimeError("CLERK_SECRET_KEY is not set.")
    return key


def fetch_clerk_user_email(clerk_user_id: str) -> str:
    """Look up a Clerk user's primary email via Clerk's Backend API.

    Called exactly once per user, the first time we see a new
    `clerk_user_id` in a verified session token (see backend/api/auth.py)
    - after that, the email is cached on our own `users` row, so this
    never runs on the hot path of every authenticated request.
    """
    response = requests.get(
        f"{CLERK_API_BASE}/users/{clerk_user_id}",
        headers={"Authorization": f"Bearer {_secret_key()}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    primary_id = data.get("primary_email_address_id")
    email_addresses = data.get("email_addresses") or []
    for addr in email_addresses:
        if addr.get("id") == primary_id:
            return addr["email_address"]
    if email_addresses:
        return email_addresses[0]["email_address"]

    raise ValueError(f"Clerk user {clerk_user_id} has no email address on file")
