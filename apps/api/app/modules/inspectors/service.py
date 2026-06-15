# app/modules/inspectors/service.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspectors.models import InspectorProfile
from app.modules.inspectors.repository import InspectorProfileRepository
from app.modules.inspectors.schemas import InspectorProfileCreate


async def create_inspector_profile(
    data: InspectorProfileCreate, cognito_sub: uuid.UUID, session: AsyncSession
) -> InspectorProfile:
    """Create the calling inspector's own profile.

    id is set to cognito_sub so the row satisfies fk_inspections_inspector_id
    when this id is later used as inspections.inspector_id. tenant_id is set
    from session.info by the repository.
    """
    profile = InspectorProfile(
        id=cognito_sub,
        cognito_sub=cognito_sub,
        **data.model_dump(),
    )
    await InspectorProfileRepository(session).create(profile)
    await session.flush()
    await session.refresh(profile)
    return profile


async def get_my_inspector_profile(
    cognito_sub: uuid.UUID, session: AsyncSession
) -> InspectorProfile | None:
    """Return the calling inspector's profile. RLS limits results to the
    current tenant; cognito_sub further limits to the current user."""
    result = await session.execute(
        select(InspectorProfile).where(InspectorProfile.cognito_sub == cognito_sub)
    )
    return result.scalars().first()
