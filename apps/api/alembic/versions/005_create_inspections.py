# alembic/versions/005_create_inspections.py
"""create inspections table with RLS

Revision ID: 005
Revises: 004
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

_VALID_TYPES = (
    "'FULL_INSPECTION','WIND_MITIGATION','FOUR_POINT','MOLD_INSPECTION',"
    "'TERMITES','ROOF_CERTIFICATION','OPENING_PROTECTION','SEWER_INSPECTION'"
)


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE inspection_status_enum AS ENUM "
        "('SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED')"
    )
    op.execute(
        "CREATE TYPE payment_timing_enum AS ENUM "
        "('AT_PROPERTY','AT_DELIVERY','AFTER_DELIVERY')"
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.create_table(
        "inspections",
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
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED",
                name="inspection_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="SCHEDULED",
        ),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.Time(), nullable=True),
        # TEXT[] — values validated by check constraint below
        sa.Column("inspection_types", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("realtor_name", sa.String(255), nullable=True),
        sa.Column("realtor_phone", sa.String(20), nullable=True),
        sa.Column("owner_buyer_name", sa.String(255), nullable=True),
        sa.Column("owner_buyer_phone", sa.String(20), nullable=True),
        sa.Column("owner_buyer_email", sa.String(255), nullable=True),
        sa.Column("listing_agent_name", sa.String(255), nullable=True),
        sa.Column("listing_agent_phone", sa.String(20), nullable=True),
        sa.Column("additional_notes", sa.Text(), nullable=True),
        sa.Column("gate_code", sa.String(50), nullable=True),
        sa.Column("lockbox_code", sa.String(50), nullable=True),
        sa.Column("total_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "payment_timing",
            postgresql.ENUM(
                "AT_PROPERTY", "AT_DELIVERY", "AFTER_DELIVERY",
                name="payment_timing_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="AT_PROPERTY",
        ),
        sa.Column("full_report_number", sa.String(50), nullable=True),
        sa.Column("insurance_report_number", sa.String(50), nullable=True),
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
        sa.CheckConstraint(
            f"inspection_types <@ ARRAY[{_VALID_TYPES}]::text[] "
            "AND array_length(inspection_types, 1) >= 1",
            name="ck_inspections_types_valid",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"],
            name="fk_inspections_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["property_id"], ["properties.id"],
            name="fk_inspections_property_id", ondelete="CASCADE",
        ),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index("ix_inspections_tenant_id", "inspections", ["tenant_id"])
    op.create_index("ix_inspections_property_id", "inspections", ["property_id"])
    op.create_index("ix_inspections_scheduled_date", "inspections", ["scheduled_date"])

    # Partial unique indexes — report numbers unique per tenant, NULLs excluded
    op.create_index(
        "uix_inspections_tenant_full_report",
        "inspections",
        ["tenant_id", "full_report_number"],
        unique=True,
        postgresql_where=sa.text("full_report_number IS NOT NULL"),
    )
    op.create_index(
        "uix_inspections_tenant_insurance_report",
        "inspections",
        ["tenant_id", "insurance_report_number"],
        unique=True,
        postgresql_where=sa.text("insurance_report_number IS NOT NULL"),
    )

    # ── RLS ───────────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE inspections ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inspections FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON inspections
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON inspections TO app_role"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON inspections")
    op.drop_table("inspections", if_exists=True)
    op.execute("DROP TYPE IF EXISTS payment_timing_enum")
    op.execute("DROP TYPE IF EXISTS inspection_status_enum")
