# ADR-025: No declarative ForeignKey on TenantScopedMixin.tenant_id

## Status
Accepted — 2026-06-14
Extended — 2026-06-14 (see "Extension: inspector_profiles" below)

## Context
`TenantScopedMixin` (`apps/api/app/shared/db/mixins.py`) adds a `tenant_id`
column to every tenant-scoped ORM model (e.g. `Inspection`, `Property`).
It previously declared this column with a string foreign key:

```python
tenant_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("tenants.id", ondelete="CASCADE"),
    ...
)
```

In production this raised:

```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
'inspections.tenant_id' could not find table 'tenants'
```

This is a SQLAlchemy *declarative mapping* error, not a database error. A
string `ForeignKey("tenants.id")` is resolved against `Base.metadata` when
mappers are configured. Because the FK lives on a **shared mixin** used by
modules across the codebase, whether `app.modules.tenants.models` has been
imported (and thus registered the `tenants` table in `Base.metadata`) by the
time mapper configuration runs depends on import order — which differs
between `app.main`, `alembic/env.py`, test entrypoints, and worker
processes. A prior fix (commit `6afe177`) added explicit imports to
`app.main`, but the error can still surface from any entrypoint that doesn't
happen to import `tenants.models` first.

## Decision
`TenantScopedMixin.tenant_id` no longer declares an ORM-level
`ForeignKey("tenants.id")`. The column is just a `UUID NOT NULL`, indexed,
security discriminator.

Referential integrity for `tenant_id -> tenants.id` (including
`ON DELETE CASCADE`) is enforced at the **database level** by the per-table
`sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE")`
constraints already present in the Alembic migrations (e.g.
`005_create_inspections.py`, `010_alter_inspections_adr024.py`). Those are
raw DDL executed in migration order (tenants is always table 001), so they
do not depend on Python import order and are unaffected by this change.

Combined with RLS policies (ADR-022/ADR-023) and the tenant middleware /
Cognito JWT, tenant scoping integrity is enforced by:
1. Postgres FK constraint + `ON DELETE CASCADE` (data integrity)
2. RLS policy on `app.current_tenant_id` (row visibility)
3. `TenantScopedRepository.create()` (write-path enforcement)

The ORM mapping no longer needs to know about `tenants.id` at all.

## Scope
This ADR covers `TenantScopedMixin` only (used by `Inspection`,
`ReportSnapshot`, `InspectorNarrativeLibrary`, `Property`). Other modules
(`agreements`, `findings`, `inspectors`, `media`, `reports`) declare their
own `tenant_id` column with their own `ForeignKey("tenants.id")` and are
*not* changed by this ADR — they were not implicated in the reported error
and removing DB constraints from already-applied migrations is a separate,
higher-risk decision out of scope here. If those modules hit the same
`NoReferencedTableError`, the same reasoning would apply to them.

## Consequences
- Fixes `NoReferencedTableError` for `TenantScopedMixin`-based models
  regardless of import order.
- The ORM no longer enforces `tenant_id` referential integrity directly —
  this is now solely a DB-constraint + RLS concern, which is where it
  already lived in practice.
- No migration changes required; existing DB-level FK constraints and
  `ON DELETE CASCADE` behavior are unchanged.

## How to apply
- Do not add `ForeignKey(...)` to columns defined on shared mixins that are
  consumed by many modules. If a per-table FK to another tenant-scoped
  table is needed, declare it on the concrete model (where import order is
  controlled by that module itself), not on a shared mixin.
- See `apps/api/app/shared/db/mixins.py` and
  `apps/api/tests/shared/test_tenant_scoped_mixin.py`.

## Extension: inspector_profiles (2026-06-14)

The same exception class (`NoReferencedTableError`) recurred for
`apps/api/app/modules/inspections/models.py`, this time for
`ForeignKey("inspector_profiles.id")` — not via a shared mixin, but via a
**cross-module** string FK. It's triggered by a different SQLAlchemy code
path: `Base.metadata.sorted_tables` (used by `create_all`/DDL
sorting/autogenerate) raises as soon as it needs to resolve FK dependencies
and `app.modules.inspectors.models` hasn't registered `inspector_profiles`
in `Base.metadata` yet. Reproduced directly:

```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
'inspections.inspector_id' could not find table 'inspector_profiles' with
which to generate a foreign key to target column 'id'
```

**Decision:** removed the declarative FK from the three cross-module
references to `inspector_profiles.id`:
- `Inspection.inspector_id`
- `ReportSnapshot.published_by`
- `InspectorNarrativeLibrary.inspector_id`

All three retain their DB-level `ForeignKeyConstraint` (RESTRICT/RESTRICT/
CASCADE respectively) from migration 010, so referential integrity is
unchanged — same reasoning as the `tenant_id` case above.

**Not changed:** `ReportSnapshot.inspection_id -> ForeignKey("inspections.id")`.
Both `Inspection` and `ReportSnapshot` are defined in the same module, so
`inspections` and `report_snapshots` are always registered together
regardless of import order. This FK is not subject to the bug and was left
in place.

**General rule:** a declarative `ForeignKey("other_table.col")` is only safe
when `other_table` is guaranteed to be registered in `Base.metadata` by the
time it's resolved — i.e. defined in the same module/file. A FK to a table
owned by a *different* module is cross-module-import-order-dependent and
should not be declared at the ORM level; rely on the DB-level constraint
from the Alembic migration instead.

See `apps/api/tests/test_inspections_models_fk.py`.
