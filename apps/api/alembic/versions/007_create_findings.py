# alembic/versions/007_create_findings.py
"""create findings table with RLS

Revision ID: 007
Revises: 006
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE section_enum AS ENUM ("
        "'FRONT','EXTERIOR','INSULATION','PLUMBING','STRUCTURAL','ELECTRICAL',"
        "'ROOF','KITCHEN','INTERIOR','AIR_CONDITIONING','COMMENTS',"
        "'COST_ESTIMATION','COUNTY_INFO','DISCLOSURE')"
    )
    op.execute(
        "CREATE TYPE condition_enum AS ENUM ('GOOD','MARGINAL','DEFECTIVE','N_A')"
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.create_table(
        "findings",
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
            "section",
            postgresql.ENUM(
                "FRONT", "EXTERIOR", "INSULATION", "PLUMBING", "STRUCTURAL",
                "ELECTRICAL", "ROOF", "KITCHEN", "INTERIOR", "AIR_CONDITIONING",
                "COMMENTS", "COST_ESTIMATION", "COUNTY_INFO", "DISCLOSURE",
                name="section_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("item", sa.Text(), nullable=False),
        sa.Column(
            "condition",
            postgresql.ENUM(
                "GOOD", "MARGINAL", "DEFECTIVE", "N_A",
                name="condition_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
            "estimated_cost IS NULL OR section = 'COST_ESTIMATION'",
            name="ck_findings_estimated_cost_section",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"],
            name="fk_findings_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"], ["inspections.id"],
            name="fk_findings_inspection_id", ondelete="CASCADE",
        ),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index(
        "ix_findings_tenant_inspection_section",
        "findings",
        ["tenant_id", "inspection_id", "section"],
    )

    # ── RLS ───────────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE findings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE findings FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON findings
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON findings TO app_role")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON findings")
    op.drop_table("findings", if_exists=True)
    op.execute("DROP TYPE IF EXISTS condition_enum")
    op.execute("DROP TYPE IF EXISTS section_enum")
