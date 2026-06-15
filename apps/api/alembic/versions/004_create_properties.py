# alembic/versions/004_create_properties.py
"""create properties table with RLS

Revision ID: 004
Revises: 003
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "properties",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text(
                "NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
            ),
        ),
        sa.Column("street", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(2), nullable=False, server_default="FL"),
        sa.Column("zip_code", sa.String(10), nullable=False),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("adjusted_sqft", sa.Integer(), nullable=True),
        # Insurance report — discrete columns (ADR-006)
        sa.Column("roof_permit_number", sa.String(50), nullable=True),
        sa.Column("roof_permit_date", sa.Date(), nullable=True),
        sa.Column("roof_style", sa.String(100), nullable=True),
        sa.Column("roof_type", sa.String(100), nullable=True),
        sa.Column("water_heater_type", sa.String(100), nullable=True),
        sa.Column("water_heater_location", sa.String(100), nullable=True),
        sa.Column("water_heater_capacity", sa.String(50), nullable=True),
        sa.Column("electrical_brand", sa.String(100), nullable=True),
        sa.Column("electrical_amps", sa.Integer(), nullable=True),
        sa.Column("electrical_location", sa.String(100), nullable=True),
        sa.Column("ac_brand", sa.String(100), nullable=True),
        sa.Column("ac_age", sa.Integer(), nullable=True),
        sa.Column("ac_model", sa.String(100), nullable=True),
        sa.Column("ac_series", sa.String(100), nullable=True),
        sa.Column("mit_doors_protection", sa.Boolean(), nullable=True),
        sa.Column("mit_windows_protection", sa.Boolean(), nullable=True),
        # Insurance report — display-only JSONB (ADR-006)
        sa.Column(
            "appliances", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "bedrooms", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "bathrooms", postgresql.JSONB(), nullable=False, server_default="{}"
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_properties_tenant_id",
            ondelete="CASCADE",
        ),
    )

    op.create_index("ix_properties_tenant_id", "properties", ["tenant_id"])

    op.execute("ALTER TABLE properties ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE properties FORCE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY tenant_isolation ON properties
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON properties TO app_role"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON properties")
    op.drop_table("properties", if_exists=True)
