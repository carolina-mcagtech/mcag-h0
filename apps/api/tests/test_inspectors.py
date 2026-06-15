# tests/test_inspectors.py
import base64
import json
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.shared.db.session import get_session, get_session_factory


def _session_override(tenant_id: uuid.UUID):
    async def _override():
        async with get_session_factory()() as session:
            async with session.begin():
                await session.execute(
                    text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'")
                )
                session.info["tenant_id"] = tenant_id
                yield session
    return _override


def _bearer_token(sub: str, tenant_id: str) -> str:
    """Minimal unsigned JWT carrying sub + custom:tenant_id (dev mode only)."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": sub, "custom:tenant_id": tenant_id}).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}."


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def two_tenants(db_engine):
    """Two tenants inserted as superuser, yielded as (t1_id, t2_id)."""
    t1 = uuid.uuid4()
    t2 = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain, is_active)
                VALUES (:t1, 'Alpha Inspections', 'alphainsp-ins', true),
                       (:t2, 'Beta Reports',      'betarep-ins',   true)
            """),
            {"t1": t1, "t2": t2},
        )
    yield t1, t2
    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1, t2]},
        )


@pytest_asyncio.fixture
async def http_client(db_engine, two_tenants):
    t1, _ = two_tenants
    app.dependency_overrides[get_session] = _session_override(t1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


# ── Tests ─────────────────────────────────────────────────────────────────────


async def test_create_inspector_profile(http_client, two_tenants):
    t1, _ = two_tenants
    sub = str(uuid.uuid4())
    token = _bearer_token(sub, str(t1))

    resp = await http_client.post(
        "/inspector-profiles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Alice Rivera",
            "email": "alice@example.com",
            "license_number": "HI12345",
            "license_expiry_date": "2027-12-31",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == sub
    assert body["cognito_sub"] == sub
    assert body["tenant_id"] == str(t1)
    assert body["full_name"] == "Alice Rivera"
    assert body["phone"] is None


async def test_get_my_inspector_profile(http_client, two_tenants):
    t1, _ = two_tenants
    sub = str(uuid.uuid4())
    token = _bearer_token(sub, str(t1))

    await http_client.post(
        "/inspector-profiles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Bob Chen",
            "email": "bob@example.com",
            "license_number": "HI99999",
            "license_expiry_date": "2028-06-30",
        },
    )

    resp = await http_client.get(
        "/inspector-profiles/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == sub
    assert body["full_name"] == "Bob Chen"


async def test_get_my_inspector_profile_not_found(http_client, two_tenants):
    t1, _ = two_tenants
    sub = str(uuid.uuid4())
    token = _bearer_token(sub, str(t1))

    resp = await http_client.get(
        "/inspector-profiles/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


async def test_create_inspector_profile_duplicate_returns_409(http_client, two_tenants):
    t1, _ = two_tenants
    sub = str(uuid.uuid4())
    token = _bearer_token(sub, str(t1))
    payload = {
        "full_name": "Carla Diaz",
        "email": "carla@example.com",
        "license_number": "HI55555",
        "license_expiry_date": "2026-01-01",
    }

    first = await http_client.post(
        "/inspector-profiles", headers={"Authorization": f"Bearer {token}"}, json=payload
    )
    assert first.status_code == 201

    second = await http_client.post(
        "/inspector-profiles", headers={"Authorization": f"Bearer {token}"}, json=payload
    )
    assert second.status_code == 409


async def test_create_inspector_profile_requires_bearer_token(http_client):
    resp = await http_client.post(
        "/inspector-profiles",
        json={
            "full_name": "No Auth",
            "email": "noauth@example.com",
            "license_number": "HI00000",
            "license_expiry_date": "2026-01-01",
        },
    )
    assert resp.status_code == 401
