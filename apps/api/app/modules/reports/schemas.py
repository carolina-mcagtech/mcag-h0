# app/modules/reports/schemas.py
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.reports.models import ReportJobStatus, ReportTemplate


class ReportJobCreate(BaseModel):
    template: ReportTemplate


class ReportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    inspection_id: uuid.UUID
    template: ReportTemplate
    status: ReportJobStatus
    template_version: str
    s3_url: str | None
    generated_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ReportJobStatusUpdate(BaseModel):
    status: ReportJobStatus
    s3_url: str | None = None
    error_message: str | None = None
