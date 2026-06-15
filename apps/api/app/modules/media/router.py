# app/modules/media/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.media import service
from app.modules.media.schemas import MediaAssetCreate, MediaAssetResponse
from app.modules.inspections.service import get_inspection
from app.shared.db.session import get_session

router = APIRouter(prefix="/inspections/{inspection_id}/media", tags=["media"])


async def _ensure_inspection(inspection_id: uuid.UUID, session: AsyncSession) -> None:
    """404 if the inspection doesn't exist or doesn't belong to the current tenant (RLS)."""
    inspection = await get_inspection(inspection_id, session)
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")


@router.post("", response_model=MediaAssetResponse, status_code=201)
async def create_media(
    inspection_id: uuid.UUID,
    payload: MediaAssetCreate,
    session: AsyncSession = Depends(get_session),
) -> MediaAssetResponse:
    await _ensure_inspection(inspection_id, session)
    media = await service.create_media(inspection_id, payload, session)
    return MediaAssetResponse.model_validate(media)


@router.get("", response_model=list[MediaAssetResponse])
async def list_media(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[MediaAssetResponse]:
    await _ensure_inspection(inspection_id, session)
    media = await service.list_media_by_inspection(inspection_id, session)
    return [MediaAssetResponse.model_validate(m) for m in media]


@router.get("/{media_id}", response_model=MediaAssetResponse)
async def get_media(
    inspection_id: uuid.UUID,
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> MediaAssetResponse:
    await _ensure_inspection(inspection_id, session)
    media = await service.get_media(inspection_id, media_id, session)
    if media is None:
        raise HTTPException(status_code=404, detail="media asset not found")
    return MediaAssetResponse.model_validate(media)


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    inspection_id: uuid.UUID,
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    await _ensure_inspection(inspection_id, session)
    deleted = await service.delete_media(inspection_id, media_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="media asset not found")
