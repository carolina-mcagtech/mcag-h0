# tests/test_inspections_service.py
"""Service-layer tests for the ADR-024 inspections module (Tarea 3).

Covers create/get/list/update plus the transition_status FSM and the
PUBLISHED write-lock + ReportSnapshot creation (ADR-024 D1/D4).
"""
import uuid
from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.modules.inspections import service
from app.modules.inspections.models import (
    InspectionStatusEnum,
    InspectionTypeEnum,
    ReportSnapshot,
)
from app.modules.inspections.schemas import InspectionCreate, InspectionUpdate
from app.modules.inspections.service import InspectionStatusTransitionError


@pytest_asyncio.fixture
async def session_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def tenant(db_engine):
    tid = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name, subdomain) VALUES (:id, 'Svc Test Tenant', 'svctesttenant')"),
            {"id": tid},
        )
    yield tid
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM tenants WHERE id = :id"), {"id": tid})


@pytest_asyncio.fixture
async def inspector(db_engine, tenant):
    insp_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES (:id, :tid, :sub, 'Svc Inspector', 'inspector@svctesttenant.com', 'HI00098', '2028-01-01')
            """),
            {"id": insp_id, "tid": tenant, "sub": uuid.uuid4()},
        )
    yield insp_id


def _create_payload(inspector_id: uuid.UUID, **overrides) -> InspectionCreate:
    return InspectionCreate(**{
        "inspector_id": inspector_id,
        "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
        "property_address": "10 Service Ln, Tampa, FL 33601",
        "inspection_types": ["FULL_INSPECTION"],
        "total_fee": "150.00",
        **overrides,
    })


# ── create / get / list ──────────────────────────────────────────────────────


async def test_create_inspection_defaults_to_draft(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        await session.commit()

    assert inspection.tenant_id == tenant
    assert inspection.status == InspectionStatusEnum.DRAFT
    assert inspection.inspection_types == [InspectionTypeEnum.FULL_INSPECTION]


async def test_get_inspection_returns_none_for_unknown_id(session_factory, tenant):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        result = await service.get_inspection(uuid.uuid4(), session)

    assert result is None


async def test_list_inspections_filters_by_status(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        i1 = await service.create_inspection(_create_payload(inspector), session)
        i2 = await service.create_inspection(_create_payload(inspector), session)
        await service.transition_status(i2.id, InspectionStatusEnum.IN_FIELD, session)
        await session.commit()

        all_inspections = await service.list_inspections(session)
        draft_only = await service.list_inspections(session, status=InspectionStatusEnum.DRAFT)
        in_field_only = await service.list_inspections(session, status=InspectionStatusEnum.IN_FIELD)

    assert {i.id for i in all_inspections} >= {i1.id, i2.id}
    assert i1.id in {i.id for i in draft_only}
    assert i2.id not in {i.id for i in draft_only}
    assert {i.id for i in in_field_only} == {i2.id}


# ── update_inspection ─────────────────────────────────────────────────────────


async def test_update_inspection_applies_partial_fields(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        await session.commit()

        updated = await service.update_inspection(
            inspection.id, InspectionUpdate(gate_code="9999", total_fee="175.50"), session
        )
        await session.commit()

    assert updated.gate_code == "9999"
    assert str(updated.total_fee) == "175.50"


async def test_update_inspection_returns_none_for_unknown_id(session_factory, tenant):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        result = await service.update_inspection(uuid.uuid4(), InspectionUpdate(gate_code="1"), session)

    assert result is None


# ── transition_status: FSM sequencing ────────────────────────────────────────


async def test_transition_status_full_fsm_sequence(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        await session.commit()

        for expected in (
            InspectionStatusEnum.IN_FIELD,
            InspectionStatusEnum.PENDING_REVIEW,
            InspectionStatusEnum.PUBLISHED,
            InspectionStatusEnum.DELIVERED,
        ):
            updated = await service.transition_status(inspection.id, expected, session)
            await session.commit()
            assert updated.status == expected


async def test_transition_status_rejects_skipping_a_state(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        await session.commit()
        inspection_id = inspection.id

        # DRAFT -> PENDING_REVIEW skips IN_FIELD.
        try:
            await service.transition_status(inspection_id, InspectionStatusEnum.PENDING_REVIEW, session)
            assert False, "expected InspectionStatusTransitionError"
        except InspectionStatusTransitionError:
            pass
        await session.rollback()

    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        result = await service.get_inspection(inspection_id, session)
    assert result.status == InspectionStatusEnum.DRAFT


async def test_transition_status_rejects_going_backwards(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        await service.transition_status(inspection.id, InspectionStatusEnum.IN_FIELD, session)
        await session.commit()

        try:
            await service.transition_status(inspection.id, InspectionStatusEnum.DRAFT, session)
            assert False, "expected InspectionStatusTransitionError"
        except InspectionStatusTransitionError:
            pass


async def test_transition_status_rejects_from_delivered(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        for status in (
            InspectionStatusEnum.IN_FIELD,
            InspectionStatusEnum.PENDING_REVIEW,
            InspectionStatusEnum.PUBLISHED,
            InspectionStatusEnum.DELIVERED,
        ):
            await service.transition_status(inspection.id, status, session)
        await session.commit()

        try:
            await service.transition_status(inspection.id, InspectionStatusEnum.DELIVERED, session)
            assert False, "expected InspectionStatusTransitionError"
        except InspectionStatusTransitionError:
            pass


# ── PUBLISHED write-lock + ReportSnapshot (ADR-024 D1/D4) ────────────────────


async def test_update_inspection_rejected_once_published(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        for status in (
            InspectionStatusEnum.IN_FIELD,
            InspectionStatusEnum.PENDING_REVIEW,
            InspectionStatusEnum.PUBLISHED,
        ):
            await service.transition_status(inspection.id, status, session)
        await session.commit()

        try:
            await service.update_inspection(inspection.id, InspectionUpdate(gate_code="0000"), session)
            assert False, "expected InspectionStatusTransitionError"
        except InspectionStatusTransitionError:
            pass


async def test_transition_status_rejects_in_place_edit_attempt_via_published_to_in_field(
    session_factory, tenant, inspector
):
    """Once PUBLISHED, the only forward transition is to DELIVERED — anything
    else (including attempting to move back into the field) is rejected."""
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        for status in (
            InspectionStatusEnum.IN_FIELD,
            InspectionStatusEnum.PENDING_REVIEW,
            InspectionStatusEnum.PUBLISHED,
        ):
            await service.transition_status(inspection.id, status, session)
        await session.commit()

        try:
            await service.transition_status(inspection.id, InspectionStatusEnum.IN_FIELD, session)
            assert False, "expected InspectionStatusTransitionError"
        except InspectionStatusTransitionError:
            pass


async def test_publish_creates_report_snapshot(session_factory, tenant, inspector):
    async with session_factory() as session:
        session.info["tenant_id"] = tenant
        inspection = await service.create_inspection(_create_payload(inspector), session)
        for status in (InspectionStatusEnum.IN_FIELD, InspectionStatusEnum.PENDING_REVIEW):
            await service.transition_status(inspection.id, status, session)
        await service.transition_status(inspection.id, InspectionStatusEnum.PUBLISHED, session)
        await session.commit()

        result = await session.execute(
            select(ReportSnapshot).where(ReportSnapshot.inspection_id == inspection.id)
        )
        snapshot = result.scalars().one()

    assert snapshot.tenant_id == tenant
    assert snapshot.published_by == inspector
    assert len(snapshot.content_hash) == 64
    assert snapshot.snapshot_json["status"] == "PUBLISHED"
    assert snapshot.snapshot_json["id"] == str(inspection.id)
