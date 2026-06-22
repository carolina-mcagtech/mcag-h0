# alembic/versions/013_add_photos_to_findings.py
"""add photos column to findings

Revision ID: 013
Revises: 012
Create Date: 2026-06-22
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'findings' AND column_name = 'photos'
            ) THEN
                ALTER TABLE findings
                    ADD COLUMN photos JSONB NOT NULL DEFAULT '[]';
            END IF;
        END $$
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'findings' AND column_name = 'photos'
            ) THEN
                ALTER TABLE findings DROP COLUMN photos;
            END IF;
        END $$
    """)
