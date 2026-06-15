# tests/test_properties.py
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
                VALUES (:t1, 'Alpha Inspections', 'alphainsp', true),
                       (:t2, 'Beta Reports',      'betarep',   true)
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


# ── Test 1: create with required fields only ─────────────────────────────────


async def test_create_property_required_fields(http_client, two_tenants):
    t1, _ = two_tenants
    resp = await http_client.post(
        "/properties",
        json={"street": "123 Oak St", "city": "Tampa", "zip_code": "33601"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["street"] == "123 Oak St"
    assert body["city"] == "Tampa"
    assert body["state"] == "FL"
    assert body["zip_code"] == "33601"
    assert body["tenant_id"] == str(t1)
    assert body["appliances"] == {}
    assert body["bedrooms"] == {}
    assert body["bathrooms"] == {}
    assert body["year_built"] is None
    assert body["roof_permit_number"] is None


# ── Test 2: create with all fields ───────────────────────────────────────────


async def test_create_property_all_fields(http_client, two_tenants):
    t1, _ = two_tenants
    payload = {
        "street": "456 Palm Ave",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32801",
        "year_built": 1998,
        "adjusted_sqft": 2100,
        "roof_permit_number": "RP-2023-001",
        "roof_permit_date": "2023-04-15",
        "roof_style": "Hip",
        "roof_type": "Shingle",
        "water_heater_type": "Tankless",
        "water_heater_location": "Garage",
        "water_heater_capacity": "50 gal",
        "electrical_brand": "Square D",
        "electrical_amps": 200,
        "electrical_location": "Utility Room",
        "ac_brand": "Carrier",
        "ac_age": 5,
        "ac_model": "24ACC636A003",
        "ac_series": "Comfort",
        "mit_doors_protection": True,
        "mit_windows_protection": False,
        "appliances": {"refrigerator": "Samsung", "stove": "GE"},
        "bedrooms": {"count": 3},
        "bathrooms": {"full": 2, "half": 1},
    }
    resp = await http_client.post("/properties", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["roof_permit_number"] == "RP-2023-001"
    assert body["roof_permit_date"] == "2023-04-15"
    assert body["electrical_amps"] == 200
    assert body["mit_doors_protection"] is True
    assert body["mit_windows_protection"] is False
    assert body["appliances"] == {"refrigerator": "Samsung", "stove": "GE"}
    assert body["bedrooms"] == {"count": 3}


# ── Test 3: list — RLS shows only current tenant's properties ─────────────────
# RLS is only active for non-superuser roles. The test engine connects as
# postgres (superuser), so we drop to app_role — same pattern as test_rls.py
# and test_inspector_rls.py — to exercise the actual policy.


async def test_list_properties_rls(db_engine, two_tenants):
    t1, t2 = two_tenants
    p1_id, p2_id = uuid.uuid4(), uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO properties (id, tenant_id, street, city, state, zip_code)
                VALUES (:p1, :t1, '1 T1 St',  'Miami',  'FL', '33101'),
                       (:p2, :t2, '2 T2 Ave', 'Naples', 'FL', '34101')
            """),
            {"p1": p1_id, "t1": t1, "p2": p2_id, "t2": t2},
        )

    # Tenant 1 — should see exactly its own row
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1}'"))
        rows = (await conn.execute(text("SELECT tenant_id FROM properties"))).fetchall()
    assert len(rows) == 1
    assert rows[0].tenant_id == t1

    # Tenant 2 — should see exactly its own row
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2}'"))
        rows = (await conn.execute(text("SELECT tenant_id FROM properties"))).fetchall()
    assert len(rows) == 1
    assert rows[0].tenant_id == t2


# ── Test 4: update property ───────────────────────────────────────────────────


async def test_update_property(http_client, two_tenants):
    t1, _ = two_tenants

    create_resp = await http_client.post(
        "/properties",
        json={"street": "100 Main St", "city": "Sarasota", "zip_code": "34230"},
    )
    prop_id = create_resp.json()["id"]

    update_resp = await http_client.put(
        f"/properties/{prop_id}",
        json={"year_built": 2005, "roof_style": "Gable", "ac_brand": "Lennox"},
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["year_built"] == 2005
    assert body["roof_style"] == "Gable"
    assert body["ac_brand"] == "Lennox"
    assert body["street"] == "100 Main St"  # unchanged


# ── Test 5: cannot access another tenant's property ──────────────────────────
# Verified at the DB layer with app_role (the role that respects RLS) rather
# than through HTTP, which runs as a superuser that bypasses FORCE ROW SECURITY.
# In production the app will connect as app_role, so this test reflects reality.


async def test_cross_tenant_property_invisible_under_rls(db_engine, two_tenants):
    t1, t2 = two_tenants
    prop_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO properties (id, tenant_id, street, city, state, zip_code)
                VALUES (:pid, :tid, '99 Private Ln', 'Clearwater', 'FL', '33755')
            """),
            {"pid": prop_id, "tid": t1},
        )

    # Tenant 2 with app_role — must see zero rows for tenant 1's property
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2}'"))
        rows = (
            await conn.execute(
                text("SELECT id FROM properties WHERE id = :pid"),
                {"pid": prop_id},
            )
        ).fetchall()

    assert len(rows) == 0, "RLS must hide tenant 1's property from tenant 2"

    # No context at all — fail-closed, zero rows
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        rows = (
            await conn.execute(
                text("SELECT id FROM properties WHERE id = :pid"),
                {"pid": prop_id},
            )
        ).fetchall()

    assert len(rows) == 0, "RLS must hide all rows when tenant context is unset"
