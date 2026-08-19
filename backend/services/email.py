from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
REQUEST_TIMEOUT_SECONDS = 15


class EmailSendError(Exception):
    """Raised when an email could not be sent. Callers (the notification
    job - see backend/services/notifications.py) are responsible for
    recording this against the relevant NotificationEvent row(s); this
    module never retries or swallows a failure silently."""


def send_email(*, to: str, subject: str, html: str) -> str:
    """Send a transactional email via Resend. Returns the provider's
    message ID on success.

    Without a verified sending domain, Resend's free tier only
    delivers to the account owner's own email address - a real
    limitation of this MVP setup (Phase 9, Step 9), not a bug here.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("NOTIFICATIONS_FROM_EMAIL")
    if not api_key or not from_email:
        raise EmailSendError("RESEND_API_KEY / NOTIFICATIONS_FROM_EMAIL is not configured")

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"from": from_email, "to": [to], "subject": subject, "html": html},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise EmailSendError(f"Request to Resend failed: {exc}") from exc

    if response.status_code >= 400:
        # The API key is only ever sent in the request header, never
        # present in the response body, so logging/raising this is safe.
        raise EmailSendError(f"Resend returned {response.status_code}: {response.text[:300]}")

    message_id = response.json().get("id", "")
    logger.info("Sent email to %s (subject=%r, resend_id=%s)", to, subject, message_id)
    return message_id
