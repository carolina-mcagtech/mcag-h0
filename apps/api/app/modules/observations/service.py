# app/modules/observations/service.py
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.observations.catalog import (
    SECTION_CATALOG,
    get_section_catalog,
)
from app.modules.observations.models import ComponentObservation, SectionMetadata
from app.modules.observations.schemas import (
    ComponentObservationResponse,
    ComponentObservationUpsert,
    SectionMetadataUpsert,
    SectionObservationsResponse,
)


def _get_tenant_id(session: AsyncSession) -> uuid.UUID:
    tid = session.info.get("tenant_id")
    if tid is None:
        raise RuntimeError(
            "No tenant context: session.info['tenant_id'] is unset."
        )
    return tid


async def upsert_observation(
    inspection_id: uuid.UUID,
    payload: ComponentObservationUpsert,
    session: AsyncSession,
) -> ComponentObservation:
    section_def = get_section_catalog(payload.section)
    if section_def is None:
        raise ValueError(f"Unknown section: {payload.section}")

    item_def = next(
        (i for i in section_def["items"] if i["key"] == payload.item_key), None
    )
    if item_def is None:
        raise ValueError(
            f"Unknown item_key '{payload.item_key}' for section '{payload.section}'"
        )

    room_type: str | None = (
        section_def.get("room_type") if section_def.get("is_room_based") else None
    )
    tid = _get_tenant_id(session)

    stmt = (
        pg_insert(ComponentObservation)
        .values(
            tenant_id=tid,
            inspection_id=inspection_id,
            section=payload.section,
            item_key=payload.item_key,
            item_label=item_def["label"],
            condition=payload.condition,
            observations=payload.observations,
            room_type=room_type,
            room_index=payload.room_index,
            room_label=payload.room_label,
            sort_order=item_def["sort_order"],
        )
        .on_conflict_do_update(
            constraint="component_observations_inspection_id_section_item_key_room__key",
            set_={
                "condition": payload.condition,
                "observations": payload.observations,
                "room_label": payload.room_label,
                "updated_at": func.now(),
            },
        )
        .returning(ComponentObservation.id)
    )

    result = await session.execute(stmt)
    obs_id: uuid.UUID = result.scalar_one()
    await session.flush()

    fetched = await session.get(ComponentObservation, obs_id)
    assert fetched is not None
    return fetched


async def upsert_section_metadata(
    inspection_id: uuid.UUID,
    payload: SectionMetadataUpsert,
    session: AsyncSession,
) -> SectionMetadata:
    if get_section_catalog(payload.section) is None:
        raise ValueError(f"Unknown section: {payload.section}")

    tid = _get_tenant_id(session)

    stmt = (
        pg_insert(SectionMetadata)
        .values(
            tenant_id=tid,
            inspection_id=inspection_id,
            section=payload.section,
            data=payload.data,
        )
        .on_conflict_do_update(
            constraint="section_metadata_inspection_id_section_key",
            set_={
                # Merge JSONB: existing fields not in payload.data are preserved.
                "data": text("section_metadata.data || EXCLUDED.data"),
                "updated_at": func.now(),
            },
        )
        .returning(SectionMetadata.id)
    )

    result = await session.execute(stmt)
    meta_id: uuid.UUID = result.scalar_one()
    await session.flush()

    fetched = await session.get(SectionMetadata, meta_id)
    assert fetched is not None
    return fetched


async def get_section_observations(
    inspection_id: uuid.UUID,
    section: str,
    session: AsyncSession,
) -> SectionObservationsResponse:
    section_def = get_section_catalog(section)
    if section_def is None:
        raise ValueError(f"Unknown section: {section}")

    obs_result = await session.execute(
        select(ComponentObservation)
        .where(
            ComponentObservation.inspection_id == inspection_id,
            ComponentObservation.section == section,
        )
        .order_by(ComponentObservation.room_index, ComponentObservation.sort_order)
    )
    observations = list(obs_result.scalars().all())

    meta_result = await session.execute(
        select(SectionMetadata).where(
            SectionMetadata.inspection_id == inspection_id,
            SectionMetadata.section == section,
        )
    )
    meta_row = meta_result.scalars().first()
    metadata_data = meta_row.data if meta_row is not None else {}

    return SectionObservationsResponse(
        section=section,
        label=section_def["label"],
        catalog=section_def,
        metadata=metadata_data,
        observations=[ComponentObservationResponse.model_validate(o) for o in observations],
    )


async def list_all_observations(
    inspection_id: uuid.UUID,
    session: AsyncSession,
) -> dict[str, SectionObservationsResponse]:
    obs_result = await session.execute(
        select(ComponentObservation)
        .where(ComponentObservation.inspection_id == inspection_id)
        .order_by(
            ComponentObservation.section,
            ComponentObservation.room_index,
            ComponentObservation.sort_order,
        )
    )
    all_obs = list(obs_result.scalars().all())

    meta_result = await session.execute(
        select(SectionMetadata).where(
            SectionMetadata.inspection_id == inspection_id
        )
    )
    meta_by_section = {m.section: m.data for m in meta_result.scalars().all()}

    obs_by_section: dict[str, list[ComponentObservation]] = {}
    for obs in all_obs:
        obs_by_section.setdefault(obs.section, []).append(obs)

    result: dict[str, SectionObservationsResponse] = {}
    for section_key, section_def in SECTION_CATALOG.items():
        obs_list = obs_by_section.get(section_key, [])
        result[section_key] = SectionObservationsResponse(
            section=section_key,
            label=section_def["label"],
            catalog=section_def,
            metadata=meta_by_section.get(section_key, {}),
            observations=[ComponentObservationResponse.model_validate(o) for o in obs_list],
        )

    return result


async def delete_observation(
    observation_id: uuid.UUID,
    inspection_id: uuid.UUID,
    session: AsyncSession,
) -> bool:
    result = await session.execute(
        select(ComponentObservation).where(
            ComponentObservation.id == observation_id,
            ComponentObservation.inspection_id == inspection_id,
        )
    )
    obs = result.scalars().first()
    if obs is None:
        return False
    await session.delete(obs)
    await session.flush()
    return True
