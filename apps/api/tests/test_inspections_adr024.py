# tests/test_inspections_adr024.py
"""RLS + schema tests for the ADR-024 inspections module (migration 010).

Covers: inspections (new schema), report_snapshots, inspector_narrative_library.
Pure-SQL, superuser-seeded / app_role-read tests — no dependency on
schemas/service/router (Tareas 2-4).
"""
import uuid
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError


@pytest_asyncio.fixture
async def two_tenant_inspectors(db_engine):
    t1_id, t2_id = uuid.uuid4(), uuid.uuid4()
    i1_id, i2_id = uuid.uuid4(), uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain, is_active)
                VALUES (:t1, 'Suncoast Inspections', 'suncoast-adr024', true),
                       (:t2, 'Gulf Coast Reports',   'gulfcoast-adr024', true)
            """),
            {"t1": t1_id, "t2": t2_id},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email,
                     license_number, license_expiry_date)
                VALUES
                    (:i1, :t1, :sub1, 'Alice Rivera', 'alice@suncoast.com',
                     'HI12345', :exp1),
                    (:i2, :t2, :sub2, 'Bob Chen',     'bob@gulfcoast.com',
                     'HI99999', :exp2)
            """),
            {
                "i1": i1_id, "t1": t1_id, "sub1": uuid.uuid4(), "exp1": date(2027, 12, 31),
                "i2": i2_id, "t2": t2_id, "sub2": uuid.uuid4(), "exp2": date(2028, 6, 30),
            },
        )

    yield t1_id, t2_id, i1_id, i2_id

    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1_id, t2_id]},
        )


def _insert_inspection_sql() -> str:
    return """
        INSERT INTO inspections
            (id, tenant_id, inspector_id, scheduled_at, property_address,
             inspection_types, total_fee)
        VALUES
            (:id, :tenant_id, :inspector_id, :scheduled_at, :property_address,
             :inspection_types, :total_fee)
    """


# ── inspections: RLS isolation on the new ADR-024 schema ───────────────────


@pytest.mark.asyncio
async def test_inspections_rls_isolation(db_engine, two_tenant_inspectors):
    t1_id, t2_id, i1_id, i2_id = two_tenant_inspectors
    insp1, insp2 = uuid.uuid4(), uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text(_insert_inspection_sql()),
            {
                "id": insp1, "tenant_id": t1_id, "inspector_id": i1_id,
                "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
                "property_address": "10 Test Ln, Tampa, FL 33601",
                "inspection_types": ["FULL_INSPECTION"],
                "total_fee": "150.00",
            },
        )
        await conn.execute(
            text(_insert_inspection_sql()),
            {
                "id": insp2, "tenant_id": t2_id, "inspector_id": i2_id,
                "scheduled_at": datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc),
                "property_address": "2 Beta Ave, Naples, FL 34101",
                "inspection_types": ["WIND_MITIGATION", "FOUR_POINT"],
                "total_fee": "200.00",
            },
        )

    # Default status is DRAFT
    async with db_engine.begin() as conn:
        row = (
            await conn.execute(text("SELECT status FROM inspections WHERE id = :id"), {"id": insp1})
        ).first()
    assert row.status == "DRAFT"

    # Tenant 1 sees only its own inspection
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1_id}'"))
        rows = (await conn.execute(text("SELECT id FROM inspections"))).fetchall()
    assert [r.id for r in rows] == [insp1]

    # Tenant 2 sees only its own inspection
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2_id}'"))
        rows = (await conn.execute(text("SELECT id FROM inspections"))).fetchall()
    assert [r.id for r in rows] == [insp2]

    # No context — fail-closed, zero rows
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        rows = (await conn.execute(text("SELECT id FROM inspections"))).fetchall()
    assert rows == []

    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM inspections WHERE id = ANY(:ids)"), {"ids": [insp1, insp2]})


# ── inspections: new enum types accept the full ADR-024 value sets ─────────


@pytest.mark.asyncio
async def test_inspection_types_accepts_new_adr024_values(db_engine, two_tenant_inspectors):
    t1_id, _, i1_id, _ = two_tenant_inspectors
    insp_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text(_insert_inspection_sql()),
            {
                "id": insp_id, "tenant_id": t1_id, "inspector_id": i1_id,
                "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
                "property_address": "10 Test Ln, Tampa, FL 33601",
                "inspection_types": ["LEAD_PAINT_INSPECTION", "WATER_QUALITY_TEST"],
                "total_fee": "150.00",
            },
        )
        rows = (
            await conn.execute(text("SELECT inspection_types FROM inspections WHERE id = :id"), {"id": insp_id})
        ).first()
    assert set(rows.inspection_types) == {"LEAD_PAINT_INSPECTION", "WATER_QUALITY_TEST"}

    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM inspections WHERE id = :id"), {"id": insp_id})


@pytest.mark.asyncio
async def test_inspection_types_nonempty_constraint(db_engine, two_tenant_inspectors):
    t1_id, _, i1_id, _ = two_tenant_inspectors
    insp_id = uuid.uuid4()

    with pytest.raises((IntegrityError, DBAPIError)):
        async with db_engine.begin() as conn:
            await conn.execute(
                text(_insert_inspection_sql()),
                {
                    "id": insp_id, "tenant_id": t1_id, "inspector_id": i1_id,
                    "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
                    "property_address": "10 Test Ln, Tampa, FL 33601",
                    "inspection_types": [],
                    "total_fee": "150.00",
                },
            )


