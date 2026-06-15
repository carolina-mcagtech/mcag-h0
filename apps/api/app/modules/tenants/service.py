# app/modules/tenants/service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.modules.tenants.schemas import TenantCreate


async def create_tenant(payload: TenantCreate, session: AsyncSession) -> Tenant:
    """Insert a new tenant. Raises IntegrityError on duplicate subdomain."""
    tenant = Tenant(name=payload.name, subdomain=payload.subdomain)
    session.add(tenant)
    await session.flush()
    await session.refresh(tenant)
    return tenant


async def get_tenant_by_id(session: AsyncSession) -> Tenant | None:
    """Return the current tenant via RLS context. Returns None if no context is set."""
    result = await session.execute(select(Tenant))
    return result.scalars().first()


async def get_tenant_by_subdomain(subdomain: str, session: AsyncSession) -> Tenant | None:
    """Lookup by subdomain without RLS. Requires an admin session from the caller."""
    result = await session.execute(
        select(Tenant).where(Tenant.subdomain == subdomain)
    )
    return result.scalars().first()


async def get_tenant_by_custom_domain(domain: str, session: AsyncSession) -> Tenant | None:
    """Lookup by custom_domain without RLS. Requires an admin session from the caller."""
    result = await session.execute(
        select(Tenant).where(Tenant.custom_domain == domain)
    )
    return result.scalars().first()


async def update_theme(theme_config: dict, session: AsyncSession) -> Tenant:
    """Replace theme_config for the current tenant. Raises LookupError if no tenant in context."""
    tenant = await get_tenant_by_id(session)
    if tenant is None:
        raise LookupError("tenant not found")
    tenant.theme_config = theme_config
    await session.flush()
    await session.refresh(tenant)
    return tenant


async def assign_subdomain(subdomain: str, session: AsyncSession) -> Tenant:
    """Update subdomain for the current tenant. Raises LookupError or IntegrityError."""
    tenant = await get_tenant_by_id(session)
    if tenant is None:
        raise LookupError("tenant not found")
    tenant.subdomain = subdomain
    await session.flush()
    await session.refresh(tenant)
    return tenant
