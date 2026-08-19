from __future__ import annotations

import logging
import os

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.models import User
from backend.services.clerk_client import fetch_clerk_user_email

logger = logging.getLogger(__name__)

# e.g. https://your-app-name.clerk.accounts.dev/.well-known/jwks.json -
# derivable from the Clerk publishable key's encoded frontend-API
# domain, but read from its own env var so it's explicit and doesn't
# require decoding a key at runtime.
CLERK_JWKS_URL = os.environ.get("CLERK_JWKS_URL")

_jwk_client: PyJWKClient | None = None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        if not CLERK_JWKS_URL:
            raise RuntimeError("CLERK_JWKS_URL is not set.")
        _jwk_client = PyJWKClient(CLERK_JWKS_URL, cache_keys=True)
    return _jwk_client


def _decode_clerk_token(token: str) -> dict:
    """Verify a Clerk session JWT's signature against Clerk's own JWKS
    and decode its claims. This is the whole point of using Clerk: the
    backend trusts nothing the frontend claims about who's signed in -
    only a token whose signature actually validates against Clerk's
    public key is accepted (Phase 9, Step 11)."""
    jwk_client = _get_jwk_client()
    signing_key = jwk_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},  # Clerk session tokens don't set a conventional `aud`
    )


def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """Resolve the authenticated user, or None for a genuinely anonymous
    request (no Authorization header at all - the normal, expected case
    for public browsing). A *present but invalid/expired* token is
    rejected with 401 rather than quietly downgraded to "anonymous" -
    otherwise a client could never tell the difference between "you're
    not signed in" and "your session expired, please sign in again".

    On a user's first verified request, looks up their email via
    Clerk's Backend API and creates the local `users` row - Clerk is
    the source of truth for identity/credentials, this table just
    mirrors the minimum needed for foreign keys and composing emails.
    """
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        payload = _decode_clerk_token(token)
    except Exception:
        # Never log the token itself - only that verification failed.
        logger.info("Rejected an invalid or expired authentication token")
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token") from None

    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    user = db.query(User).filter_by(clerk_user_id=clerk_user_id).one_or_none()
    if user is None:
        email = fetch_clerk_user_email(clerk_user_id)
        user = User(clerk_user_id=clerk_user_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    """Dependency for endpoints that require authentication."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
