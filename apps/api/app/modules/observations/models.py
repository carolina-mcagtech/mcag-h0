# app/modules/observations/models.py
import enum
import uuid

from sqlalchemy import SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base, TimestampMixin
from app.shared.db.mixins import TenantScopedMixin


class ComponentCondition(str, enum.Enum):
    GOOD = "GOOD"
    MARGINAL = "MARGINAL"
    DEFECTIVE = "DEFECTIVE"
    N_A = "N_A"


class ComponentObservation(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "component_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # No ForeignKey("inspections.id") — cross-module, per ADR-025.
    # DB-level FK (fk_co_inspection_id, ON DELETE CASCADE) exists via migration 012.
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(Text, nullable=False)
    item_key: Mapped[str] = mapped_column(Text, nullable=False)
    item_label: Mapped[str] = mapped_column(Text, nullable=False)
    # VARCHAR(20) + CHECK constraint (no custom ENUM type — avoids DDL privilege requirement)
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    room_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    room_index: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    room_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )


class SectionMetadata(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "section_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # No ForeignKey("inspections.id") — cross-module, per ADR-025.
    # DB-level FK (fk_sm_inspection_id, ON DELETE CASCADE) exists via migration 012.
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
