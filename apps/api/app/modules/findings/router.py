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
    PhotoAddRequest,
    PhotoDeleteRequest,
    PhotoUploadRequest,
    PhotoUploadResponse,
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

    # Serialize first (avoids ORM mutation), then refresh presigned URLs.
    validated: list[FindingResponse] = []
    for f in findings:
        resp = FindingResponse.model_validate(f)
        if resp.photos:
            try:
                resp.photos = await service.refresh_photo_urls(f)
            except Exception:
                pass  # S3 unavailable; keep stored URLs
        validated.append(resp)

    if not grouped:
        return validated

    sections: dict[str, list[FindingResponse]] = {}
    for resp in validated:
        key = resp.section.value
        if key not in sections:
            sections[key] = []
        sections[key].append(resp)
    return [
        FindingsBySectionResponse(section=sec, findings=items)
        for sec, items in sections.items()
    ]


# ── Photo endpoints (registered before /{finding_id} to prevent routing ambiguity) ──

@router.post("/{finding_id}/photos/upload-url", response_model=PhotoUploadResponse)
async def get_photo_upload_url(
    inspection_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: PhotoUploadRequest,
    session: AsyncSession = Depends(get_session),
) -> PhotoUploadResponse:
    await _ensure_inspection(inspection_id, session)
    finding = await service.get_finding(inspection_id, finding_id, session)
    if finding is None:
        raise HTTPException(status_code=404, detail="finding not found")
    from app.modules.media.s3 import generate_upload_url
    urls = generate_upload_url(
        tenant_id=str(finding.tenant_id),
        inspection_id=str(inspection_id),
        finding_id=str(finding_id),
        content_type=payload.content_type,
    )
    return PhotoUploadResponse(**urls)


@router.post("/{finding_id}/photos", response_model=FindingResponse)
async def add_photo(
    inspection_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: PhotoAddRequest,
    session: AsyncSession = Depends(get_session),
) -> FindingResponse:
    await _ensure_inspection(inspection_id, session)
    finding = await service.add_photo_to_finding(
        finding_id, inspection_id, payload.key, payload.view_url, session
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="finding not found")
    return FindingResponse.model_validate(finding)


@router.delete("/{finding_id}/photos", response_model=FindingResponse)
async def remove_photo(
    inspection_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: PhotoDeleteRequest,
    session: AsyncSession = Depends(get_session),
) -> FindingResponse:
    await _ensure_inspection(inspection_id, session)
    finding = await service.remove_photo_from_finding(
        finding_id, inspection_id, payload.key, session
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="finding not found")
    return FindingResponse.model_validate(finding)


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
