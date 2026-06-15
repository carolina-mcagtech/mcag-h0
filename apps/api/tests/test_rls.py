# tests/test_rls.py
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text


@pytest_asyncio.fixture
async def two_tenants(db_engine):
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain, is_active)
                VALUES (:id1, 'Acme Inspections', 'acme', true),
                       (:id2, 'Gulf Coast Reports', 'gulfcoast', true)
            """),
            {"id1": t1_id, "id2": t2_id},
        )

    yield t1_id, t2_id

    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1_id, t2_id]},
        )


@pytest.mark.asyncio
async def test_tenant_sees_only_own_rows(db_engine, two_tenants):
    """Tenant context limits SELECT to rows owned by that tenant."""
    t1_id, _ = two_tenants

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1_id}'"))
        rows = (await conn.execute(text("SELECT id FROM tenants"))).fetchall()

    assert len(rows) == 1
    assert rows[0].id == t1_id


@pytest.mark.asyncio
async def test_cross_tenant_access_blocked(db_engine, two_tenants):
    """Tenant 1's JWT must not expose Tenant 2's rows."""
    t1_id, t2_id = two_tenants

    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        await conn.execute(text(f"SET LOCAL app.current_tenant_id = '{t1_id}'"))
        rows = (await conn.execute(text("SELECT id FROM tenants"))).fetchall()

    visible_ids = {r.id for r in rows}
    assert t2_id not in visible_ids, "Tenant 2 row must not be visible under tenant 1 context"


@pytest.mark.asyncio
async def test_no_context_fails_closed(db_engine, two_tenants):
    """Missing GUC → NULLIF evaluates to NULL → zero rows (fail-closed)."""
    async with db_engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE app_role"))
        # Intentionally omit SET LOCAL app.current_tenant_id
        rows = (await conn.execute(text("SELECT id FROM tenants"))).fetchall()

    assert len(rows) == 0, "RLS must return zero rows when tenant context is absent"
