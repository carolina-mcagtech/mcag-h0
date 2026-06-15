# alembic/versions/010_alter_inspections_adr024.py
"""alter inspections to ADR-024 schema; add report_snapshots and inspector_narrative_library

Revision ID: 010
Revises: 009
Create Date: 2026-06-12
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None

_OLD_TYPES = (
    "'FULL_INSPECTION','WIND_MITIGATION','FOUR_POINT','MOLD_INSPECTION',"
    "'TERMITES','ROOF_CERTIFICATION','OPENING_PROTECTION','SEWER_INSPECTION'"
)
_NEW_TYPES = (
    "'FULL_INSPECTION','WIND_MITIGATION','FOUR_POINT','MOLD_INSPECTION',"
    "'TERMITES','ROOF_CERTIFICATION','OPENING_PROTECTION','SEWER_INSPECTION',"
    "'LEAD_PAINT_INSPECTION','WATER_QUALITY_TEST'"
)
_OLD_STATUSES = "'SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED'"
_NEW_STATUSES = "'DRAFT','IN_FIELD','PENDING_REVIEW','PUBLISHED','DELIVERED'"


def upgrade() -> None:
    # ── Architect Option C: clear dev/test data before the FSM-incompatible ───
    # status/type changes below. Phase 0 — no production workloads (CLAUDE.md).
    op.execute("DELETE FROM inspections")

    # ── inspection_types: TEXT[] + CHECK -> native enum[] (10 values, ADR-024) ──
    op.execute("ALTER TABLE inspections DROP CONSTRAINT ck_inspections_types_valid")
    op.execute(f"CREATE TYPE inspection_type_enum AS ENUM ({_NEW_TYPES})")
    op.execute("""
        ALTER TABLE inspections
        ALTER COLUMN inspection_types
        TYPE inspection_type_enum[]
        USING inspection_types::text[]::inspection_type_enum[]
    """)
    op.execute("""
        ALTER TABLE inspections
        ADD CONSTRAINT ck_inspections_types_nonempty
        CHECK (cardinality(inspection_types) >= 1)
    """)

    # ── status: SCHEDULED/IN_PROGRESS/COMPLETED/CANCELLED -> ADR-024 FSM ────────
    op.execute(f"CREATE TYPE inspection_status_enum_new AS ENUM ({_NEW_STATUSES})")
    op.execute("ALTER TABLE inspections ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE inspections
        ALTER COLUMN status TYPE inspection_status_enum_new
        USING (
            CASE status::text
                WHEN 'SCHEDULED'   THEN 'DRAFT'
                WHEN 'IN_PROGRESS' THEN 'IN_FIELD'
                WHEN 'COMPLETED'   THEN 'PUBLISHED'
                WHEN 'CANCELLED'   THEN 'DRAFT'
            END
        )::inspection_status_enum_new
    """)
    op.execute("DROP TYPE inspection_status_enum")
    op.execute("ALTER TYPE inspection_status_enum_new RENAME TO inspection_status_enum")
    op.execute("ALTER TABLE inspections ALTER COLUMN status SET DEFAULT 'DRAFT'")

    # ── property_id (FK properties) -> property_address (free text, REBS card) ──
    op.drop_constraint("fk_inspections_property_id", "inspections", type_="foreignkey")
    op.drop_index("ix_inspections_property_id", table_name="inspections")
    op.drop_column("inspections", "property_id")
    # inspections is empty at this point (DELETE above), so a direct NOT NULL add is safe.
    op.add_column("inspections", sa.Column("property_address", sa.String(500), nullable=False))

    # ── inspector_id (FK inspector_profiles) — required by ADR-024 D3 ───────────
    op.add_column(
        "inspections",
        sa.Column(
            "inspector_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_inspections_inspector_id",
        "inspections",
        "inspector_profiles",
        ["inspector_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_inspections_inspector_id", "inspections", ["inspector_id"])

    # ── scheduled_date + scheduled_time -> scheduled_at ──────────────────────────
    op.add_column("inspections", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("""
        UPDATE inspections
        SET scheduled_at = (scheduled_date + COALESCE(scheduled_time, '00:00'::time)) AT TIME ZONE 'UTC'
        WHERE scheduled_at IS NULL
    """)
    op.alter_column("inspections", "scheduled_at", nullable=False)
    op.drop_index("ix_inspections_scheduled_date", table_name="inspections")
    op.drop_column("inspections", "scheduled_date")
    op.drop_column("inspections", "scheduled_time")
    op.create_index("ix_inspections_scheduled_at", "inspections", ["scheduled_at"])

    # ── total_fee: optional at creation time (set later in workflow) ───────────
    op.alter_column("inspections", "total_fee", nullable=True)

    # ── rename contact columns to match REBS Ficha card field names ────────────
    op.alter_column("inspections", "realtor_phone", new_column_name="realtor_cell")
    op.alter_column("inspections", "owner_buyer_phone", new_column_name="owner_buyer_cell")
    op.alter_column("inspections", "listing_agent_phone", new_column_name="listing_agent_cell")
    op.alter_column("inspections", "lockbox_code", new_column_name="lockbox")

    # ── new fields: REBS Preinspection sheet (roof / MEP / appliances / rooms) ──
    op.add_column("inspections", sa.Column("year_built", sa.Integer(), nullable=True))
    op.add_column("inspections", sa.Column("adj_sqft", sa.Integer(), nullable=True))

    op.add_column("inspections", sa.Column("roof_permit_number", sa.String(50), nullable=True))
    op.add_column("inspections", sa.Column("roof_date", sa.Date(), nullable=True))
    op.add_column("inspections", sa.Column("roof_style", sa.String(100), nullable=True))
    op.add_column("inspections", sa.Column("roof_type", sa.String(100), nullable=True))

    op.add_column("inspections", sa.Column("water_heater_type", sa.String(100), nullable=True))
    op.add_column("inspections", sa.Column("water_heater_location", sa.String(100), nullable=True))
    op.add_column("inspections", sa.Column("water_heater_capacity", sa.String(50), nullable=True))

    op.add_column("inspections", sa.Column("electrical_brand", sa.String(100), nullable=True))
    op.add_column("inspections", sa.Column("electrical_amps", sa.Integer(), nullable=True))
    op.add_column("inspections", sa.Column("electrical_location", sa.String(100), nullable=True))

    op.add_column("inspections", sa.Column("hvac_brand", sa.String(100), nullable=True))
    op.add_column("inspections", sa.Column("hvac_age", sa.Integer(), nullable=True))
    op.add_column("inspections", sa.Column("hvac_model", sa.String(100), nullable=True))
    op.add_column("inspections", sa.Column("hvac_series", sa.String(100), nullable=True))

    op.add_column(
        "inspections",
        sa.Column("appliances", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
    )
    op.add_column(
        "inspections",
        sa.Column("rooms", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
    )

    op.add_column(
        "inspections",
        sa.Column("wind_mit_doors_protected", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "inspections",
        sa.Column("wind_mit_windows_protected", sa.Boolean(), nullable=False, server_default="false"),
    )

    # ── report_snapshots (ADR-024 D4 component 2 — immutable publish snapshot) ──
    op.create_table(
        "report_snapshots",
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
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pdf_s3_key", sa.String(1024), nullable=True),
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
            ["tenant_id"], ["tenants.id"],
            name="fk_report_snapshots_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"], ["inspections.id"],
            name="fk_report_snapshots_inspection_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["published_by"], ["inspector_profiles.id"],
            name="fk_report_snapshots_published_by", ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_report_snapshots_tenant_inspection",
        "report_snapshots",
        ["tenant_id", "inspection_id"],
    )

    op.execute("ALTER TABLE report_snapshots ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE report_snapshots FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON report_snapshots
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON report_snapshots TO app_role")

    # ── inspector_narrative_library (ADR-024 D6 — AI suggestion corpus, Phase 1) ─
    op.create_table(
        "inspector_narrative_library",
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
        sa.Column("inspector_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("system", sa.String(50), nullable=False),
        sa.Column(
            "trigger_keywords",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("narrative_text", sa.Text(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
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
            ["tenant_id"], ["tenants.id"],
            name="fk_inspector_narrative_library_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspector_id"], ["inspector_profiles.id"],
            name="fk_inspector_narrative_library_inspector_id", ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_inspector_narrative_library_tenant_inspector_system",
        "inspector_narrative_library",
        ["tenant_id", "inspector_id", "system"],
    )

    op.execute("ALTER TABLE inspector_narrative_library ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inspector_narrative_library FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON inspector_narrative_library
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON inspector_narrative_library TO app_role")


def downgrade() -> None:
    # ── total_fee: restore NOT NULL ─────────────────────────────────────────────
    op.alter_column("inspections", "total_fee", nullable=False)

    # ── inspector_narrative_library ─────────────────────────────────────────────
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON inspector_narrative_library")
    op.drop_table("inspector_narrative_library", if_exists=True)

    # ── report_snapshots ─────────────────────────────────────────────────────────
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON report_snapshots")
    op.drop_table("report_snapshots", if_exists=True)

    # ── new fields ───────────────────────────────────────────────────────────────
    op.drop_column("inspections", "wind_mit_windows_protected")
    op.drop_column("inspections", "wind_mit_doors_protected")
    op.drop_column("inspections", "rooms")
    op.drop_column("inspections", "appliances")
    op.drop_column("inspections", "hvac_series")
    op.drop_column("inspections", "hvac_model")
    op.drop_column("inspections", "hvac_age")
    op.drop_column("inspections", "hvac_brand")
    op.drop_column("inspections", "electrical_location")
    op.drop_column("inspections", "electrical_amps")
    op.drop_column("inspections", "electrical_brand")
    op.drop_column("inspections", "water_heater_capacity")
    op.drop_column("inspections", "water_heater_location")
    op.drop_column("inspections", "water_heater_type")
    op.drop_column("inspections", "roof_type")
    op.drop_column("inspections", "roof_style")
    op.drop_column("inspections", "roof_date")
    op.drop_column("inspections", "roof_permit_number")
    op.drop_column("inspections", "adj_sqft")
    op.drop_column("inspections", "year_built")

    # ── rename contact columns back ─────────────────────────────────────────────
    op.alter_column("inspections", "lockbox", new_column_name="lockbox_code")
    op.alter_column("inspections", "listing_agent_cell", new_column_name="listing_agent_phone")
    op.alter_column("inspections", "owner_buyer_cell", new_column_name="owner_buyer_phone")
    op.alter_column("inspections", "realtor_cell", new_column_name="realtor_phone")

    # ── scheduled_at -> scheduled_date + scheduled_time ─────────────────────────
    op.drop_index("ix_inspections_scheduled_at", table_name="inspections")
    op.add_column("inspections", sa.Column("scheduled_date", sa.Date(), nullable=True))
    op.add_column("inspections", sa.Column("scheduled_time", sa.Time(), nullable=True))
    op.execute("""
        UPDATE inspections
        SET scheduled_date = (scheduled_at AT TIME ZONE 'UTC')::date,
            scheduled_time = (scheduled_at AT TIME ZONE 'UTC')::time
    """)
    op.alter_column("inspections", "scheduled_date", nullable=False)
    op.drop_column("inspections", "scheduled_at")
    op.create_index("ix_inspections_scheduled_date", "inspections", ["scheduled_date"])

    # ── inspector_id -> drop ─────────────────────────────────────────────────────
    op.drop_index("ix_inspections_inspector_id", table_name="inspections")
    op.drop_constraint("fk_inspections_inspector_id", "inspections", type_="foreignkey")
    op.drop_column("inspections", "inspector_id")

    # ── property_address -> property_id ─────────────────────────────────────────
    # NOTE: data is not recoverable — there is no property_id to restore to.
    # Acceptable for Phase 0 (no production workloads, CLAUDE.md).
    op.drop_column("inspections", "property_address")
    op.add_column("inspections", sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_inspections_property_id", "inspections", "properties", ["property_id"], ["id"], ondelete="CASCADE",
    )
    op.create_index("ix_inspections_property_id", "inspections", ["property_id"])

    # ── status: ADR-024 FSM -> SCHEDULED/IN_PROGRESS/COMPLETED/CANCELLED ────────
    op.execute(f"CREATE TYPE inspection_status_enum_old AS ENUM ({_OLD_STATUSES})")
    op.execute("ALTER TABLE inspections ALTER COLUMN status DROP DEFAULT")
    op.execute("""
        ALTER TABLE inspections
        ALTER COLUMN status TYPE inspection_status_enum_old
        USING (
            CASE status::text
                WHEN 'DRAFT'           THEN 'SCHEDULED'
                WHEN 'IN_FIELD'        THEN 'IN_PROGRESS'
                WHEN 'PENDING_REVIEW'  THEN 'IN_PROGRESS'
                WHEN 'PUBLISHED'       THEN 'COMPLETED'
                WHEN 'DELIVERED'       THEN 'COMPLETED'
            END
        )::inspection_status_enum_old
    """)
    op.execute("DROP TYPE inspection_status_enum")
    op.execute("ALTER TYPE inspection_status_enum_old RENAME TO inspection_status_enum")
    op.execute("ALTER TABLE inspections ALTER COLUMN status SET DEFAULT 'SCHEDULED'")

    # ── inspection_types: enum[] -> TEXT[] + CHECK (8 values) ───────────────────
    op.execute("ALTER TABLE inspections DROP CONSTRAINT ck_inspections_types_nonempty")
    op.execute("""
        ALTER TABLE inspections
        ALTER COLUMN inspection_types
        TYPE text[]
        USING inspection_types::text[]
    """)
    op.execute("DROP TYPE inspection_type_enum")
    op.execute(f"""
        ALTER TABLE inspections
        ADD CONSTRAINT ck_inspections_types_valid
        CHECK (
            inspection_types <@ ARRAY[{_OLD_TYPES}]::text[]
            AND array_length(inspection_types, 1) >= 1
        )
    """)
