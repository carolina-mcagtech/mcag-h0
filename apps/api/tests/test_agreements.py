# tests/test_agreements.py
import uuid
from datetime import date

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.shared.db.session import get_session, get_session_factory


def _session_override(tenant_id: uuid.UUID):
    async def _override():
        async with get_session_factory()() as session:
            async with session.begin():
                # db_engine connects as superuser, which bypasses RLS entirely.
                # Switch to app_role so RLS policies are actually enforced.
                await session.execute(text("SET LOCAL ROLE app_role"))
                await session.execute(
                    text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'")
                )
                session.info["tenant_id"] = tenant_id
                yield session
    return _override


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def seeded_inspection(db_engine):
    """Seed tenant → inspector → inspection as superuser; yield (tenant_id, inspection_id)."""
    tid = uuid.uuid4()
    insp_id = uuid.uuid4()
    iid = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, 'Agree Co', 'agreeco')"),
            {"id": tid},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES (:insp_id, :tid, :sub, 'Agree Inspector', 'inspector@agreeco.com', 'HI00007', '2028-01-01')
            """),
            {"insp_id": insp_id, "tid": tid, "sub": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee)
                VALUES (:iid, :tid, :insp_id, '2026-08-20T09:00:00Z', '5 Oak St, Tampa, FL 33601',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 200.00)
            """),
            {"iid": iid, "tid": tid, "insp_id": insp_id},
        )
    yield tid, iid
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tid})


@pytest_asyncio.fixture
async def two_seeded_inspections(db_engine):
    """Two independent tenant/inspector/inspection chains; yield ((t1,i1), (t2,i2))."""
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    insp1, insp2 = uuid.uuid4(), uuid.uuid4()
    i1, i2 = uuid.uuid4(), uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain) VALUES
                    (:t1, 'Agree Alpha', 'agreealpha'),
                    (:t2, 'Agree Beta',  'agreebeta')
            """),
            {"t1": t1, "t2": t2},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date) VALUES
                    (:insp1, :t1, :sub1, 'Alpha Inspector', 'inspector@agreealpha.com', 'HI00008', '2028-01-01'),
                    (:insp2, :t2, :sub2, 'Beta Inspector',  'inspector@agreebeta.com',  'HI00009', '2028-01-01')
            """),
            {"insp1": insp1, "t1": t1, "sub1": uuid.uuid4(), "insp2": insp2, "t2": t2, "sub2": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee) VALUES
                    (:i1, :t1, :insp1, '2026-09-01T09:00:00Z', '1 Alpha Ln, Miami, FL 33101',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 150.00),
                    (:i2, :t2, :insp2, '2026-09-02T09:00:00Z', '2 Beta Rd, Naples, FL 34101',
                        ARRAY['WIND_MITIGATION']::inspection_type_enum[], 175.00)
            """),
            {"i1": i1, "t1": t1, "insp1": insp1, "i2": i2, "t2": t2, "insp2": insp2},
        )
    yield (t1, i1), (t2, i2)
    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1, t2]},
        )


@pytest_asyncio.fixture
async def http_client(db_engine, seeded_inspection):
    tid, _ = seeded_inspection
    app.dependency_overrides[get_session] = _session_override(tid)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


def _agreement_payload(**kwargs) -> dict:
    return {
        "client_name": "Jane Homeowner",
        "property_address": "5 Oak St, Tampa FL 33601",
        "inspection_date": str(date(2026, 8, 20)),
        "fee_amount": "200.00",
        "payment_timing": "AT_PROPERTY",
        **kwargs,
    }


# ── Test 1: create agreement for inspection ───────────────────────────────────


async def test_create_agreement(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.post(f"/inspections/{iid}/agreements", json=_agreement_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["inspection_id"] == str(iid)
    assert body["tenant_id"] == str(tid)
    assert body["client_name"] == "Jane Homeowner"
    assert float(body["fee_amount"]) == 200.00
    # liquidated_damages_amount defaults to fee * 1.5
    assert float(body["liquidated_damages_amount"]) == 300.00
    assert body["signed_by_client"] is False
    assert body["signed_at"] is None
    assert body["agreement_version"] == "InterNACHI-Feb-2019"
    assert body["exclusions_acknowledged"] is False


# ── Test 2: duplicate agreement for same inspection rejected ──────────────────


async def test_duplicate_agreement_rejected(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    payload = _agreement_payload()

    await http_client.post(f"/inspections/{iid}/agreements", json=payload)
    resp2 = await http_client.post(f"/inspections/{iid}/agreements", json=payload)
    assert resp2.status_code == 409


# ── Test 3: sign agreement sets signed_at timestamp ──────────────────────────


async def test_sign_agreement_sets_signed_at(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    create_resp = await http_client.post(f"/inspections/{iid}/agreements", json=_agreement_payload())
    aid = create_resp.json()["id"]

    sign_resp = await http_client.post(
        f"/inspections/{iid}/agreements/{aid}/sign",
        json={"signed_by_client": True, "exclusions_acknowledged": True},
    )
    assert sign_resp.status_code == 200
    body = sign_resp.json()
    assert body["signed_by_client"] is True
    assert body["exclusions_acknowledged"] is True
    assert body["signed_at"] is not None


# ── Test 4: cannot sign already-signed agreement ──────────────────────────────


async def test_cannot_sign_twice(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    create_resp = await http_client.post(f"/inspections/{iid}/agreements", json=_agreement_payload())
    aid = create_resp.json()["id"]

    await http_client.post(
        f"/inspections/{iid}/agreements/{aid}/sign",
        json={"signed_by_client": True, "exclusions_acknowledged": True},
    )
    resp2 = await http_client.post(
        f"/inspections/{iid}/agreements/{aid}/sign",
        json={"signed_by_client": True, "exclusions_acknowledged": True},
    )
    assert resp2.status_code == 409
    assert "already signed" in resp2.json()["detail"]


# ── Test 5: RLS — cannot access another tenant's agreement ────────────────────


async def test_rls_agreement_isolation(db_engine, two_seeded_inspections):
    (t1, i1), (t2, i2) = two_seeded_inspections
    a1 = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO agreements
                    (id, tenant_id, inspection_id, client_name, property_address,
                     inspection_date, fee_amount, payment_timing,
                     liquidated_damages_amount)
                VALUES
                    (:aid, :tid, :iid, 'Alice', '1 Alpha Ln, Miami FL',
                     '2026-09-01', 150.00, 'AT_PROPERTY', 225.00)
            """),
            {"aid": a1, "tid": t1, "iid": i1},
        )

    # Tenant 2 with app_role must not see tenant 1's agreement
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2}'"))
        rows = (
            await conn.execute(text("SELECT id FROM agreements"))
        ).fetchall()
    assert len(rows) == 0

    # Tenant 1 sees its own agreement
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1}'"))
        rows = (
            await conn.execute(text("SELECT id FROM agreements"))
        ).fetchall()
    assert len(rows) == 1
    assert rows[0].id == a1


