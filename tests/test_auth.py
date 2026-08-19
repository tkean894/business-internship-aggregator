"""Tests for the actual JWT verification logic (backend/api/auth.py),
run against Clerk's real JWKS endpoint (requires CLERK_JWKS_URL to be
configured, same as production) - route-level tests elsewhere use
FastAPI dependency overrides instead (see tests/conftest.py) since
they're testing route behavior, not signature verification itself."""

from __future__ import annotations

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from backend.api.auth import _decode_clerk_token
from backend.api.main import app

client = TestClient(app)


def test_garbage_token_is_rejected():
    with pytest.raises(Exception):
        _decode_clerk_token("not.a.valid.jwt")


def test_forged_token_with_real_key_id_is_rejected():
    """An attacker who knows Clerk's key ID (public info, in the JWKS
    response) but not Clerk's private key must not be able to forge a
    valid-looking token."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    forged = jwt.encode(
        {"sub": "user_attacker"},
        private_pem,
        algorithm="RS256",
        headers={"kid": "ins_3I7e4axFe1MGVo7c3M2s9GOtjKX"},  # Clerk's real, public key ID
    )
    with pytest.raises(Exception):
        _decode_clerk_token(forged)


def test_protected_endpoint_rejects_missing_auth_header():
    resp = client.get("/me")
    assert resp.status_code == 401


def test_protected_endpoint_rejects_malformed_auth_header():
    resp = client.get("/me", headers={"Authorization": "NotBearer something"})
    assert resp.status_code == 401


def test_protected_endpoint_rejects_garbage_bearer_token():
    resp = client.get("/me", headers={"Authorization": "Bearer garbage.token.here"})
    assert resp.status_code == 401


def test_anonymous_browsing_endpoints_still_work_without_auth():
    """Public endpoints must never require the Authorization header."""
    assert client.get("/internships").status_code == 200
    assert client.get("/companies").status_code == 200
    assert client.get("/categories").status_code == 200
