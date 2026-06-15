# tests/test_findings.py
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
    """Seed tenant → inspector → inspection; yield (tenant_id, inspection_id)."""
    tid = uuid.uuid4()
    insp_id = uuid.uuid4()
    iid = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, 'Find Co', 'findco')"),
            {"id": tid},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES (:insp_id, :tid, :sub, 'Find Inspector', 'inspector@findco.com', 'HI00001', '2028-01-01')
            """),
            {"insp_id": insp_id, "tid": tid, "sub": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee)
                VALUES (:iid, :tid, :insp_id, '2026-08-20T09:00:00Z', '7 Oak Ave, Tampa, FL 33601',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 250.00)
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
                    (:t1, 'Find Alpha', 'findalpha'),
                    (:t2, 'Find Beta',  'findbeta')
            """),
            {"t1": t1, "t2": t2},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date) VALUES
                    (:insp1, :t1, :sub1, 'Alpha Inspector', 'inspector@findalpha.com', 'HI00002', '2028-01-01'),
                    (:insp2, :t2, :sub2, 'Beta Inspector',  'inspector@findbeta.com',  'HI00003', '2028-01-01')
            """),
            {"insp1": insp1, "t1": t1, "sub1": uuid.uuid4(), "insp2": insp2, "t2": t2, "sub2": uuid.uuid4()},
        )
        await conn.execute(
            text("""
                INSERT INTO inspections
                    (id, tenant_id, inspector_id, scheduled_at, property_address, inspection_types, total_fee) VALUES
                    (:i1, :t1, :insp1, '2026-09-01T09:00:00Z', '1 Alpha Dr, Miami, FL 33101',
                        ARRAY['FULL_INSPECTION']::inspection_type_enum[], 150.00),
                    (:i2, :t2, :insp2, '2026-09-02T09:00:00Z', '2 Beta Blvd, Naples, FL 34101',
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


# ── Test 1: create finding in structural section (condition required) ──────────


async def test_create_finding_exterior_with_condition(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "EXTERIOR", "item": "Siding", "condition": "GOOD"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["section"] == "EXTERIOR"
    assert body["item"] == "Siding"
    assert body["condition"] == "GOOD"
    assert body["tenant_id"] == str(tid)
    assert body["inspection_id"] == str(iid)
    assert body["sort_order"] == 0
    assert body["estimated_cost"] is None


# ── Test 2: create finding in COMMENTS section without condition ───────────────


async def test_create_finding_comments_no_condition(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.post(
        f"/inspections/{iid}/findings",
        json={
            "section": "COMMENTS",
            "item": "General note about the property",
            "observations": "Some additional context",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["section"] == "COMMENTS"
    assert body["condition"] is None


# ── Test 3: create finding in COST_ESTIMATION with estimated_cost ─────────────


async def test_create_finding_cost_estimation_with_amount(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.post(
        f"/inspections/{iid}/findings",
        json={
            "section": "COST_ESTIMATION",
            "item": "Roof replacement",
            "estimated_cost": "4500.00",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["section"] == "COST_ESTIMATION"
    assert float(body["estimated_cost"]) == 4500.00


# ── Test 4: reject condition on COMMENTS and DISCLOSURE sections ──────────────


async def test_reject_condition_on_comments_section(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "COMMENTS", "item": "Note", "condition": "GOOD"},
    )
    assert resp.status_code == 422


async def test_reject_condition_on_disclosure_section(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "DISCLOSURE", "item": "Disclosure text", "condition": "N_A"},
    )
    assert resp.status_code == 422


# ── Test 5: reject estimated_cost on non-COST_ESTIMATION sections ─────────────


async def test_reject_estimated_cost_on_structural_section(http_client, seeded_inspection):
    tid, iid = seeded_inspection
    resp = await http_client.post(
        f"/inspections/{iid}/findings",
        json={
            "section": "ROOF",
            "item": "Missing shingles",
            "condition": "DEFECTIVE",
            "estimated_cost": "1200.00",
        },
    )
    assert resp.status_code == 422


# ── Test 6: list findings grouped by section ──────────────────────────────────


async def test_list_findings_grouped_by_section(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    # Create findings in two different sections
    await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "ROOF", "item": "Missing shingles", "condition": "DEFECTIVE"},
    )
    await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "ROOF", "item": "Flashing", "condition": "GOOD"},
    )
    await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "ELECTRICAL", "item": "Panel", "condition": "MARGINAL"},
    )

    # Ungrouped list
    flat_resp = await http_client.get(f"/inspections/{iid}/findings")
    assert flat_resp.status_code == 200
    assert len(flat_resp.json()) == 3

    # Grouped list
    grouped_resp = await http_client.get(f"/inspections/{iid}/findings?grouped=true")
    assert grouped_resp.status_code == 200
    groups = grouped_resp.json()
    section_keys = {g["section"] for g in groups}
    assert "ROOF" in section_keys
    assert "ELECTRICAL" in section_keys

    roof_group = next(g for g in groups if g["section"] == "ROOF")
    assert len(roof_group["findings"]) == 2


# ── Test 7: inspection summary shows defective count ─────────────────────────


async def test_inspection_summary_defective_count(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "PLUMBING", "item": "Pipe", "condition": "DEFECTIVE"},
    )
    await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "PLUMBING", "item": "Valve", "condition": "GOOD"},
    )
    await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "ELECTRICAL", "item": "Breaker", "condition": "DEFECTIVE"},
    )

    resp = await http_client.get(f"/inspections/{iid}/findings/summary")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["PLUMBING"]["total"] == 2
    assert summary["PLUMBING"]["defective"] == 1
    assert summary["ELECTRICAL"]["total"] == 1
    assert summary["ELECTRICAL"]["defective"] == 1


