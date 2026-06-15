# app/modules/inspectors/schemas.py
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class InspectorProfileCreate(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    license_number: str
    license_expiry_date: date


class InspectorProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    cognito_sub: uuid.UUID
    full_name: str
    email: str
    phone: str | None
    license_number: str
    license_expiry_date: date
    created_at: datetime
    updated_at: datetime
