# tests/test_middleware.py
import base64
import json
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.middleware.tenant import TenantMiddleware, current_tenant_id

# ── Minimal test app ─────────────────────────────────────────────────────────
# Isolated from app.main so these tests are self-contained.

_app = FastAPI()
_app.add_middleware(TenantMiddleware)


@_app.get("/context")
async def _get_context() -> dict[str, str]:
    return {"tenant_id": current_tenant_id.get()}


def _make_dev_token(tenant_id: str) -> str:
    """Build a minimal unsigned JWT carrying custom:tenant_id (dev mode only)."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"custom:tenant_id": tenant_id}).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}."


# ── Middleware / ContextVar tests (no DB required) ───────────────────────────

@pytest.mark.asyncio
async def test_valid_jwt_sets_context() -> None:
    """Bearer JWT with custom:tenant_id sets ContextVar correctly."""
    tid = str(uuid.uuid4())
    token = _make_dev_token(tid)
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/context", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == tid


@pytest.mark.asyncio
async def test_missing_jwt_gives_empty_context() -> None:
    """No Authorization header → ContextVar stays '' (fail-closed)."""
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/context")
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == ""


@pytest.mark.asyncio
async def test_invalid_jwt_gives_empty_context() -> None:
    """Malformed Bearer token → ContextVar stays '' (fail-closed)."""
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/context", headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == ""


@pytest.mark.asyncio
async def test_jwt_missing_tenant_claim_gives_empty_context() -> None:
    """JWT without custom:tenant_id → ContextVar stays ''."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "some-user"}).encode()
    ).rstrip(b"=").decode()
    token = f"{header}.{payload}."
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as client:
        resp = await client.get("/context", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == ""

