# app/modules/inspections/service.py
import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspections.models import (
    Inspection,
    InspectionStatusEnum,
    ReportSnapshot,
)
from app.modules.inspections.repository import InspectionRepository
from app.modules.inspections.schemas import (
    InspectionCreate,
    InspectionResponse,
    InspectionUpdate,
)

# ADR-024 D1 — strict FSM order. A transition is valid only if it advances the
# inspection exactly one step. PUBLISHED -> DELIVERED is the sole transition
# permitted out of PUBLISHED; every other field is write-locked once published.
_FSM_ORDER = (
    InspectionStatusEnum.DRAFT,
    InspectionStatusEnum.IN_FIELD,
    InspectionStatusEnum.PENDING_REVIEW,
    InspectionStatusEnum.PUBLISHED,
    InspectionStatusEnum.DELIVERED,
)

_LOCKED_STATUSES = frozenset(
    {InspectionStatusEnum.PUBLISHED, InspectionStatusEnum.DELIVERED}
)


class InspectionStatusTransitionError(ValueError):
    """Raised for invalid ADR-024 FSM transitions or writes to a locked inspection."""


async def create_inspection(data: InspectionCreate, session: AsyncSession) -> Inspection:
    """Insert an inspection. tenant_id is set by InspectionRepository.create()."""
    inspection = Inspection(**data.model_dump())
    await InspectionRepository(session).create(inspection)
    await session.flush()
    await session.refresh(inspection)
    return inspection


async def get_inspection(
    inspection_id: uuid.UUID, session: AsyncSession
) -> Inspection | None:
    """Return an inspection by id. RLS limits results to the current tenant."""
    result = await session.execute(
        select(Inspection).where(Inspection.id == inspection_id)
    )
    return result.scalars().first()


async def list_inspections(
    session: AsyncSession,
    status: InspectionStatusEnum | None = None,
) -> list[Inspection]:
    """Return inspections visible to the current tenant, optionally filtered by status."""
    q = select(Inspection)
    if status is not None:
        q = q.where(Inspection.status == status)
    result = await session.execute(q)
    return list(result.scalars().all())


async def update_inspection(
    inspection_id: uuid.UUID, data: InspectionUpdate, session: AsyncSession
) -> Inspection | None:
    """Update provided fields. Returns None if not found or belongs to another tenant.

    Raises InspectionStatusTransitionError if the inspection is PUBLISHED or
    DELIVERED — ADR-024 D1 write-locks those states; amendments require a new
    revision, not an in-place edit.
    """
    inspection = await get_inspection(inspection_id, session)
    if inspection is None:
        return None
    if inspection.status in _LOCKED_STATUSES:
        raise InspectionStatusTransitionError(
            f"Inspection is {inspection.status.value} and write-locked (ADR-024 D1); "
            "amendments require a new revision, not an in-place update."
        )
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(inspection, key, value)
    await session.flush()
    await session.refresh(inspection)
    return inspection


async def transition_status(
    inspection_id: uuid.UUID,
    new_status: InspectionStatusEnum,
    session: AsyncSession,
) -> Inspection | None:
    """Advance an inspection through the ADR-024 D1 FSM.

    DRAFT -> IN_FIELD -> PENDING_REVIEW -> PUBLISHED -> DELIVERED, one step at
    a time — no skipping, no going back. Transitioning to PUBLISHED creates an
    immutable ReportSnapshot (ADR-024 D4).
    """
    inspection = await get_inspection(inspection_id, session)
    if inspection is None:
        return None

    current_idx = _FSM_ORDER.index(inspection.status)
    try:
        new_idx = _FSM_ORDER.index(new_status)
    except ValueError:
        raise InspectionStatusTransitionError(f"Unknown status: {new_status!r}")

    if new_idx != current_idx + 1:
        raise InspectionStatusTransitionError(
            f"Cannot transition from {inspection.status.value} to {new_status.value}; "
            "the ADR-024 FSM only permits sequential progression "
            f"({' -> '.join(s.value for s in _FSM_ORDER)})."
        )

    inspection.status = new_status

    if new_status == InspectionStatusEnum.PUBLISHED:
        await _create_report_snapshot(inspection, session)

    await session.flush()
    await session.refresh(inspection)
    return inspection


async def _create_report_snapshot(
    inspection: Inspection, session: AsyncSession
) -> ReportSnapshot:
    """ADR-024 D4 — immutable snapshot of the inspection at publish time.

    The delivered PDF is generated from this snapshot, not the live
    inspection record, so a later edit cannot alter what was already
    published. Completeness checking is deferred to a future task.
    """
    snapshot_json = InspectionResponse.model_validate(inspection).model_dump(mode="json")
    content_hash = hashlib.sha256(
        json.dumps(snapshot_json, sort_keys=True).encode("utf-8")
    ).hexdigest()

    snapshot = ReportSnapshot(
        inspection_id=inspection.id,
        published_at=datetime.now(timezone.utc),
        published_by=inspection.inspector_id,
        content_hash=content_hash,
        snapshot_json=snapshot_json,
    )
    await InspectionRepository(session).create(snapshot)
    return snapshot
