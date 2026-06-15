# app/modules/media/schemas.py
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaAssetCreate(BaseModel):
    filename: str
    content_type: str
    s3_key: str
    s3_bucket: str


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    inspection_id: uuid.UUID
    filename: str
    content_type: str
    s3_key: str
    s3_bucket: str
    created_at: datetime
    updated_at: datetime
