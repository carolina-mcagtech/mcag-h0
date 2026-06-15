# app/modules/properties/models.py
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base, TimestampMixin
from app.shared.db.mixins import TenantScopedMixin


class Property(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Address ───────────────────────────────────────────────────────────────
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(
        String(2), nullable=False, default="FL", server_default="FL"
    )
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adjusted_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Insurance report — discrete columns (ADR-006) ─────────────────────────
    roof_permit_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    roof_permit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    roof_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    roof_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    water_heater_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    water_heater_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    water_heater_capacity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    electrical_brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    electrical_amps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    electrical_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ac_brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ac_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ac_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ac_series: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mit_doors_protection: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    mit_windows_protection: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # ── Insurance report — display-only JSONB (ADR-006) ───────────────────────
    appliances: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    bedrooms: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    bathrooms: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
