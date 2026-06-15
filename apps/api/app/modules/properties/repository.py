# app/modules/properties/repository.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.properties.models import Property
from app.shared.db.repository import TenantScopedRepository


class PropertyRepository(TenantScopedRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
