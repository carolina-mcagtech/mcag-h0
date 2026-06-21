# app/modules/observations/schemas.py
import enum
import uuid

from pydantic import BaseModel, ConfigDict


class ComponentConditionEnum(str, enum.Enum):
    GOOD = "GOOD"
    MARGINAL = "MARGINAL"
    DEFECTIVE = "DEFECTIVE"
    N_A = "N_A"


class ComponentObservationUpsert(BaseModel):
    section: str
    item_key: str
    condition: ComponentConditionEnum
    observations: str | None = None
    room_index: int = 0
    room_label: str | None = None


class ComponentObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    section: str
    item_key: str
    item_label: str
    condition: ComponentConditionEnum
    observations: str | None
    room_type: str | None
    room_index: int
    room_label: str | None
    sort_order: int


class SectionMetadataUpsert(BaseModel):
    section: str
    data: dict


class SectionMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    section: str
    data: dict


class SectionObservationsResponse(BaseModel):
    section: str
    label: str
    catalog: dict
    metadata: dict
    observations: list[ComponentObservationResponse]
