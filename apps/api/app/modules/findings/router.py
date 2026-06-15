# app/modules/findings/router.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.findings import service
from app.modules.findings.schemas import (
    FindingCreate,
    FindingResponse,
    FindingsBySectionResponse,
    FindingUpdate,
)
from app.modules.inspections.service import get_inspection
from app.shared.db.session import get_session

router = APIRouter(prefix="/inspections/{inspection_id}/findings", tags=["findings"])


async def _ensure_inspection(inspection_id: uuid.UUID, session: AsyncSession) -> None:
    """404 if the inspection doesn't exist or doesn't belong to the current tenant (RLS)."""
    inspection = await get_inspection(inspection_id, session)
    if inspection is None:
        raise HTTPException(status_code=404, detail="inspection not found")


@router.post("", response_model=FindingResponse, status_code=201)
async def create_finding(
    inspection_id: uuid.UUID,
    payload: FindingCreate,
    session: AsyncSession = Depends(get_session),
) -> FindingResponse:
    await _ensure_inspection(inspection_id, session)
    finding = await service.create_finding(inspection_id, payload, session)
    return FindingResponse.model_validate(finding)


# Registered before /{finding_id} so the literal "summary" segment matches first.
@router.get("/summary")
async def get_inspection_summary(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    await _ensure_inspection(inspection_id, session)
    return await service.get_inspection_summary(inspection_id, session)


@router.get("")
async def list_findings(
    inspection_id: uuid.UUID,
    grouped: bool = Query(False),
    session: AsyncSession = Depends(get_session),
):
    await _ensure_inspection(inspection_id, session)
    findings = await service.list_findings_by_inspection(inspection_id, session)
    if not grouped:
        return [FindingResponse.model_validate(f) for f in findings]

    sections: dict[str, list[FindingResponse]] = {}
    for f in findings:
        key = f.section.value
        if key not in sections:
            sections[key] = []
        sections[key].append(FindingResponse.model_validate(f))
    return [
        FindingsBySectionResponse(section=sec, findings=items)
        for sec, items in sections.items()
    ]


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    inspection_id: uuid.UUID,
    finding_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> FindingResponse:
    await _ensure_inspection(inspection_id, session)
    finding = await service.get_finding(inspection_id, finding_id, session)
    if finding is None:
        raise HTTPException(status_code=404, detail="finding not found")
    return FindingResponse.model_validate(finding)


@router.put("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    inspection_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: FindingUpdate,
    session: AsyncSession = Depends(get_session),
) -> FindingResponse:
    await _ensure_inspection(inspection_id, session)
    finding = await service.update_finding(inspection_id, finding_id, payload, session)
    if finding is None:
        raise HTTPException(status_code=404, detail="finding not found")
    return FindingResponse.model_validate(finding)


@router.delete("/{finding_id}", status_code=204)
async def delete_finding(
    inspection_id: uuid.UUID,
    finding_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    await _ensure_inspection(inspection_id, session)
    deleted = await service.delete_finding(inspection_id, finding_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="finding not found")