# ── Test 6: list and get agreement ─────────────────────────────────────────────


async def test_list_and_get_agreement(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    create_resp = await http_client.post(f"/inspections/{iid}/agreements", json=_agreement_payload())
    aid = create_resp.json()["id"]

    list_resp = await http_client.get(f"/inspections/{iid}/agreements")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert len(body) == 1
    assert body[0]["id"] == aid

    get_resp = await http_client.get(f"/inspections/{iid}/agreements/{aid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == aid


# ── Test 7: update agreement ────────────────────────────────────────────────


async def test_update_agreement(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    create_resp = await http_client.post(f"/inspections/{iid}/agreements", json=_agreement_payload())
    aid = create_resp.json()["id"]

    update_resp = await http_client.put(
        f"/inspections/{iid}/agreements/{aid}",
        json={"client_name": "John Buyer", "fee_amount": "250.00"},
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["client_name"] == "John Buyer"
    assert float(body["fee_amount"]) == 250.00


async def test_update_agreement_not_found(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.put(
        f"/inspections/{iid}/agreements/{uuid.uuid4()}",
        json={"client_name": "John Buyer"},
    )
    assert resp.status_code == 404


# ── Test 8: 404 when inspection does not exist ─────────────────────────────────


async def test_create_agreement_unknown_inspection_404(http_client):
    resp = await http_client.post(
        f"/inspections/{uuid.uuid4()}/agreements", json=_agreement_payload()
    )
    assert resp.status_code == 404


async def test_list_agreements_unknown_inspection_404(http_client):
    resp = await http_client.get(f"/inspections/{uuid.uuid4()}/agreements")
    assert resp.status_code == 404


# ── Test 9: 404 when inspection belongs to another tenant ──────────────────────


async def test_agreements_for_other_tenants_inspection_404(db_engine, two_seeded_inspections):
    (t1, i1), (t2, i2) = two_seeded_inspections

    # Authenticated as tenant 2, but i1 belongs to tenant 1.
    app.dependency_overrides[get_session] = _session_override(t2)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(f"/inspections/{i1}/agreements", json=_agreement_payload())
            assert resp.status_code == 404

            resp = await client.get(f"/inspections/{i1}/agreements")
            assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 10: agreement scoped to a different inspection_id returns 404 ────────


async def test_agreement_not_found_under_wrong_inspection(db_engine, two_seeded_inspections):
    (t1, i1), (t2, i2) = two_seeded_inspections

    app.dependency_overrides[get_session] = _session_override(t1)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            create_resp = await client.post(f"/inspections/{i1}/agreements", json=_agreement_payload())
            assert create_resp.status_code == 201
            aid = create_resp.json()["id"]

            # Same tenant, but i2 belongs to tenant 2 — should 404 before reaching the agreement.
            resp = await client.get(f"/inspections/{i2}/agreements/{aid}")
            assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)
