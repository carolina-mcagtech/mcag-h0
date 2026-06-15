# tests/test_inspector_rls.py
import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import text


@pytest_asyncio.fixture
async def two_tenant_inspectors(db_engine):
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()
    i1_id = uuid.uuid4()
    i2_id = uuid.uuid4()

    # Insert as superuser so FORCE ROW LEVEL SECURITY is bypassed for setup.
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain, is_active)
                VALUES (:t1, 'Suncoast Inspections', 'suncoast', true),
                       (:t2, 'Gulf Coast Reports',   'gulfcoast', true)
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
                "i1": i1_id, "t1": t1_id, "sub1": uuid.uuid4(),
                "exp1": date(2027, 12, 31),
                "i2": i2_id, "t2": t2_id, "sub2": uuid.uuid4(),
                "exp2": date(2028, 6, 30),
            },
        )

    yield t1_id, t2_id, i1_id, i2_id

    # Clean up rows (child first to satisfy FK, then parent).
    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM inspector_profiles WHERE id = ANY(:ids)"),
            {"ids": [i1_id, i2_id]},
        )
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1_id, t2_id]},
        )


@pytest.mark.asyncio
async def test_inspector_rls_isolation(db_engine, two_tenant_inspectors):
    t1_id, t2_id, i1_id, i2_id = two_tenant_inspectors

    # ── Tenant 1 context: only Alice visible ────────────────────────────────
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1_id}'"))
        result = await conn.execute(text("SELECT id FROM inspector_profiles"))
        rows = result.fetchall()

    assert len(rows) == 1, f"Expected 1 row for tenant 1, got {len(rows)}"
    assert rows[0].id == i1_id

    # ── Tenant 2 context: only Bob visible ──────────────────────────────────
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t2_id}'"))
        result = await conn.execute(text("SELECT id FROM inspector_profiles"))
        rows = result.fetchall()

    assert len(rows) == 1, f"Expected 1 row for tenant 2, got {len(rows)}"
    assert rows[0].id == i2_id

    # ── No context → fail-closed, zero rows ─────────────────────────────────
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        result = await conn.execute(text("SELECT id FROM inspector_profiles"))
        rows = result.fetchall()

    assert len(rows) == 0, "Expected 0 rows when tenant context is unset"