# ── Test 8: RLS — cannot access another tenant's findings ─────────────────────


async def test_rls_finding_isolation(db_engine, two_seeded_inspections):
    (t1, i1), (t2, i2) = two_seeded_inspections
    fid = uuid.uuid4()

    # Insert a finding for tenant 1 as superuser
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO findings
                    (id, tenant_id, inspection_id, section, item, condition)
                VALUES
                    (:fid, :tid, :iid, 'EXTERIOR', 'Siding crack', 'DEFECTIVE')
            """),
            {"fid": fid, "tid": t1, "iid": i1},
        )

    # Tenant 2 with app_role must not see tenant 1's finding
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2}'"))
        rows = (
            await conn.execute(text("SELECT id FROM findings"))
        ).fetchall()
    assert len(rows) == 0

    # Tenant 1 sees its own finding
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1}'"))
        rows = (
            await conn.execute(text("SELECT id FROM findings"))
        ).fetchall()
    assert len(rows) == 1
    assert rows[0].id == fid


# ── Test 9: delete finding ────────────────────────────────────────────────────


async def test_delete_finding(http_client, seeded_inspection):
    tid, iid = seeded_inspection

    create_resp = await http_client.post(
        f"/inspections/{iid}/findings",
        json={"section": "KITCHEN", "item": "Cabinet", "condition": "MARGINAL"},
    )
    assert create_resp.status_code == 201
    fid = create_resp.json()["id"]

    delete_resp = await http_client.delete(f"/inspections/{iid}/findings/{fid}")
    assert delete_resp.status_code == 204

    get_resp = await http_client.get(f"/inspections/{iid}/findings/{fid}")
    assert get_resp.status_code == 404


# ── Test 10: 404 when inspection does not exist ───────────────────────────────


async def test_create_finding_unknown_inspection_404(http_client):
    resp = await http_client.post(
        f"/inspections/{uuid.uuid4()}/findings",
        json={"section": "EXTERIOR", "item": "Siding", "condition": "GOOD"},
    )
    assert resp.status_code == 404


async def test_list_findings_unknown_inspection_404(http_client):
    resp = await http_client.get(f"/inspections/{uuid.uuid4()}/findings")
    assert resp.status_code == 404


# ── Test 11: 404 when inspection belongs to another tenant ────────────────────


async def test_findings_for_other_tenants_inspection_404(db_engine, two_seeded_inspections):
    (t1, i1), (t2, i2) = two_seeded_inspections

    # Authenticated as tenant 2, but i1 belongs to tenant 1.
    app.dependency_overrides[get_session] = _session_override(t2)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                f"/inspections/{i1}/findings",
                json={"section": "EXTERIOR", "item": "Siding", "condition": "GOOD"},
            )
            assert resp.status_code == 404

            resp = await client.get(f"/inspections/{i1}/findings")
            assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)


# ── Test 12: finding scoped to a different inspection_id returns 404 ──────────


async def test_finding_not_found_under_wrong_inspection(
    db_engine, two_seeded_inspections
):
    (t1, i1), (t2, i2) = two_seeded_inspections

    app.dependency_overrides[get_session] = _session_override(t1)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            create_resp = await client.post(
                f"/inspections/{i1}/findings",
                json={"section": "EXTERIOR", "item": "Siding", "condition": "GOOD"},
            )
            assert create_resp.status_code == 201
            fid = create_resp.json()["id"]

            # Same tenant, but i2 belongs to tenant 2 — should 404 before reaching the finding.
            resp = await client.get(f"/inspections/{i2}/findings/{fid}")
            assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)
