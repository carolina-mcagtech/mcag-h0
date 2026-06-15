# app/modules/inspectors/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspectors import service
from app.modules.inspectors.schemas import InspectorProfileCreate, InspectorProfileResponse
from app.shared.auth.cognito import get_current_cognito_sub
from app.shared.db.session import get_session

router = APIRouter(prefix="/inspector-profiles", tags=["inspectors"])


@router.post("", response_model=InspectorProfileResponse, status_code=201)
async def create_inspector_profile(
    payload: InspectorProfileCreate,
    cognito_sub: uuid.UUID = Depends(get_current_cognito_sub),
    session: AsyncSession = Depends(get_session),
) -> InspectorProfileResponse:
    try:
        profile = await service.create_inspector_profile(payload, cognito_sub, session)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="inspector profile already exists for this user")
    return InspectorProfileResponse.model_validate(profile)


@router.get("/me", response_model=InspectorProfileResponse)
async def get_my_inspector_profile(
    cognito_sub: uuid.UUID = Depends(get_current_cognito_sub),
    session: AsyncSession = Depends(get_session),
) -> InspectorProfileResponse:
    profile = await service.get_my_inspector_profile(cognito_sub, session)
    if profile is None:
        raise HTTPException(status_code=404, detail="inspector profile not found")
    return InspectorProfileResponse.model_validate(profile)
