# app/shared/db/repository.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.db.mixins import TenantScopedMixin


class TenantScopedRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _get_tenant_id(self) -> uuid.UUID:
        tid = self._session.info.get("tenant_id")
        if tid is None:
            raise RuntimeError(
                "No tenant context: session.info['tenant_id'] is unset. "
                "Ensure the request goes through TenantMiddleware and get_session."
            )
        return tid

    async def create(self, obj: TenantScopedMixin) -> TenantScopedMixin:
        obj.tenant_id = self._get_tenant_id()
        self._session.add(obj)
        await self._session.flush()
        return obj
