# app/modules/agreements/service.py
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agreements.models import Agreement
from app.modules.agreements.repository import AgreementRepository
from app.modules.agreements.schemas import AgreementCreate, AgreementUpdate


async def create_agreement(
    inspection_id: uuid.UUID, data: AgreementCreate, session: AsyncSession
) -> Agreement:
    """Insert an agreement scoped to inspection_id. tenant_id is set by
    AgreementRepository.create(). liquidated_damages_amount defaults to
    fee_amount * 1.5 when not provided."""
    payload = data.model_dump()
    if payload["liquidated_damages_amount"] is None:
        payload["liquidated_damages_amount"] = payload["fee_amount"] * Decimal("1.5")
    agreement = Agreement(inspection_id=inspection_id, **payload)
    await AgreementRepository(session).create(agreement)
    await session.refresh(agreement)
    return agreement


async def get_agreement(
    inspection_id: uuid.UUID, agreement_id: uuid.UUID, session: AsyncSession
) -> Agreement | None:
    """Return an agreement by id, scoped to inspection_id. RLS limits results to the current tenant."""
    result = await session.execute(
        select(Agreement).where(
            Agreement.id == agreement_id, Agreement.inspection_id == inspection_id
        )
    )
    return result.scalars().first()


async def list_agreements_by_inspection(
    inspection_id: uuid.UUID, session: AsyncSession
) -> list[Agreement]:
    result = await session.execute(
        select(Agreement).where(Agreement.inspection_id == inspection_id)
    )
    return list(result.scalars().all())


async def update_agreement(
    inspection_id: uuid.UUID,
    agreement_id: uuid.UUID,
    data: AgreementUpdate,
    session: AsyncSession,
) -> Agreement | None:
    """Update provided fields. Returns None if not found or not part of this inspection/tenant."""
    agreement = await get_agreement(inspection_id, agreement_id, session)
    if agreement is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(agreement, key, value)
    await session.flush()
    await session.refresh(agreement)
    return agreement


async def sign_agreement(
    inspection_id: uuid.UUID, agreement_id: uuid.UUID, session: AsyncSession
) -> Agreement:
    """Mark the agreement as signed. Raises LookupError if not found,
    ValueError if already signed."""
    agreement = await get_agreement(inspection_id, agreement_id, session)
    if agreement is None:
        raise LookupError("agreement not found")
    if agreement.signed_by_client:
        raise ValueError("agreement already signed")
    agreement.signed_by_client = True
    agreement.exclusions_acknowledged = True
    agreement.signed_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(agreement)
    return agreement
