# alembic/versions/008_create_report_jobs.py
"""create report_jobs table with RLS

Revision ID: 008
Revises: 007
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE report_template_enum AS ENUM ('FULL', 'INSURANCE')"
    )
    op.execute(
        "CREATE TYPE report_job_status_enum AS ENUM ('PENDING', 'GENERATING', 'COMPLETE', 'FAILED')"
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.create_table(
        "report_jobs",
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
            "template",
            postgresql.ENUM(
                "FULL", "INSURANCE",
                name="report_template_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING", "GENERATING", "COMPLETE", "FAILED",
                name="report_job_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "template_version", sa.String(50), nullable=False, server_default="v1.0"
        ),
        sa.Column("s3_url", sa.String(2048), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.UniqueConstraint(
            "inspection_id", "template",
            name="uq_report_jobs_inspection_template",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"],
            name="fk_report_jobs_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"], ["inspections.id"],
            name="fk_report_jobs_inspection_id", ondelete="CASCADE",
        ),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index(
        "ix_report_jobs_tenant_inspection_status",
        "report_jobs",
        ["tenant_id", "inspection_id", "status"],
    )

    # ── RLS ───────────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE report_jobs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE report_jobs FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON report_jobs
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON report_jobs TO app_role")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON report_jobs")
    op.drop_table("report_jobs", if_exists=True)
    op.execute("DROP TYPE IF EXISTS report_job_status_enum")
    op.execute("DROP TYPE IF EXISTS report_template_enum")
