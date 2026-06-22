# app/modules/inspections/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspections import service
from app.modules.inspections.models import InspectionStatusEnum
from app.modules.inspections.schemas import (
    InspectionCreate,
    InspectionListResponse,
    InspectionResponse,
    InspectionStatusTransition,
    InspectionUpdate,
)
from app.modules.inspections.service import InspectionStatusTransitionError
from app.shared.db.session import get_session

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.post("", response_model=InspectionResponse, status_code=201)
async def create_inspection(
    payload: InspectionCreate,
    session: AsyncSession = Depends(get_session),
) -> InspectionResponse:
    try:
        inspection = await service.create_inspection(payload, session)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="report number already exists for this tenant")
    return InspectionResponse.model_validate(inspection)


@router.get("", response_model=list[InspectionListResponse])
async def list_inspections(
    status: InspectionStatusEnum | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[InspectionListResponse]:
    inspections = await service.list_inspections(session, status=status)
    return [InspectionListResponse.model_validate(i) for i in inspections]


@router.get("/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> InspectionResponse:
    inspection = await service.get_inspection(inspection_id, session)
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")
    return InspectionResponse.model_validate(inspection)


@router.put("/{inspection_id}", response_model=InspectionResponse)
async def update_inspection(
    inspection_id: uuid.UUID,
    payload: InspectionUpdate,
    session: AsyncSession = Depends(get_session),
) -> InspectionResponse:
    try:
        inspection = await service.update_inspection(inspection_id, payload, session)
    except InspectionStatusTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="report number already exists for this tenant")
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")
    return InspectionResponse.model_validate(inspection)


@router.delete("/{inspection_id}", status_code=204)
async def delete_inspection(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await service.delete_inspection(inspection_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="inspection not found")


@router.post("/{inspection_id}/transition", response_model=InspectionResponse)
async def transition_inspection_status(
    inspection_id: uuid.UUID,
    payload: InspectionStatusTransition,
    session: AsyncSession = Depends(get_session),
) -> InspectionResponse:
    try:
        inspection = await service.transition_status(inspection_id, payload.status, session)
    except InspectionStatusTransitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")
    return InspectionResponse.model_validate(inspection)
