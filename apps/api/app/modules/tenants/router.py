# app/modules/tenants/router.py
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.tenants import service
from app.modules.tenants.schemas import (
    SubdomainAssign,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)
from app.shared.auth.admin import admin_key_required
from app.shared.db.session import get_admin_session, get_session

router = APIRouter(prefix="/tenants", tags=["tenants"])

# /internal/* routes are gated by settings.internal_routes_enabled in main.py
# and are NEVER exposed to the public internet. See ADR-018.
internal_router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    _: None = Depends(admin_key_required),
    session: AsyncSession = Depends(get_admin_session),
) -> TenantResponse:
    try:
        tenant = await service.create_tenant(payload, session)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="subdomain already taken")
    return TenantResponse.model_validate(tenant)


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant(
    session: AsyncSession = Depends(get_session),
) -> TenantResponse:
    tenant = await service.get_tenant_by_id(session)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return TenantResponse.model_validate(tenant)


@router.put("/me/theme", response_model=TenantResponse)
async def update_theme(
    payload: TenantUpdate,
    session: AsyncSession = Depends(get_session),
) -> TenantResponse:
    if payload.theme_config is None:
        raise HTTPException(status_code=422, detail="theme_config is required")
    try:
        tenant = await service.update_theme(
            payload.theme_config.model_dump(exclude_none=True),
            session,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="tenant not found")
    return TenantResponse.model_validate(tenant)


@router.put("/me/subdomain", response_model=TenantResponse)
async def assign_subdomain(
    payload: SubdomainAssign,
    session: AsyncSession = Depends(get_session),
) -> TenantResponse:
    try:
        tenant = await service.assign_subdomain(payload.subdomain, session)
    except LookupError:
        raise HTTPException(status_code=404, detail="tenant not found")
    except IntegrityError:
        raise HTTPException(status_code=409, detail="subdomain already taken")
    return TenantResponse.model_validate(tenant)


@internal_router.get("/tenant-by-domain", response_model=TenantResponse)
async def get_tenant_by_domain(
    hostname: str = Query(...),
    x_internal_token: str = Header(...),
    session: AsyncSession = Depends(get_admin_session),
) -> TenantResponse:
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="invalid internal token")
    tenant = await service.get_tenant_by_custom_domain(hostname, session)
    if tenant is None:
        tenant = await service.get_tenant_by_subdomain(hostname, session)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return TenantResponse.model_validate(tenant)
