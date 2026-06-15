# tests/shared/test_tenant_scoped_mixin.py
"""ADR-025: TenantScopedMixin.tenant_id must not carry a declarative FK.

A string ForeignKey("tenants.id") on a shared mixin is resolved against
Base.metadata at mapper-configure time, which depends on import order across
unrelated modules — raising NoReferencedTableError if "tenants" hasn't been
registered yet. Referential integrity for tenant_id is enforced at the DB
level by the per-table Alembic migrations (ON DELETE CASCADE) and by RLS,
not by the ORM mapping.
"""
import pytest

from app.shared.db.mixins import TenantScopedMixin


def test_mixin_tenant_id_has_no_declarative_foreign_key():
    column = TenantScopedMixin.tenant_id.column
    assert column.foreign_keys == set()


@pytest.mark.parametrize(
    "model_module,model_name",
    [
        ("app.modules.inspections.models", "Inspection"),
        ("app.modules.inspections.models", "ReportSnapshot"),
        ("app.modules.inspections.models", "InspectorNarrativeLibrary"),
        ("app.modules.properties.models", "Property"),
    ],
)
def test_tenant_scoped_model_tenant_id_has_no_declarative_foreign_key(model_module, model_name):
    """Models using TenantScopedMixin must have no ORM-level FK on tenant_id,
    so mapper configuration cannot raise NoReferencedTableError regardless of
    module import order."""
    import importlib

    module = importlib.import_module(model_module)
    model = getattr(module, model_name)
    assert model.__table__.c.tenant_id.foreign_keys == set()
