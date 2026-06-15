# app/modules/reports/router.py
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.inspections.service import get_inspection
from app.modules.reports import service
from app.modules.reports.schemas import (
    ReportJobCreate,
    ReportJobResponse,
    ReportJobStatusUpdate,
)
from app.shared.db.session import get_session

router = APIRouter(prefix="/inspections/{inspection_id}/reports", tags=["reports"])


async def _ensure_inspection(inspection_id: uuid.UUID, session: AsyncSession) -> None:
    """404 if the inspection doesn't exist or doesn't belong to the current tenant (RLS)."""
    inspection = await get_inspection(inspection_id, session)
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")


@router.post("", response_model=ReportJobResponse, status_code=201)
async def create_report_job(
    inspection_id: uuid.UUID,
    payload: ReportJobCreate,
    session: AsyncSession = Depends(get_session),
) -> ReportJobResponse:
    await _ensure_inspection(inspection_id, session)
    try:
        job = await service.create_report_job(inspection_id, payload, session)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except IntegrityError as exc:
        orig = getattr(exc, "orig", None)
        pgcode = getattr(orig, "pgcode", None)
        if pgcode == "23505":
            raise HTTPException(
                status_code=409,
                detail="a report job already exists for this inspection and template",
            )
        raise HTTPException(status_code=422, detail="invalid inspection_id")
    return ReportJobResponse.model_validate(job)


@router.get("", response_model=list[ReportJobResponse])
async def list_report_jobs(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[ReportJobResponse]:
    await _ensure_inspection(inspection_id, session)
    jobs = await service.list_report_jobs_by_inspection(inspection_id, session)
    return [ReportJobResponse.model_validate(j) for j in jobs]


@router.get("/{report_id}", response_model=ReportJobResponse)
async def get_report_job(
    inspection_id: uuid.UUID,
    report_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ReportJobResponse:
    await _ensure_inspection(inspection_id, session)
    job = await service.get_report_job(inspection_id, report_id, session)
    if job is None:
        raise HTTPException(status_code=404, detail="report job not found")
    return ReportJobResponse.model_validate(job)


@router.post("/{report_id}/status", response_model=ReportJobResponse)
async def update_job_status(
    inspection_id: uuid.UUID,
    report_id: uuid.UUID,
    payload: ReportJobStatusUpdate,
    x_internal_token: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> ReportJobResponse:
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=403, detail="forbidden")
    await _ensure_inspection(inspection_id, session)
    job = await service.update_job_status(inspection_id, report_id, payload, session)
    if job is None:
        raise HTTPException(status_code=404, detail="report job not found")
    return ReportJobResponse.model_validate(job)
