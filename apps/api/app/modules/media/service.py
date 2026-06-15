# app/modules/media/service.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.media.models import MediaAsset
from app.modules.media.repository import MediaRepository
from app.modules.media.schemas import MediaAssetCreate


async def create_media(
    inspection_id: uuid.UUID, data: MediaAssetCreate, session: AsyncSession
) -> MediaAsset:
    """Insert a media asset scoped to inspection_id. tenant_id is set by MediaRepository.create()."""
    media = MediaAsset(inspection_id=inspection_id, **data.model_dump())
    await MediaRepository(session).create(media)
    await session.refresh(media)
    return media


async def get_media(
    inspection_id: uuid.UUID, media_id: uuid.UUID, session: AsyncSession
) -> MediaAsset | None:
    """Return a media asset by id, scoped to inspection_id. RLS limits results to the current tenant."""
    result = await session.execute(
        select(MediaAsset).where(
            MediaAsset.id == media_id, MediaAsset.inspection_id == inspection_id
        )
    )
    return result.scalars().first()


async def list_media_by_inspection(
    inspection_id: uuid.UUID, session: AsyncSession
) -> list[MediaAsset]:
    result = await session.execute(
        select(MediaAsset)
        .where(MediaAsset.inspection_id == inspection_id)
        .order_by(MediaAsset.created_at)
    )
    return list(result.scalars().all())


async def delete_media(
    inspection_id: uuid.UUID, media_id: uuid.UUID, session: AsyncSession
) -> bool:
    media = await get_media(inspection_id, media_id, session)
    if media is None:
        return False
    await session.delete(media)
    await session.flush()
    return True
