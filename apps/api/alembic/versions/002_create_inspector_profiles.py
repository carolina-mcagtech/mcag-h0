# alembic/versions/002_create_inspector_profiles.py
"""create inspector_profiles table with RLS

Revision ID: 002
Revises: 001
Create Date: 2026-05-29
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inspector_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # tenant_id is populated by application code from the session context
        # variable (app.current_tenant_id). The server_default is a DB-level
        # safety net for raw SQL inserts that omit the column — if the context
        # variable is unset the NULLIF returns NULL and the NOT NULL constraint
        # rejects the insert, which is the correct fail-closed behaviour.
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text(
                "NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
            ),
        ),
        sa.Column("cognito_sub", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("license_number", sa.String(50), nullable=False),
        sa.Column("license_expiry_date", sa.Date(), nullable=False),
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
        sa.UniqueConstraint("cognito_sub", name="uq_inspector_profiles_cognito_sub"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_inspector_profiles_tenant_id",
            ondelete="CASCADE",
        ),
    )

    op.execute("ALTER TABLE inspector_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inspector_profiles FORCE ROW LEVEL SECURITY")

    # Filter rows by tenant_id. Same NULLIF pattern as the tenants policy:
    # an empty or missing session variable yields NULL → no rows visible.
    op.execute("""
        CREATE POLICY tenant_isolation ON inspector_profiles
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON inspector_profiles TO app_role"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON inspector_profiles")
    op.drop_table("inspector_profiles", if_exists=True)
