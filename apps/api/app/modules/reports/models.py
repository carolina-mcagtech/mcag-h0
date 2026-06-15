# app/modules/reports/models.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base, TimestampMixin
from app.shared.db.mixins import TenantScopedMixin


class ReportTemplate(str, enum.Enum):
    FULL = "FULL"
    INSURANCE = "INSURANCE"


class ReportJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ReportJob(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "report_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # No ForeignKey("inspections.id") here — deliberately, per ADR-025.
    # reports and inspections are different modules; a declarative cross-module
    # string FK can raise NoReferencedTableError depending on import order.
    # DB-level FK (fk_report_jobs_inspection_id, ON DELETE CASCADE) already
    # exists via migration 008.
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    template: Mapped[ReportTemplate] = mapped_column(
        SAEnum(ReportTemplate, name="report_template_enum", create_type=False),
        nullable=False,
    )
    status: Mapped[ReportJobStatus] = mapped_column(
        SAEnum(ReportJobStatus, name="report_job_status_enum", create_type=False),
        nullable=False,
        default=ReportJobStatus.PENDING,
        server_default="PENDING",
    )
    template_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="v1.0", server_default="v1.0"
    )
    s3_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
