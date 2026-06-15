# alembic/versions/006_create_agreements.py
"""create agreements table with RLS

Revision ID: 006
Revises: 005
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agreements",
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
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("property_address", sa.String(500), nullable=False),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column("fee_amount", sa.Numeric(10, 2), nullable=False),
        # Reuses payment_timing_enum created by migration 005.
        sa.Column("payment_timing", sa.String(20), nullable=False),
        # Defaults to fee_amount * 1.5 — calculated in service, stored here.
        sa.Column("liquidated_damages_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "agreement_version",
            sa.String(50),
            nullable=False,
            server_default="InterNACHI-Feb-2019",
        ),
        sa.Column(
            "signed_by_client",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_data_url", sa.String(2048), nullable=True),
        sa.Column(
            "exclusions_acknowledged",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
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
        # One agreement per inspection
        sa.UniqueConstraint("inspection_id", name="uq_agreements_inspection_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"],
            name="fk_agreements_tenant_id", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["inspection_id"], ["inspections.id"],
            name="fk_agreements_inspection_id", ondelete="CASCADE",
        ),
    )

    op.create_index("ix_agreements_tenant_id", "agreements", ["tenant_id"])
    op.create_index("ix_agreements_inspection_id", "agreements", ["inspection_id"])

    op.execute("ALTER TABLE agreements ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agreements FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON agreements
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON agreements TO app_role")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON agreements")
    op.drop_table("agreements", if_exists=True)
