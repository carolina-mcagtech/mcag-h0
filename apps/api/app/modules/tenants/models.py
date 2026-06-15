# app/modules/tenants/models.py
import enum
import uuid

from sqlalchemy import Boolean, CheckConstraint, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base, TimestampMixin


class PlanEnum(str, enum.Enum):
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    AGENCY = "AGENCY"


class CustomDomainStatusEnum(str, enum.Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PENDING_CERT = "PENDING_CERT"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            r"subdomain ~ '^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$'",
            name="ck_tenants_subdomain_format",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    custom_domain: Mapped[str | None] = mapped_column(String(253), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    plan: Mapped[PlanEnum] = mapped_column(
        SAEnum(PlanEnum, name="plan_enum", create_type=False),
        nullable=False,
        default=PlanEnum.STARTER,
        server_default="STARTER",
    )
    custom_domain_status: Mapped[CustomDomainStatusEnum | None] = mapped_column(
        SAEnum(CustomDomainStatusEnum, name="custom_domain_status_enum", create_type=False),
        nullable=True,
    )
    theme_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
