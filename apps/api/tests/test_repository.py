# tests/test_repository.py
#
# Unit tests for TenantScopedRepository and PropertyRepository (ADR-020).
# These tests exercise the Python-layer tenant_id injection, independent of
# the HTTP stack.

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.modules.inspections.models import Inspection, InspectionTypeEnum
from app.modules.inspections.repository import InspectionRepository
from app.modules.properties.models import Property
from app.modules.properties.repository import PropertyRepository
from app.shared.db.repository import TenantScopedRepository


@pytest_asyncio.fixture
async def session_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def tenant(db_engine):
    tid = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenants (id, name, subdomain) "
                "VALUES (:id, 'Repo Test Tenant', 'repotestenant')"
            ),
            {"id": tid},
        )
    yield tid
    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = :id"), {"id": tid}
        )


# ── Test 1: create() sets tenant_id from session.info ────────────────────────


async def test_repo_create_sets_tenant_id(session_factory, tenant):
    """repo.create() with session.info['tenant_id'] set produces the correct row."""
    prop = Property(street="1 Repo St", city="Miami", zip_code="33101")

    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        repo = PropertyRepository(session)
        await repo.create(prop)
        await session.commit()

    assert prop.tenant_id == tenant


# ── Test 2: create() without tenant_id raises RuntimeError ───────────────────


async def test_repo_create_raises_without_tenant_id(session_factory, tenant):
    """repo.create() raises RuntimeError when session.info has no tenant_id."""
    prop = Property(street="2 Repo St", city="Orlando", zip_code="32801")

    async with session_factory() as session:
        # Deliberately do NOT set session.info["tenant_id"]
        repo = PropertyRepository(session)
        with pytest.raises(RuntimeError, match="tenant"):
            await repo.create(prop)


# ── InspectionRepository (ADR-024) ────────────────────────────────────────────


@pytest_asyncio.fixture
async def inspector(db_engine, tenant):
    insp_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES (:id, :tid, :sub, 'Repo Inspector', 'inspector@repotestenant.com', 'HI00099', '2028-01-01')
            """),
            {"id": insp_id, "tid": tenant, "sub": uuid.uuid4()},
        )
    yield insp_id


async def test_inspection_repo_create_sets_tenant_id(session_factory, tenant, inspector):
    """InspectionRepository.create() sets tenant_id from session.info."""
    inspection = Inspection(
        inspector_id=inspector,
        scheduled_at=datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
        property_address="1 Repo St, Miami, FL 33101",
        inspection_types=[InspectionTypeEnum.FULL_INSPECTION],
        total_fee="150.00",
    )

    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        repo = InspectionRepository(session)
        await repo.create(inspection)
        await session.commit()

    assert inspection.tenant_id == tenant


async def test_inspection_repo_create_raises_without_tenant_id(session_factory, tenant, inspector):
    """InspectionRepository.create() raises RuntimeError when session.info has no tenant_id."""
    inspection = Inspection(
        inspector_id=inspector,
        scheduled_at=datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
        property_address="2 Repo St, Orlando, FL 32801",
        inspection_types=[InspectionTypeEnum.FULL_INSPECTION],
        total_fee="150.00",
    )

    async with session_factory() as session:
        repo = InspectionRepository(session)
        with pytest.raises(RuntimeError, match="tenant"):
            await repo.create(inspection)
