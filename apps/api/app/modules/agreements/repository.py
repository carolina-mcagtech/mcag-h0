# app/modules/agreements/repository.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.db.repository import TenantScopedRepository


class AgreementRepository(TenantScopedRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
