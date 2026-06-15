# app/shared/db/mixins.py
import uuid

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TenantScopedMixin:
    """Adds tenant_id to any ORM model.

    Use TenantScopedRepository.create() to insert — it sets tenant_id from
    session.info["tenant_id"] before session.add(). Never call session.add()
    directly on objects that inherit this mixin.
    """

    # No ForeignKey("tenants.id") here — deliberately. See ADR-025: this is a
    # shared mixin, and a declarative string FK is resolved against
    # Base.metadata at mapper-configure time, which depends on import order
    # across unrelated modules (NoReferencedTableError if "tenants" hasn't
    # been registered yet). The DB-level FK + ON DELETE CASCADE already exists
    # per-table via the Alembic migrations (e.g. 005_create_inspections);
    # integrity is enforced there and by RLS, not by the ORM mapping.
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        # Defence-in-depth: DB sets tenant_id from GUC if the ORM value is absent.
        server_default=text(
            "NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
        ),
    )