@pytest.mark.asyncio
async def test_inspection_status_transitions_through_adr024_fsm(db_engine, two_tenant_inspectors):
    t1_id, _, i1_id, _ = two_tenant_inspectors
    insp_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text(_insert_inspection_sql()),
            {
                "id": insp_id, "tenant_id": t1_id, "inspector_id": i1_id,
                "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
                "property_address": "10 Test Ln, Tampa, FL 33601",
                "inspection_types": ["FULL_INSPECTION"],
                "total_fee": "150.00",
            },
        )

    for new_status in ("IN_FIELD", "PENDING_REVIEW", "PUBLISHED", "DELIVERED"):
        async with db_engine.begin() as conn:
            await conn.execute(
                text("UPDATE inspections SET status = :status WHERE id = :id"),
                {"status": new_status, "id": insp_id},
            )
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(text("SELECT status FROM inspections WHERE id = :id"), {"id": insp_id})
            ).first()
        assert row.status == new_status

    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM inspections WHERE id = :id"), {"id": insp_id})


# ── report_snapshots: RLS isolation ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_report_snapshots_rls_isolation(db_engine, two_tenant_inspectors):
    t1_id, t2_id, i1_id, i2_id = two_tenant_inspectors
    insp1, insp2 = uuid.uuid4(), uuid.uuid4()
    snap1, snap2 = uuid.uuid4(), uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text(_insert_inspection_sql()),
            {
                "id": insp1, "tenant_id": t1_id, "inspector_id": i1_id,
                "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
                "property_address": "10 Test Ln, Tampa, FL 33601",
                "inspection_types": ["FULL_INSPECTION"],
                "total_fee": "150.00",
            },
        )
        await conn.execute(
            text(_insert_inspection_sql()),
            {
                "id": insp2, "tenant_id": t2_id, "inspector_id": i2_id,
                "scheduled_at": datetime(2026, 8, 16, 9, 0, tzinfo=timezone.utc),
                "property_address": "2 Beta Ave, Naples, FL 34101",
                "inspection_types": ["WIND_MITIGATION"],
                "total_fee": "200.00",
            },
        )
        await conn.execute(
            text("""
                INSERT INTO report_snapshots
                    (id, tenant_id, inspection_id, published_by, content_hash, snapshot_json)
                VALUES
                    (:s1, :t1, :insp1, :i1, :hash1, :snap1),
                    (:s2, :t2, :insp2, :i2, :hash2, :snap2)
            """),
            {
                "s1": snap1, "t1": t1_id, "insp1": insp1, "i1": i1_id,
                "hash1": "a" * 64, "snap1": '{"sections": []}',
                "s2": snap2, "t2": t2_id, "insp2": insp2, "i2": i2_id,
                "hash2": "b" * 64, "snap2": '{"sections": []}',
            },
        )

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1_id}'"))
        rows = (await conn.execute(text("SELECT id FROM report_snapshots"))).fetchall()
    assert [r.id for r in rows] == [snap1]

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2_id}'"))
        rows = (await conn.execute(text("SELECT id FROM report_snapshots"))).fetchall()
    assert [r.id for r in rows] == [snap2]

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        rows = (await conn.execute(text("SELECT id FROM report_snapshots"))).fetchall()
    assert rows == []

    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM report_snapshots WHERE id = ANY(:ids)"), {"ids": [snap1, snap2]})
        await conn.execute(text("DELETE FROM inspections WHERE id = ANY(:ids)"), {"ids": [insp1, insp2]})


# ── inspector_narrative_library: RLS isolation ──────────────────────────────


@pytest.mark.asyncio
async def test_inspector_narrative_library_rls_isolation(db_engine, two_tenant_inspectors):
    t1_id, t2_id, i1_id, i2_id = two_tenant_inspectors
    n1, n2 = uuid.uuid4(), uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO inspector_narrative_library
                    (id, tenant_id, inspector_id, system, trigger_keywords, narrative_text)
                VALUES
                    (:n1, :t1, :i1, 'electrical', ARRAY['double tap','double-tapped'],
                        'Double-tapped breaker observed at main panel.'),
                    (:n2, :t2, :i2, 'roof', ARRAY['granule loss'],
                        'Granule loss consistent with age of roof covering.')
            """),
            {"n1": n1, "t1": t1_id, "i1": i1_id, "n2": n2, "t2": t2_id, "i2": i2_id},
        )

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1_id}'"))
        rows = (await conn.execute(text("SELECT id, usage_count FROM inspector_narrative_library"))).fetchall()
    assert len(rows) == 1
    assert rows[0].id == n1
    assert rows[0].usage_count == 0

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2_id}'"))
        rows = (await conn.execute(text("SELECT id FROM inspector_narrative_library"))).fetchall()
    assert [r.id for r in rows] == [n2]

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        rows = (await conn.execute(text("SELECT id FROM inspector_narrative_library"))).fetchall()
    assert rows == []

    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM inspector_narrative_library WHERE id = ANY(:ids)"), {"ids": [n1, n2]})
