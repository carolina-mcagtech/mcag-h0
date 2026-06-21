# app/modules/observations/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspections.service import get_inspection
from app.modules.observations import service
from app.modules.observations.catalog import SECTION_CATALOG
from app.modules.observations.schemas import (
    ComponentObservationResponse,
    ComponentObservationUpsert,
    SectionMetadataResponse,
    SectionMetadataUpsert,
    SectionObservationsResponse,
)
from app.shared.db.session import get_session

router = APIRouter(
    prefix="/inspections/{inspection_id}/observations",
    tags=["observations"],
)


async def _ensure_inspection(inspection_id: uuid.UUID, session: AsyncSession) -> None:
    inspection = await get_inspection(inspection_id, session)
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")


@router.get("/catalog")
async def get_catalog() -> dict:
    return SECTION_CATALOG


@router.get("", response_model=dict[str, SectionObservationsResponse])
async def list_all_observations(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, SectionObservationsResponse]:
    await _ensure_inspection(inspection_id, session)
    return await service.list_all_observations(inspection_id, session)


@router.get("/{section}", response_model=SectionObservationsResponse)
async def get_section_observations(
    inspection_id: uuid.UUID,
    section: str,
    session: AsyncSession = Depends(get_session),
) -> SectionObservationsResponse:
    await _ensure_inspection(inspection_id, session)
    try:
        return await service.get_section_observations(inspection_id, section, session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{section}/metadata", response_model=SectionMetadataResponse)
async def upsert_section_metadata(
    inspection_id: uuid.UUID,
    section: str,
    payload: SectionMetadataUpsert,
    session: AsyncSession = Depends(get_session),
) -> SectionMetadataResponse:
    await _ensure_inspection(inspection_id, session)
    effective_payload = payload.model_copy(update={"section": section})
    try:
        meta = await service.upsert_section_metadata(
            inspection_id, effective_payload, session
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SectionMetadataResponse.model_validate(meta)


@router.put("/{section}/items/{item_key}", response_model=ComponentObservationResponse)
async def upsert_observation(
    inspection_id: uuid.UUID,
    section: str,
    item_key: str,
    payload: ComponentObservationUpsert,
    session: AsyncSession = Depends(get_session),
) -> ComponentObservationResponse:
    await _ensure_inspection(inspection_id, session)
    effective_payload = payload.model_copy(
        update={"section": section, "item_key": item_key}
    )
    try:
        obs = await service.upsert_observation(
            inspection_id, effective_payload, session
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ComponentObservationResponse.model_validate(obs)


@router.delete("/{section}/items/{observation_id}", status_code=204)
async def delete_observation(
    inspection_id: uuid.UUID,
    section: str,
    observation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    await _ensure_inspection(inspection_id, session)
    deleted = await service.delete_observation(observation_id, inspection_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="observation not found")
