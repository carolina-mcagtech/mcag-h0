# alembic/versions/009_create_media_assets.py
"""create media_assets table with RLS

Revision ID: 009
Revises: 008
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
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
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column(
            "mime_type", sa.String(100), nullable=False, server_default="image/jpeg"
        ),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("s3_key", name="uq_media_assets_s3_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_media_assets_tenant_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"],
            ["inspections.id"],
            name="fk_media_assets_inspection_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name="fk_media_assets_finding_id",
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_media_assets_tenant_inspection",
        "media_assets",
        ["tenant_id", "inspection_id"],
    )
    op.create_index(
        "ix_media_assets_finding_id",
        "media_assets",
        ["finding_id"],
    )

    op.execute("ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE media_assets FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON media_assets
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON media_assets TO app_role")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON media_assets")
    op.drop_table("media_assets", if_exists=True)
