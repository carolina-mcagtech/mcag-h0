# app/modules/properties/service.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.properties.models import Property
from app.modules.properties.repository import PropertyRepository
from app.modules.properties.schemas import PropertyCreate, PropertyUpdate


async def create_property(data: PropertyCreate, session: AsyncSession) -> Property:
    """Insert a property. tenant_id is set from session.info by the repository."""
    prop = Property(**data.model_dump())
    await PropertyRepository(session).create(prop)
    await session.flush()
    await session.refresh(prop)
    return prop


async def get_property(
    property_id: uuid.UUID, session: AsyncSession
) -> Property | None:
    """Return a property by id. RLS limits results to the current tenant."""
    result = await session.execute(
        select(Property).where(Property.id == property_id)
    )
    return result.scalars().first()


async def list_properties(session: AsyncSession) -> list[Property]:
    """Return all properties visible to the current tenant via RLS."""
    result = await session.execute(select(Property))
    return list(result.scalars().all())


async def update_property(
    property_id: uuid.UUID, data: PropertyUpdate, session: AsyncSession
) -> Property | None:
    """Update provided fields. Returns None if the property is not found or
    belongs to a different tenant (RLS returns no rows)."""
    prop = await get_property(property_id, session)
    if prop is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prop, key, value)
    await session.flush()
    await session.refresh(prop)
    return prop
