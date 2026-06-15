# alembic/versions/001_create_tenants.py
"""create tenants table with RLS

Revision ID: 001
Revises:
Create Date: 2026-05-29
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subdomain", sa.String(63), nullable=False),
        sa.Column("custom_domain", sa.String(253), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("subdomain", name="uq_tenants_subdomain"),
    )

    # Application role — non-superuser, non-owner, so RLS applies to it.
    # Created here (the foundation migration) so all subsequent migrations
    # can grant privileges to it without checking for existence themselves.
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_role') THEN
                CREATE ROLE app_role;
            END IF;
        END $$
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO app_role")

    # RLS: non-owner app role cannot query across tenants
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY")

    # Policy: only rows whose id matches the session variable are visible.
    # NULLIF(..., '') converts an empty string to NULL so the cast never errors;
    # NULL result means id = NULL is always false → zero rows (fail-closed).
    op.execute("""
        CREATE POLICY tenant_isolation ON tenants
        USING (id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON tenants")
    op.drop_table("tenants", if_exists=True)
