# tests/test_inspections_models_fk.py
"""ADR-025 (extended to inspector_profiles): cross-module string FKs in
inspections/models.py must not raise NoReferencedTableError.

A ForeignKey("inspector_profiles.id") in app.modules.inspections.models is
resolved against Base.metadata when something needs FK dependency info
(e.g. Base.metadata.sorted_tables, used by create_all/autogenerate/DDL
sorting). If app.modules.inspectors.models hasn't been imported yet, that
table isn't registered and resolution raises NoReferencedTableError —
exactly like the tenant_id case in ADR-025, just triggered via a different
SQLAlchemy code path.

ReportSnapshot.inspection_id -> "inspections.id" is NOT affected: both
tables are defined in this same module, so they are always registered
together. Its FK is intentionally kept.
"""
from app.modules.inspections.models import Inspection, InspectorNarrativeLibrary, ReportSnapshot


def test_inspector_id_fks_have_no_declarative_foreign_key():
    assert Inspection.__table__.c.inspector_id.foreign_keys == set()
    assert ReportSnapshot.__table__.c.published_by.foreign_keys == set()
    assert InspectorNarrativeLibrary.__table__.c.inspector_id.foreign_keys == set()


def test_report_snapshot_inspection_id_fk_is_kept():
    """Same-module FK to inspections.id is unaffected by ADR-025 and kept."""
    fks = ReportSnapshot.__table__.c.inspection_id.foreign_keys
    assert {fk.target_fullname for fk in fks} == {"inspections.id"}
