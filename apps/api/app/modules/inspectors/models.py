# app/modules/inspectors/models.py
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base, TimestampMixin


class InspectorProfile(Base, TimestampMixin):
    __tablename__ = "inspector_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Stored in every row so the RLS policy can filter by it.
    # Application service code must never accept tenant_id as a function
    # argument — it is read from the session context variable instead.
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Cognito user sub — the only auth identifier we keep; no passwords stored.
    cognito_sub: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Florida DBPR home inspector license
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    license_expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
