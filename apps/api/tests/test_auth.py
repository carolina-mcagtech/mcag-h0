# tests/test_auth.py
import base64
import json
import time
import uuid
from unittest.mock import patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from jwt.algorithms import RSAAlgorithm

from app.shared.auth.cognito import get_current_tenant_id, verify_token


def _make_dev_token(tenant_id: str) -> str:
    """Build a minimal unsigned JWT carrying custom:tenant_id (dev mode only)."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"custom:tenant_id": tenant_id}).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}."


# Minimal test app — isolated from app.main
_app = FastAPI()


@_app.get("/protected")
async def _protected(tenant_id: str = Depends(get_current_tenant_id)) -> dict[str, str]:
    return {"tenant_id": tenant_id}


@pytest.mark.asyncio
async def test_bearer_token_with_tenant_id_dev() -> None:
    """Bearer JWT with custom:tenant_id → 200 with correct tenant_id."""
    tid = str(uuid.uuid4())
    token = _make_dev_token(tid)
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == tid


@pytest.mark.asyncio
async def test_missing_bearer_returns_401() -> None:
    """No Authorization header → 401."""
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/protected")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_non_bearer_scheme_returns_401() -> None:
    """Authorization header with non-Bearer scheme → 401."""
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/protected", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_jwt_missing_tenant_claim_returns_401() -> None:
    """Bearer JWT without custom:tenant_id claim → 401."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "no-tenant-here"}).encode()
    ).rstrip(b"=").decode()
    token = f"{header}.{payload}."
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_malformed_token_returns_401() -> None:
    """Malformed Bearer token (not a valid JWT) → 401."""
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/protected", headers={"Authorization": "Bearer notajwt"})
    assert resp.status_code == 401


# ── Production verify_token: multi-client issuer-based validation ──────────

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_JWK = json.loads(RSAAlgorithm(RSAAlgorithm.SHA256).to_jwk(_PRIVATE_KEY.public_key()))
_PUBLIC_JWK["kid"] = "test-kid"
_PUBLIC_JWK["alg"] = "RS256"
_PUBLIC_JWK["use"] = "sig"
_JWKS = {"keys": [_PUBLIC_JWK]}

_POOL_ID = "us-east-1_ZbCnC86PS"
_REGION = "us-east-1"
_ISSUER = f"https://cognito-idp.{_REGION}.amazonaws.com/{_POOL_ID}"
_WEB_CLIENT_ID = "web-client-id"
_SCRIPTS_CLIENT_ID = "scripts-client-id"


def _sign(claims: dict) -> str:
    payload = {"exp": int(time.time()) + 3600, **claims}
    return pyjwt.encode(payload, _PRIVATE_KEY, algorithm="RS256", headers={"kid": "test-kid"})


def _prod_settings_patch(allowed_client_ids: list[str]):
    return patch.multiple(
        "app.shared.auth.cognito.settings",
        app_env="production",
        cognito_pool_id=_POOL_ID,
        cognito_region=_REGION,
        cognito_allowed_client_ids=allowed_client_ids,
    )


def test_verify_token_prod_web_client_passes() -> None:
    """ID token minted for the web app client → accepted."""
    token = _sign({"iss": _ISSUER, "aud": _WEB_CLIENT_ID, "token_use": "id", "sub": "user-1"})
    with (
        _prod_settings_patch([_WEB_CLIENT_ID, _SCRIPTS_CLIENT_ID]),
        patch("app.shared.auth.cognito._fetch_jwks_sync", return_value=_JWKS),
    ):
        claims = verify_token(token)
    assert claims["aud"] == _WEB_CLIENT_ID


def test_verify_token_prod_allowed_scripts_client_passes() -> None:
    """ID token minted for the scripts/automation client → accepted when allowlisted."""
    token = _sign({"iss": _ISSUER, "aud": _SCRIPTS_CLIENT_ID, "token_use": "id", "sub": "automation"})
    with (
        _prod_settings_patch([_WEB_CLIENT_ID, _SCRIPTS_CLIENT_ID]),
        patch("app.shared.auth.cognito._fetch_jwks_sync", return_value=_JWKS),
    ):
        claims = verify_token(token)
    assert claims["aud"] == _SCRIPTS_CLIENT_ID


def test_verify_token_prod_wrong_issuer_fails() -> None:
    """Token signed for a different Cognito pool → 401."""
    token = _sign(
        {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_someotherpool",
            "aud": _WEB_CLIENT_ID,
            "token_use": "id",
            "sub": "user-1",
        }
    )
    with (
        _prod_settings_patch([_WEB_CLIENT_ID, _SCRIPTS_CLIENT_ID]),
        patch("app.shared.auth.cognito._fetch_jwks_sync", return_value=_JWKS),
    ):
        with pytest.raises(Exception) as exc_info:
            verify_token(token)
    assert getattr(exc_info.value, "status_code", None) == 401


def test_verify_token_prod_client_id_not_allowed_fails() -> None:
    """Correctly signed, correct issuer, but client id not in the allowlist → 401."""
    token = _sign({"iss": _ISSUER, "aud": "unknown-client-id", "token_use": "id", "sub": "user-1"})
    with (
        _prod_settings_patch([_WEB_CLIENT_ID, _SCRIPTS_CLIENT_ID]),
        patch("app.shared.auth.cognito._fetch_jwks_sync", return_value=_JWKS),
    ):
        with pytest.raises(Exception) as exc_info:
            verify_token(token)
    assert getattr(exc_info.value, "status_code", None) == 401
