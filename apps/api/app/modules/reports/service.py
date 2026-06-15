# app/modules/reports/service.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inspections.models import Inspection
from app.modules.reports.models import ReportJob, ReportJobStatus, ReportTemplate
from app.modules.reports.repository import ReportRepository
from app.modules.reports.schemas import ReportJobCreate, ReportJobStatusUpdate

_INSURANCE_ELIGIBLE_TYPES = frozenset({
    "WIND_MITIGATION", "FOUR_POINT", "ROOF_CERTIFICATION"
})


async def create_report_job(
    inspection_id: uuid.UUID, data: ReportJobCreate, session: AsyncSession
) -> ReportJob:
    """Insert a report job scoped to inspection_id. tenant_id is set by ReportRepository.create()."""
    if data.template == ReportTemplate.INSURANCE:
        result = await session.execute(
            select(Inspection).where(Inspection.id == inspection_id)
        )
        inspection = result.scalars().first()
        if inspection is None:
            raise ValueError("inspection not found")
        if not _INSURANCE_ELIGIBLE_TYPES.intersection(inspection.inspection_types):
            raise ValueError(
                "INSURANCE template requires WIND_MITIGATION, FOUR_POINT, or ROOF_CERTIFICATION"
            )

    job = ReportJob(inspection_id=inspection_id, template=data.template)
    await ReportRepository(session).create(job)
    await session.refresh(job)
    return job


async def get_report_job(
    inspection_id: uuid.UUID, job_id: uuid.UUID, session: AsyncSession
) -> ReportJob | None:
    """Return a report job by id, scoped to inspection_id. RLS limits results to the current tenant."""
    result = await session.execute(
        select(ReportJob).where(
            ReportJob.id == job_id, ReportJob.inspection_id == inspection_id
        )
    )
    return result.scalars().first()


async def list_report_jobs_by_inspection(
    inspection_id: uuid.UUID, session: AsyncSession
) -> list[ReportJob]:
    result = await session.execute(
        select(ReportJob)
        .where(ReportJob.inspection_id == inspection_id)
        .order_by(ReportJob.created_at)
    )
    return list(result.scalars().all())


async def update_job_status(
    inspection_id: uuid.UUID,
    job_id: uuid.UUID,
    data: ReportJobStatusUpdate,
    session: AsyncSession,
) -> ReportJob | None:
    job = await get_report_job(inspection_id, job_id, session)
    if job is None:
        return None
    job.status = data.status
    if data.s3_url is not None:
        job.s3_url = data.s3_url
    if data.error_message is not None:
        job.error_message = data.error_message
    if data.status == ReportJobStatus.COMPLETE:
        job.generated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(job)
    return job
