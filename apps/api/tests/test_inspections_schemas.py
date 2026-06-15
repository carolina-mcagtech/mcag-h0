# tests/test_inspections_schemas.py
"""Pydantic schema validation for the ADR-024 inspections module (Tarea 2).

Pure validation tests — no DB required.
"""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.modules.inspections.schemas import (
    InspectionCreate,
    InspectionUpdate,
    NarrativeLibraryCreate,
)


def _base_create_kwargs(**overrides) -> dict:
    return {
        "inspector_id": uuid.uuid4(),
        "scheduled_at": datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
        "property_address": "10 Test Ln, Tampa, FL 33601",
        "inspection_types": ["FULL_INSPECTION"],
        "total_fee": "150.00",
        **overrides,
    }


def test_inspection_create_minimal_payload_applies_defaults():
    data = InspectionCreate(**_base_create_kwargs())

    assert data.payment_timing == "AT_PROPERTY"
    assert data.appliances == {}
    assert data.rooms == {}
    assert data.wind_mit_doors_protected is False
    assert data.wind_mit_windows_protected is False
    assert data.gate_code is None


def test_inspection_create_accepts_multiple_types():
    data = InspectionCreate(**_base_create_kwargs(
        inspection_types=["WIND_MITIGATION", "FOUR_POINT", "ROOF_CERTIFICATION"],
    ))

    assert {t.value for t in data.inspection_types} == {
        "WIND_MITIGATION", "FOUR_POINT", "ROOF_CERTIFICATION",
    }


def test_inspection_create_rejects_empty_inspection_types():
    with pytest.raises(ValidationError):
        InspectionCreate(**_base_create_kwargs(inspection_types=[]))


def test_inspection_create_rejects_unknown_inspection_type():
    with pytest.raises(ValidationError):
        InspectionCreate(**_base_create_kwargs(inspection_types=["NOT_A_REAL_TYPE"]))


def test_inspection_update_all_fields_optional():
    # An empty update payload must be valid — every field is optional.
    data = InspectionUpdate()

    assert data.model_dump(exclude_unset=True) == {}


def test_inspection_update_rejects_empty_inspection_types():
    with pytest.raises(ValidationError):
        InspectionUpdate(inspection_types=[])


def test_inspection_update_partial_payload():
    data = InspectionUpdate(total_fee="200.00", gate_code="1234")

    dumped = data.model_dump(exclude_unset=True)
    assert set(dumped) == {"total_fee", "gate_code"}
    assert dumped["gate_code"] == "1234"
    assert "property_address" not in dumped


# ── NarrativeLibraryCreate (ADR-024 D6) ─────────────────────────────────────


def test_narrative_library_create_minimal_payload():
    data = NarrativeLibraryCreate(
        inspector_id=uuid.uuid4(),
        system="electrical",
        narrative_text="Double-tapped breaker observed at main panel.",
    )

    assert data.trigger_keywords == []


def test_narrative_library_create_with_keywords():
    data = NarrativeLibraryCreate(
        inspector_id=uuid.uuid4(),
        system="roof",
        trigger_keywords=["granule loss", "curling"],
        narrative_text="Granule loss consistent with age of roof covering.",
    )

    assert data.trigger_keywords == ["granule loss", "curling"]
