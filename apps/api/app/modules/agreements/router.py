# app/modules/agreements/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agreements import service
from app.modules.agreements.schemas import (
    AgreementCreate,
    AgreementResponse,
    AgreementSign,
    AgreementUpdate,
)
from app.modules.inspections.service import get_inspection
from app.shared.db.session import get_session

router = APIRouter(prefix="/inspections/{inspection_id}/agreements", tags=["agreements"])


async def _ensure_inspection(inspection_id: uuid.UUID, session: AsyncSession) -> None:
    """404 if the inspection doesn't exist or doesn't belong to the current tenant (RLS)."""
    inspection = await get_inspection(inspection_id, session)
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")


@router.post("", response_model=AgreementResponse, status_code=201)
async def create_agreement(
    inspection_id: uuid.UUID,
    payload: AgreementCreate,
    session: AsyncSession = Depends(get_session),
) -> AgreementResponse:
    await _ensure_inspection(inspection_id, session)
    try:
        agreement = await service.create_agreement(inspection_id, payload, session)
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="an agreement already exists for this inspection"
        )
    return AgreementResponse.model_validate(agreement)


@router.get("", response_model=list[AgreementResponse])
async def list_agreements(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[AgreementResponse]:
    await _ensure_inspection(inspection_id, session)
    agreements = await service.list_agreements_by_inspection(inspection_id, session)
    return [AgreementResponse.model_validate(a) for a in agreements]


@router.get("/{agreement_id}", response_model=AgreementResponse)
async def get_agreement(
    inspection_id: uuid.UUID,
    agreement_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AgreementResponse:
    await _ensure_inspection(inspection_id, session)
    agreement = await service.get_agreement(inspection_id, agreement_id, session)
    if agreement is None:
        raise HTTPException(status_code=404, detail="agreement not found")
    return AgreementResponse.model_validate(agreement)


@router.put("/{agreement_id}", response_model=AgreementResponse)
async def update_agreement(
    inspection_id: uuid.UUID,
    agreement_id: uuid.UUID,
    payload: AgreementUpdate,
    session: AsyncSession = Depends(get_session),
) -> AgreementResponse:
    await _ensure_inspection(inspection_id, session)
    agreement = await service.update_agreement(inspection_id, agreement_id, payload, session)
    if agreement is None:
        raise HTTPException(status_code=404, detail="agreement not found")
    return AgreementResponse.model_validate(agreement)


@router.post("/{agreement_id}/sign", response_model=AgreementResponse)
async def sign_agreement(
    inspection_id: uuid.UUID,
    agreement_id: uuid.UUID,
    payload: AgreementSign,
    session: AsyncSession = Depends(get_session),
) -> AgreementResponse:
    await _ensure_inspection(inspection_id, session)
    try:
        agreement = await service.sign_agreement(inspection_id, agreement_id, session)
    except LookupError:
        raise HTTPException(status_code=404, detail="agreement not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return AgreementResponse.model_validate(agreement)
