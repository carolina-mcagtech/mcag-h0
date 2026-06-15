# app/modules/findings/service.py
import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.findings.models import Condition, Finding
from app.modules.findings.repository import FindingRepository
from app.modules.findings.schemas import FindingCreate, FindingUpdate


async def create_finding(
    inspection_id: uuid.UUID, data: FindingCreate, session: AsyncSession
) -> Finding:
    """Insert a finding scoped to inspection_id. tenant_id is set by FindingRepository.create()."""
    finding = Finding(inspection_id=inspection_id, **data.model_dump())
    await FindingRepository(session).create(finding)
    await session.refresh(finding)
    return finding


async def get_finding(
    inspection_id: uuid.UUID, finding_id: uuid.UUID, session: AsyncSession
) -> Finding | None:
    """Return a finding by id, scoped to inspection_id. RLS limits results to the current tenant."""
    result = await session.execute(
        select(Finding).where(
            Finding.id == finding_id, Finding.inspection_id == inspection_id
        )
    )
    return result.scalars().first()


async def list_findings_by_inspection(
    inspection_id: uuid.UUID, session: AsyncSession
) -> list[Finding]:
    result = await session.execute(
        select(Finding)
        .where(Finding.inspection_id == inspection_id)
        .order_by(Finding.section, Finding.sort_order)
    )
    return list(result.scalars().all())


async def update_finding(
    inspection_id: uuid.UUID,
    finding_id: uuid.UUID,
    data: FindingUpdate,
    session: AsyncSession,
) -> Finding | None:
    """Update provided fields. Returns None if not found or not part of this inspection/tenant."""
    finding = await get_finding(inspection_id, finding_id, session)
    if finding is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(finding, key, value)
    await session.flush()
    await session.refresh(finding)
    return finding


async def delete_finding(
    inspection_id: uuid.UUID, finding_id: uuid.UUID, session: AsyncSession
) -> bool:
    finding = await get_finding(inspection_id, finding_id, session)
    if finding is None:
        return False
    await session.delete(finding)
    await session.flush()
    return True


async def get_inspection_summary(
    inspection_id: uuid.UUID, session: AsyncSession
) -> dict[str, dict[str, int]]:
    result = await session.execute(
        select(Finding.section, Finding.condition)
        .where(Finding.inspection_id == inspection_id)
    )
    rows = result.all()

    summary: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "defective": 0})
    for section, condition in rows:
        key = section.value if hasattr(section, "value") else str(section)
        summary[key]["total"] += 1
        if condition == Condition.DEFECTIVE:
            summary[key]["defective"] += 1
    return dict(summary)
