# alembic/versions/012_create_component_observations.py
"""create component_observations and section_metadata tables with RLS

Revision ID: 012
Revises: 011
Create Date: 2026-06-21
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Ensure mcagapp_admin has DDL privileges for this migration ────────────
    op.execute("GRANT CREATE ON SCHEMA public TO mcagapp_admin")
    op.execute("GRANT USAGE ON SCHEMA public TO mcagapp_admin")

    # ── component_observations ────────────────────────────────────────────────
    # condition uses VARCHAR(20) + CHECK constraint instead of a custom ENUM
    # type so that mcagapp_admin (no CREATE TYPE privilege) can run this migration.
    op.create_table(
        "component_observations",
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
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column("item_key", sa.Text(), nullable=False),
        sa.Column("item_label", sa.Text(), nullable=False),
        sa.Column("condition", sa.String(20), nullable=False),
        sa.CheckConstraint(
            "condition IN ('GOOD', 'MARGINAL', 'DEFECTIVE', 'N_A')",
            name="ck_co_condition",
        ),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("room_type", sa.Text(), nullable=True),
        sa.Column(
            "room_index",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("room_label", sa.Text(), nullable=True),
        sa.Column(
            "sort_order",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
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
            ["tenant_id"], ["tenants.id"],
            name="fk_co_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"], ["inspections.id"],
            name="fk_co_inspection_id", ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "inspection_id", "section", "item_key", "room_index",
            name="uq_co_inspection_section_item_room",
        ),
    )

    # ── section_metadata ──────────────────────────────────────────────────────
    op.create_table(
        "section_metadata",
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
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
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
            ["tenant_id"], ["tenants.id"],
            name="fk_sm_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"], ["inspections.id"],
            name="fk_sm_inspection_id", ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "inspection_id", "section",
            name="uq_sm_inspection_section",
        ),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index(
        "idx_co_tenant_inspection",
        "component_observations",
        ["tenant_id", "inspection_id"],
    )
    op.create_index(
        "idx_co_defective",
        "component_observations",
        ["tenant_id", "inspection_id"],
        postgresql_where=sa.text("condition = 'DEFECTIVE'"),
    )
    op.create_index(
        "idx_sm_tenant_inspection",
        "section_metadata",
        ["tenant_id", "inspection_id"],
    )

    # ── RLS: component_observations ───────────────────────────────────────────
    op.execute("ALTER TABLE component_observations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE component_observations FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON component_observations
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON component_observations TO app_role"
    )

    # ── RLS: section_metadata ─────────────────────────────────────────────────
    op.execute("ALTER TABLE section_metadata ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE section_metadata FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON section_metadata
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON section_metadata TO app_role")

    # ── Add num_bedrooms / num_bathrooms to inspections ───────────────────────
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'inspections' AND column_name = 'num_bedrooms'
            ) THEN
                ALTER TABLE inspections ADD COLUMN num_bedrooms SMALLINT NOT NULL DEFAULT 0;
            END IF;
            IF NOT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'inspections' AND column_name = 'num_bathrooms'
            ) THEN
                ALTER TABLE inspections ADD COLUMN num_bathrooms SMALLINT NOT NULL DEFAULT 0;
            END IF;
        END $$
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'inspections' AND column_name = 'num_bathrooms'
            ) THEN
                ALTER TABLE inspections DROP COLUMN num_bathrooms;
            END IF;
            IF EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'inspections' AND column_name = 'num_bedrooms'
            ) THEN
                ALTER TABLE inspections DROP COLUMN num_bedrooms;
            END IF;
        END $$
    """)
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON section_metadata")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON component_observations")
    op.drop_table("section_metadata", if_exists=True)
    op.drop_table("component_observations", if_exists=True)
