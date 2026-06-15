# tests/test_tenants.py
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.config import settings
from app.main import app
from app.modules.tenants.models import PlanEnum
from app.shared.db.session import get_admin_session, get_session, get_session_factory


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


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def http_client(db_engine):
    """AsyncClient wired to the full FastAPI app with a real DB."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def seeded_tenant(db_engine):
    """Insert a tenant as superuser (bypasses RLS) and yield its UUID."""
    tid = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain, is_active,
                                     custom_domain, theme_config)
                VALUES (:id, 'Seed Co', 'seedco', true,
                        'seed.example.com', '{}')
            """),
            {"id": tid},
        )
    yield tid
    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = :id"), {"id": tid}
        )


# ── Test 1: create tenant with valid subdomain ────────────────────────────────


async def test_create_tenant_valid(http_client):
    resp = await http_client.post(
        "/tenants",
        json={"name": "Acme Inspections", "subdomain": "acmeinsp"},
        headers={"X-Admin-Api-Key": settings.admin_api_key},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["subdomain"] == "acmeinsp"
    assert body["plan"] == PlanEnum.STARTER
    assert body["theme_config"] == {}
    assert body["is_active"] is True


# ── Test 2: reject duplicate subdomain ───────────────────────────────────────


async def test_create_tenant_duplicate_subdomain(http_client, seeded_tenant):
    resp = await http_client.post(
        "/tenants",
        json={"name": "Copy Co", "subdomain": "seedco"},
        headers={"X-Admin-Api-Key": settings.admin_api_key},
    )
    assert resp.status_code == 409
    assert "subdomain" in resp.json()["detail"]


# ── Test 3: reject invalid subdomain formats ──────────────────────────────────


@pytest.mark.parametrize(
    "subdomain",
    [
        "-leading",        # leading hyphen
        "trailing-",       # trailing hyphen
        "AB",              # uppercase
        "ab",              # too short (< 3 chars)
        "a" * 64,          # too long (> 63 chars)
        "has space",       # space
        "has_underscore",  # underscore
    ],
)
async def test_create_tenant_invalid_subdomain(http_client, subdomain):
    resp = await http_client.post(
        "/tenants",
        json={"name": "Bad Co", "subdomain": subdomain},
        headers={"X-Admin-Api-Key": settings.admin_api_key},
    )
    assert resp.status_code == 422


# ── Test 3b: admin key enforcement on POST /tenants ──────────────────────────


async def test_create_tenant_missing_admin_key(http_client):
    resp = await http_client.post(
        "/tenants", json={"name": "Acme Inspections", "subdomain": "acmeinsp"}
    )
    assert resp.status_code == 403


async def test_create_tenant_wrong_admin_key(http_client):
    resp = await http_client.post(
        "/tenants",
        json={"name": "Acme Inspections", "subdomain": "acmeinsp"},
        headers={"X-Admin-Api-Key": "totally-wrong"},
    )
    assert resp.status_code == 403


# ── Test 4: get_tenant_by_subdomain works without RLS ────────────────────────


async def test_get_tenant_by_subdomain_no_rls(db_engine, seeded_tenant):
    from app.modules.tenants import service

    async for admin_session in get_admin_session():
        tenant = await service.get_tenant_by_subdomain("seedco", admin_session)

    assert tenant is not None
    assert tenant.subdomain == "seedco"
    assert str(tenant.id) == str(seeded_tenant)


# ── Test 5: RLS — tenant A cannot see tenant B ────────────────────────────────


async def test_rls_cross_tenant_isolation(db_engine):
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain, is_active)
                VALUES (:t1, 'Alpha Corp', 'alphacorp', true),
                       (:t2, 'Beta LLC',  'betallc',   true)
            """),
            {"t1": t1_id, "t2": t2_id},
        )

    try:
        # Tenant 1 context — must see only its own row
        async with db_engine.begin() as conn:
            await conn.execute(text("SET LOCAL ROLE app_role"))
            await conn.execute(
                text(f"SET LOCAL app.current_tenant_id = '{t1_id}'")
            )
            rows = (await conn.execute(text("SELECT id FROM tenants"))).fetchall()

        assert len(rows) == 1
        assert rows[0].id == t1_id

        # Tenant 2 context — must see only its own row
        async with db_engine.begin() as conn:
            await conn.execute(text("SET LOCAL ROLE app_role"))
            await conn.execute(
                text(f"SET LOCAL app.current_tenant_id = '{t2_id}'")
            )
            rows = (await conn.execute(text("SELECT id FROM tenants"))).fetchall()

        assert len(rows) == 1
        assert rows[0].id == t2_id

    finally:
        async with db_engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM tenants WHERE id = ANY(:ids)"),
                {"ids": [t1_id, t2_id]},
            )


# ── Test 6: theme_config stores and retrieves correctly ──────────────────────


async def test_theme_config_round_trip(http_client, seeded_tenant):
    tid = seeded_tenant
    theme = {"primary_color": "#FF5733", "logo_url": "https://cdn.example.com/logo.png"}

    app.dependency_overrides[get_session] = _session_override(tid)
    try:
        put_resp = await http_client.put(
            "/tenants/me/theme",
            json={"theme_config": theme},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["theme_config"] == theme

        get_resp = await http_client.get("/tenants/me")
        assert get_resp.status_code == 200
        assert get_resp.json()["theme_config"] == theme
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 7: internal endpoint requires a valid token ─────────────────────────


async def test_internal_endpoint_missing_token(http_client, seeded_tenant):
    resp = await http_client.get(
        "/internal/tenant-by-domain?hostname=seed.example.com"
    )
    # FastAPI returns 422 when a required Header is absent
    assert resp.status_code == 422


async def test_internal_endpoint_wrong_token(http_client, seeded_tenant):
    resp = await http_client.get(
        "/internal/tenant-by-domain?hostname=seed.example.com",
        headers={"X-Internal-Token": "wrong-token"},
    )
    assert resp.status_code == 401


async def test_internal_endpoint_valid_token(http_client, seeded_tenant):
    resp = await http_client.get(
        "/internal/tenant-by-domain?hostname=seed.example.com",
        headers={"X-Internal-Token": settings.internal_api_token},
    )
    assert resp.status_code == 200
    assert resp.json()["subdomain"] == "seedco"


async def test_internal_endpoint_subdomain_fallback(http_client, seeded_tenant):
    """hostname matches subdomain (no custom_domain set) — should still resolve."""
    resp = await http_client.get(
        "/internal/tenant-by-domain?hostname=seedco",
        headers={"X-Internal-Token": settings.internal_api_token},
    )
    assert resp.status_code == 200
    assert resp.json()["subdomain"] == "seedco"


async def test_internal_endpoint_not_found(http_client):
    resp = await http_client.get(
        "/internal/tenant-by-domain?hostname=does-not-exist",
        headers={"X-Internal-Token": settings.internal_api_token},
    )
    assert resp.status_code == 404
