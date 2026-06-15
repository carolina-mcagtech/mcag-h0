# app/modules/properties/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.properties import service
from app.modules.properties.schemas import (
    PropertyCreate,
    PropertyResponse,
    PropertyUpdate,
)
from app.shared.db.session import get_session

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("", response_model=PropertyResponse, status_code=201)
async def create_property(
    payload: PropertyCreate,
    session: AsyncSession = Depends(get_session),
) -> PropertyResponse:
    prop = await service.create_property(payload, session)
    return PropertyResponse.model_validate(prop)


@router.get("", response_model=list[PropertyResponse])
async def list_properties(
    session: AsyncSession = Depends(get_session),
) -> list[PropertyResponse]:
    props = await service.list_properties(session)
    return [PropertyResponse.model_validate(p) for p in props]


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PropertyResponse:
    prop = await service.get_property(property_id, session)
    if prop is None:
        raise HTTPException(status_code=404, detail="property not found")
    return PropertyResponse.model_validate(prop)


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: uuid.UUID,
    payload: PropertyUpdate,
    session: AsyncSession = Depends(get_session),
) -> PropertyResponse:
    prop = await service.update_property(property_id, payload, session)
    if prop is None:
        raise HTTPException(status_code=404, detail="property not found")
    return PropertyResponse.model_validate(prop)
