# app/modules/properties/schemas.py
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PropertyCreate(BaseModel):
    street: str
    city: str
    state: str = "FL"
    zip_code: str
    year_built: int | None = None
    adjusted_sqft: int | None = None
    roof_permit_number: str | None = None
    roof_permit_date: date | None = None
    roof_style: str | None = None
    roof_type: str | None = None
    water_heater_type: str | None = None
    water_heater_location: str | None = None
    water_heater_capacity: str | None = None
    electrical_brand: str | None = None
    electrical_amps: int | None = None
    electrical_location: str | None = None
    ac_brand: str | None = None
    ac_age: int | None = None
    ac_model: str | None = None
    ac_series: str | None = None
    mit_doors_protection: bool | None = None
    mit_windows_protection: bool | None = None
    appliances: dict = {}
    bedrooms: dict = {}
    bathrooms: dict = {}


class PropertyUpdate(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    year_built: int | None = None
    adjusted_sqft: int | None = None
    roof_permit_number: str | None = None
    roof_permit_date: date | None = None
    roof_style: str | None = None
    roof_type: str | None = None
    water_heater_type: str | None = None
    water_heater_location: str | None = None
    water_heater_capacity: str | None = None
    electrical_brand: str | None = None
    electrical_amps: int | None = None
    electrical_location: str | None = None
    ac_brand: str | None = None
    ac_age: int | None = None
    ac_model: str | None = None
    ac_series: str | None = None
    mit_doors_protection: bool | None = None
    mit_windows_protection: bool | None = None
    appliances: dict | None = None
    bedrooms: dict | None = None
    bathrooms: dict | None = None


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    street: str
    city: str
    state: str
    zip_code: str
    year_built: int | None
    adjusted_sqft: int | None
    roof_permit_number: str | None
    roof_permit_date: date | None
    roof_style: str | None
    roof_type: str | None
    water_heater_type: str | None
    water_heater_location: str | None
    water_heater_capacity: str | None
    electrical_brand: str | None
    electrical_amps: int | None
    electrical_location: str | None
    ac_brand: str | None
    ac_age: int | None
    ac_model: str | None
    ac_series: str | None
    mit_doors_protection: bool | None
    mit_windows_protection: bool | None
    appliances: dict
    bedrooms: dict
    bathrooms: dict
    created_at: datetime
    updated_at: datetime
