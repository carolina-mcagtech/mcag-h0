# tests/shared/test_rls_transaction_scope.py
import uuid

import pytest
from sqlalchemy import text

from app.shared.db.session import get_session_factory


@pytest.mark.asyncio
async def test_set_local_survives_flush(db_engine):
    """SET LOCAL must still be active after flush() — proves flush() does not commit."""
    tid = str(uuid.uuid4())

    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, 'FlushTest', 'flush-test')"),
            {"id": uuid.UUID(tid)},
        )

    try:
        guc_after_flush: str | None = None

        async with get_session_factory()() as session:
            async with session.begin():
                await session.execute(
                    text(f"SET LOCAL app.current_tenant_id = '{tid}'")
                )
                # flush() sends pending ORM state to DB but does NOT commit — stays in transaction
                await session.flush()
                result = await session.execute(
                    text("SELECT current_setting('app.current_tenant_id', true)")
                )
                guc_after_flush = result.scalar()

        assert guc_after_flush == tid, "SET LOCAL must survive flush() within session.begin()"
    finally:
        async with db_engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM tenants WHERE id = :id"), {"id": uuid.UUID(tid)}
            )


@pytest.mark.asyncio
async def test_inspector_b_cannot_read_inspector_a_data(db_engine):
    """Tenant B's session context must not return Tenant A's rows (RLS enforcement)."""
    tid_a = uuid.uuid4()
    tid_b = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain)
                VALUES (:a, 'Inspector A Co', 'inspa-rls'), (:b, 'Inspector B Co', 'inspb-rls')
            """),
            {"a": tid_a, "b": tid_b},
        )

    try:
        async with get_session_factory()() as session:
            async with session.begin():
                # Switch to app_role so RLS is enforced (superuser bypasses RLS by default)
                await session.execute(text("SET LOCAL ROLE app_role"))
                await session.execute(
                    text(f"SET LOCAL app.current_tenant_id = '{tid_b}'")
                )
                result = await session.execute(
                    text("SELECT id FROM tenants WHERE id = :target"),
                    {"target": tid_a},
                )
                rows = result.fetchall()

        assert len(rows) == 0, "Tenant B must not be able to read Tenant A's data"
    finally:
        async with db_engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM tenants WHERE id = ANY(:ids)"),
                {"ids": [tid_a, tid_b]},
            )
