# app/modules/agreements/schemas.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.modules.inspections.models import PaymentTimingEnum


class AgreementCreate(BaseModel):
    client_name: str
    property_address: str
    inspection_date: date
    fee_amount: Decimal
    payment_timing: PaymentTimingEnum
    # Optional — service defaults to fee_amount * 1.5 when omitted.
    liquidated_damages_amount: Decimal | None = None
    agreement_version: str = "InterNACHI-Feb-2019"
    signature_data_url: str | None = None


class AgreementUpdate(BaseModel):
    client_name: str | None = None
    property_address: str | None = None
    inspection_date: date | None = None
    fee_amount: Decimal | None = None
    payment_timing: PaymentTimingEnum | None = None
    liquidated_damages_amount: Decimal | None = None
    agreement_version: str | None = None
    signature_data_url: str | None = None


class AgreementSign(BaseModel):
    # Literal[True] forces the client to explicitly confirm both fields.
    # Pydantic returns 422 if either is False or absent.
    signed_by_client: Literal[True]
    exclusions_acknowledged: Literal[True]


class AgreementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    inspection_id: uuid.UUID
    client_name: str
    property_address: str
    inspection_date: date
    fee_amount: Decimal
    payment_timing: PaymentTimingEnum
    liquidated_damages_amount: Decimal
    agreement_version: str
    signed_by_client: bool
    signed_at: datetime | None
    signature_data_url: str | None
    exclusions_acknowledged: bool
    created_at: datetime
    updated_at: datetime
