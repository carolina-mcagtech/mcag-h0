# alembic/versions/011_alter_media_assets_content_type_bucket.py
"""alter media_assets: mime_type -> content_type, add s3_bucket

Revision ID: 011
Revises: 010
Create Date: 2026-06-14
"""
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Defensive: some environments may have already been bootstrapped with
    # the post-ADR-025 column names via the test safety net, so guard both
    # changes on the column's current existence.
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'media_assets' AND column_name = 'mime_type'
            ) THEN
                ALTER TABLE media_assets RENAME COLUMN mime_type TO content_type;
            END IF;
            IF NOT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'media_assets' AND column_name = 's3_bucket'
            ) THEN
                ALTER TABLE media_assets ADD COLUMN s3_bucket VARCHAR(255) NOT NULL DEFAULT '';
            END IF;
        END $$
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'media_assets' AND column_name = 's3_bucket'
            ) THEN
                ALTER TABLE media_assets DROP COLUMN s3_bucket;
            END IF;
            IF EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'media_assets' AND column_name = 'content_type'
            ) THEN
                ALTER TABLE media_assets RENAME COLUMN content_type TO mime_type;
            END IF;
        END $$
    """)
