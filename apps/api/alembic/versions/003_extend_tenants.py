# alembic/versions/003_extend_tenants.py
"""extend tenants: plan, custom_domain_status, theme_config

Revision ID: 003
Revises: 002
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE plan_enum AS ENUM ('STARTER', 'PROFESSIONAL', 'AGENCY')"
    )
    op.execute(
        "CREATE TYPE custom_domain_status_enum AS ENUM "
        "('PENDING_VERIFICATION', 'PENDING_CERT', 'ACTIVE', 'FAILED')"
    )

    # ── New columns ───────────────────────────────────────────────────────────
    op.add_column(
        "tenants",
        sa.Column(
            "plan",
            postgresql.ENUM(
                "STARTER", "PROFESSIONAL", "AGENCY",
                name="plan_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="STARTER",
        ),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "custom_domain_status",
            postgresql.ENUM(
                "PENDING_VERIFICATION", "PENDING_CERT", "ACTIVE", "FAILED",
                name="custom_domain_status_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "theme_config",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )

    # ── Partial unique index: custom_domain where not null ────────────────────
    op.create_index(
        "ix_tenants_custom_domain",
        "tenants",
        ["custom_domain"],
        unique=True,
        postgresql_where=sa.text("custom_domain IS NOT NULL"),
    )

    # ── Subdomain format check ────────────────────────────────────────────────
    # Enforces [a-z0-9][a-z0-9-]{1,61}[a-z0-9]: 3–63 chars, no leading/trailing hyphens.
    op.create_check_constraint(
        "ck_tenants_subdomain_format",
        "tenants",
        r"subdomain ~ '^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tenants_subdomain_format", "tenants", type_="check")
    op.drop_index("ix_tenants_custom_domain", table_name="tenants")
    op.drop_column("tenants", "theme_config")
    op.drop_column("tenants", "custom_domain_status")
    op.drop_column("tenants", "plan")
    op.execute("DROP TYPE IF EXISTS custom_domain_status_enum")
    op.execute("DROP TYPE IF EXISTS plan_enum")
