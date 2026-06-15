# app/modules/media/models.py
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base, TimestampMixin
from app.shared.db.mixins import TenantScopedMixin


class MediaAsset(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # No ForeignKey("inspections.id") here — deliberately, per ADR-025.
    # media and inspections are different modules; a declarative cross-module
    # string FK can raise NoReferencedTableError depending on import order.
    # DB-level FK (fk_media_assets_inspection_id, ON DELETE CASCADE) already
    # exists via migration 009.
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
