# tests/test_auth.py
import base64
import json
import uuid

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.auth.cognito import get_current_tenant_id


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
