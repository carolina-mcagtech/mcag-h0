# app/modules/tenants/schemas.py
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.tenants.models import CustomDomainStatusEnum, PlanEnum

_SUBDOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")


def _validate_subdomain(v: str) -> str:
    if not _SUBDOMAIN_RE.match(v):
        raise ValueError(
            "subdomain must be 3–63 characters, lowercase alphanumeric or hyphens, "
            "no leading or trailing hyphens"
        )
    return v


class ThemeConfig(BaseModel):
    primary_color: str | None = None
    logo_url: str | None = None
    brand_name: str | None = None
    license_number: str | None = None
    inspector_name: str | None = None
    phone: str | None = None
    website: str | None = None
    font_family: str | None = None
    email: str | None = None
    mold_license: str | None = None
    nachi_license: str | None = None


class TenantCreate(BaseModel):
    name: str
    subdomain: str

    @field_validator("subdomain")
    @classmethod
    def subdomain_format(cls, v: str) -> str:
        return _validate_subdomain(v)


class TenantUpdate(BaseModel):
    theme_config: ThemeConfig | None = None
    custom_domain: str | None = None


class SubdomainAssign(BaseModel):
    subdomain: str

    @field_validator("subdomain")
    @classmethod
    def subdomain_format(cls, v: str) -> str:
        return _validate_subdomain(v)


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    subdomain: str
    custom_domain: str | None
    is_active: bool
    plan: PlanEnum
    custom_domain_status: CustomDomainStatusEnum | None
    theme_config: dict
    created_at: datetime
    updated_at: datetime
