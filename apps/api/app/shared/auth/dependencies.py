# app/shared/auth/dependencies.py
import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspectors.models import InspectorProfile
from app.shared.auth.cognito import get_current_cognito_sub
from app.shared.db.session import get_session


async def get_current_inspector(
    cognito_sub: uuid.UUID = Depends(get_current_cognito_sub),
    session: AsyncSession = Depends(get_session),
) -> InspectorProfile:
    result = await session.execute(
        select(InspectorProfile).where(InspectorProfile.cognito_sub == cognito_sub)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Inspector profile not found for this user",
        )
    return profile
