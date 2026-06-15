# app/modules/agreements/models.py
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.inspections.models import PaymentTimingEnum
from app.shared.db.base import Base, TimestampMixin
from app.shared.db.mixins import TenantScopedMixin

# Re-export so callers can import PaymentTimingEnum from here without caring
# which module owns the canonical definition.
__all__ = ["Agreement", "PaymentTimingEnum"]


class Agreement(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "agreements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # No ForeignKey("inspections.id") here — deliberately, per ADR-025.
    # agreements and inspections are different modules; a declarative
    # cross-module string FK can raise NoReferencedTableError depending on
    # import order. DB-level FK (fk_agreements_inspection_id, ON DELETE
    # CASCADE) and the UNIQUE constraint (one agreement per inspection)
    # already exist via migration 006.
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
    )

    # ── Agreement body ────────────────────────────────────────────────────────
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    property_address: Mapped[str] = mapped_column(String(500), nullable=False)
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_timing: Mapped[PaymentTimingEnum] = mapped_column(
        # Reuses the payment_timing_enum type created by migration 005.
        String(20), nullable=False
    )
    # Defaults to fee_amount * 1.5 — calculated in service.create_agreement.
    liquidated_damages_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    agreement_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="InterNACHI-Feb-2019",
        server_default="InterNACHI-Feb-2019",
    )

    # ── Signature ─────────────────────────────────────────────────────────────
    signed_by_client: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Placeholder for the S3 URL set when the signed document is stored.
    signature_data_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    exclusions_acknowledged: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
