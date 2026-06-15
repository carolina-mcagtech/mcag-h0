# tests/conftest.py
#
# The tenants table is owned by Alembic (migration 001). The conftest must NOT
# drop or recreate it — only manage test data. The RLS policy and app_role are
# also created by the migration; the fixture below ensures they exist for the
# benefit of fresh test-only databases (e.g. CI without prior migration run).

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
import app.modules.tenants.models  # noqa: F401 — registers metadata
import app.modules.inspectors.models  # noqa: F401 — registers metadata
import app.modules.properties.models  # noqa: F401 — registers metadata
import app.modules.inspections.models  # noqa: F401 — registers metadata
import app.modules.agreements.models  # noqa: F401 — registers metadata
import app.modules.findings.models  # noqa: F401 — registers metadata
import app.modules.reports.models  # noqa: F401 — registers metadata
import app.modules.media.models  # noqa: F401 — registers metadata


@pytest_asyncio.fixture(autouse=True)
async def _dispose_session_engine() -> None:
    """Dispose the shared session engine after every test.

    pytest-asyncio gives each test its own event loop. asyncpg connections are
    bound to the loop that created them, so a pooled connection from test N
    will raise "Future attached to a different loop" in test N+1. Disposing
    after each test ensures the next test always opens a fresh connection.
    """
    yield
    from app.shared.db.session import get_engine
    await get_engine().dispose()


@pytest_asyncio.fixture(autouse=True)
async def _dispose_admin_engine() -> None:
    """Dispose admin engine after every test — same event-loop isolation as above."""
    yield
    import app.shared.db.session as _sess
    if _sess._admin_engine is not None:
        await _sess._admin_engine.dispose()


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        # Idempotent safety net: if tests run against a DB without the migration,
        # ensure the table and RLS exist before any test touches them.

        # Enum types (migrations 003+)
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'plan_enum') THEN
                    CREATE TYPE plan_enum AS ENUM ('STARTER', 'PROFESSIONAL', 'AGENCY');
                END IF;
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'custom_domain_status_enum') THEN
                    CREATE TYPE custom_domain_status_enum AS ENUM
                        ('PENDING_VERIFICATION', 'PENDING_CERT', 'ACTIVE', 'FAILED');
                END IF;
            END $$
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tenants (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name        VARCHAR(255) NOT NULL,
                subdomain   VARCHAR(63)  NOT NULL,
                custom_domain VARCHAR(253),
                is_active   BOOLEAN NOT NULL DEFAULT true,
                plan        plan_enum NOT NULL DEFAULT 'STARTER',
                custom_domain_status custom_domain_status_enum,
                theme_config JSONB NOT NULL DEFAULT '{}',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT uq_tenants_subdomain UNIQUE (subdomain)
            )
        """))

        # Add columns introduced in migration 003 if the table already existed
        # without them (e.g. CI database that ran migration 001/002 only).
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'tenants' AND column_name = 'plan'
                ) THEN
                    ALTER TABLE tenants ADD COLUMN plan plan_enum NOT NULL DEFAULT 'STARTER';
                END IF;
                IF NOT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'tenants' AND column_name = 'custom_domain_status'
                ) THEN
                    ALTER TABLE tenants ADD COLUMN custom_domain_status custom_domain_status_enum;
                END IF;
                IF NOT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'tenants' AND column_name = 'theme_config'
                ) THEN
                    ALTER TABLE tenants ADD COLUMN theme_config JSONB NOT NULL DEFAULT '{}';
                END IF;
            END $$
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_role') THEN
                    CREATE ROLE app_role;
                END IF;
            END $$
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE tenants FORCE ROW LEVEL SECURITY")
        )
        # DROP ... IF EXISTS so re-running the fixture (e.g. in watch mode)
        # doesn't error on a duplicate policy name.
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON tenants")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON tenants
            USING (
                id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── inspector_profiles safety net ────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inspector_profiles (
                id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id           UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                cognito_sub         UUID NOT NULL,
                full_name           VARCHAR(255) NOT NULL,
                email               VARCHAR(255) NOT NULL,
                phone               VARCHAR(20),
                license_number      VARCHAR(50) NOT NULL,
                license_expiry_date DATE NOT NULL,
                created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT uq_inspector_profiles_cognito_sub UNIQUE (cognito_sub)
            )
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON inspector_profiles TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE inspector_profiles ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE inspector_profiles FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON inspector_profiles")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON inspector_profiles
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── properties safety net ────────────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS properties (
                id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id             UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                street                VARCHAR(255) NOT NULL,
                city                  VARCHAR(100) NOT NULL,
                state                 VARCHAR(2)   NOT NULL DEFAULT 'FL',
                zip_code              VARCHAR(10)  NOT NULL,
                year_built            INTEGER,
                adjusted_sqft         INTEGER,
                roof_permit_number    VARCHAR(50),
                roof_permit_date      DATE,
                roof_style            VARCHAR(100),
                roof_type             VARCHAR(100),
                water_heater_type     VARCHAR(100),
                water_heater_location VARCHAR(100),
                water_heater_capacity VARCHAR(50),
                electrical_brand      VARCHAR(100),
                electrical_amps       INTEGER,
                electrical_location   VARCHAR(100),
                ac_brand              VARCHAR(100),
                ac_age                INTEGER,
                ac_model              VARCHAR(100),
                ac_series             VARCHAR(100),
                mit_doors_protection   BOOLEAN,
                mit_windows_protection BOOLEAN,
                appliances            JSONB NOT NULL DEFAULT '{}',
                bedrooms              JSONB NOT NULL DEFAULT '{}',
                bathrooms             JSONB NOT NULL DEFAULT '{}',
                created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON properties TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE properties ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE properties FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON properties")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON properties
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── inspections safety net (ADR-024 schema) ──────────────────────────
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'inspection_status_enum') THEN
                    CREATE TYPE inspection_status_enum AS ENUM
                        ('DRAFT','IN_FIELD','PENDING_REVIEW','PUBLISHED','DELIVERED');
                END IF;
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'payment_timing_enum') THEN
                    CREATE TYPE payment_timing_enum AS ENUM
                        ('AT_PROPERTY','AT_DELIVERY','AFTER_DELIVERY');
                END IF;
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'inspection_type_enum') THEN
                    CREATE TYPE inspection_type_enum AS ENUM (
                        'FULL_INSPECTION','WIND_MITIGATION','FOUR_POINT','MOLD_INSPECTION',
                        'TERMITES','ROOF_CERTIFICATION','OPENING_PROTECTION','SEWER_INSPECTION',
                        'LEAD_PAINT_INSPECTION','WATER_QUALITY_TEST'
                    );
                END IF;
            END $$
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inspections (
                id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id               UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                inspector_id            UUID NOT NULL
                    REFERENCES inspector_profiles(id) ON DELETE RESTRICT,
                status                  inspection_status_enum NOT NULL DEFAULT 'DRAFT',
                scheduled_at            TIMESTAMPTZ NOT NULL,
                property_address        VARCHAR(500) NOT NULL,
                year_built              INTEGER,
                adj_sqft                INTEGER,
                inspection_types        inspection_type_enum[] NOT NULL,
                realtor_name            VARCHAR(255),
                realtor_cell            VARCHAR(20),
                owner_buyer_name        VARCHAR(255),
                owner_buyer_cell        VARCHAR(20),
                owner_buyer_email       VARCHAR(255),
                listing_agent_name      VARCHAR(255),
                listing_agent_cell      VARCHAR(20),
                additional_notes        TEXT,
                gate_code               VARCHAR(50),
                lockbox                 VARCHAR(50),
                total_fee               NUMERIC(10,2) NOT NULL,
                payment_timing          payment_timing_enum NOT NULL DEFAULT 'AT_PROPERTY',
                full_report_number      VARCHAR(50),
                insurance_report_number VARCHAR(50),
                roof_permit_number      VARCHAR(50),
                roof_date               DATE,
                roof_style              VARCHAR(100),
                roof_type               VARCHAR(100),
                water_heater_type       VARCHAR(100),
                water_heater_location   VARCHAR(100),
                water_heater_capacity   VARCHAR(50),
                electrical_brand        VARCHAR(100),
                electrical_amps         INTEGER,
                electrical_location     VARCHAR(100),
                hvac_brand              VARCHAR(100),
                hvac_age                INTEGER,
                hvac_model              VARCHAR(100),
                hvac_series             VARCHAR(100),
                appliances              JSONB NOT NULL DEFAULT '{}',
                rooms                   JSONB NOT NULL DEFAULT '{}',
                wind_mit_doors_protected   BOOLEAN NOT NULL DEFAULT false,
                wind_mit_windows_protected BOOLEAN NOT NULL DEFAULT false,
                created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT ck_inspections_types_nonempty
                    CHECK (cardinality(inspection_types) >= 1)
            )
        """))
        # Partial unique indexes for report numbers (idempotent)
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_indexes WHERE indexname = 'uix_inspections_tenant_full_report'
                ) THEN
                    CREATE UNIQUE INDEX uix_inspections_tenant_full_report
                        ON inspections (tenant_id, full_report_number)
                        WHERE full_report_number IS NOT NULL;
                END IF;
                IF NOT EXISTS (
                    SELECT FROM pg_indexes WHERE indexname = 'uix_inspections_tenant_insurance_report'
                ) THEN
                    CREATE UNIQUE INDEX uix_inspections_tenant_insurance_report
                        ON inspections (tenant_id, insurance_report_number)
                        WHERE insurance_report_number IS NOT NULL;
                END IF;
            END $$
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON inspections TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE inspections ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE inspections FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON inspections")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON inspections
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── agreements safety net ────────────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agreements (
                id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id                 UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                inspection_id             UUID NOT NULL UNIQUE
                    REFERENCES inspections(id) ON DELETE CASCADE,
                client_name               VARCHAR(255) NOT NULL,
                property_address          VARCHAR(500) NOT NULL,
                inspection_date           DATE NOT NULL,
                fee_amount                NUMERIC(10,2) NOT NULL,
                payment_timing            VARCHAR(20) NOT NULL,
                liquidated_damages_amount NUMERIC(10,2) NOT NULL,
                agreement_version         VARCHAR(50) NOT NULL DEFAULT 'InterNACHI-Feb-2019',
                signed_by_client          BOOLEAN NOT NULL DEFAULT false,
                signed_at                 TIMESTAMPTZ,
                signature_data_url        VARCHAR(2048),
                exclusions_acknowledged   BOOLEAN NOT NULL DEFAULT false,
                created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at                TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON agreements TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE agreements ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE agreements FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON agreements")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON agreements
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── findings safety net ──────────────────────────────────────────────
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'section_enum') THEN
                    CREATE TYPE section_enum AS ENUM (
                        'FRONT','EXTERIOR','INSULATION','PLUMBING','STRUCTURAL',
                        'ELECTRICAL','ROOF','KITCHEN','INTERIOR','AIR_CONDITIONING',
                        'COMMENTS','COST_ESTIMATION','COUNTY_INFO','DISCLOSURE'
                    );
                END IF;
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'condition_enum') THEN
                    CREATE TYPE condition_enum AS ENUM ('GOOD','MARGINAL','DEFECTIVE','N_A');
                END IF;
            END $$
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS findings (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id       UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                inspection_id   UUID NOT NULL
                    REFERENCES inspections(id) ON DELETE CASCADE,
                section         section_enum NOT NULL,
                item            TEXT NOT NULL,
                condition       condition_enum,
                observations    TEXT,
                estimated_cost  NUMERIC(10,2),
                sort_order      INTEGER NOT NULL DEFAULT 0,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT ck_findings_estimated_cost_section
                    CHECK (estimated_cost IS NULL OR section = 'COST_ESTIMATION')
            )
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = 'ix_findings_tenant_inspection_section'
                ) THEN
                    CREATE INDEX ix_findings_tenant_inspection_section
                        ON findings (tenant_id, inspection_id, section);
                END IF;
            END $$
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON findings TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE findings ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE findings FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON findings")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON findings
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── report_jobs safety net ───────────────────────────────────────────
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'report_template_enum') THEN
                    CREATE TYPE report_template_enum AS ENUM ('FULL', 'INSURANCE');
                END IF;
                IF NOT EXISTS (SELECT FROM pg_type WHERE typname = 'report_job_status_enum') THEN
                    CREATE TYPE report_job_status_enum AS ENUM
                        ('PENDING', 'GENERATING', 'COMPLETE', 'FAILED');
                END IF;
            END $$
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS report_jobs (
                id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id        UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                inspection_id    UUID NOT NULL
                    REFERENCES inspections(id) ON DELETE CASCADE,
                template         report_template_enum NOT NULL,
                status           report_job_status_enum NOT NULL DEFAULT 'PENDING',
                template_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
                s3_url           VARCHAR(2048),
                generated_at     TIMESTAMPTZ,
                error_message    TEXT,
                created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT uq_report_jobs_inspection_template
                    UNIQUE (inspection_id, template)
            )
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = 'ix_report_jobs_tenant_inspection_status'
                ) THEN
                    CREATE INDEX ix_report_jobs_tenant_inspection_status
                        ON report_jobs (tenant_id, inspection_id, status);
                END IF;
            END $$
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON report_jobs TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE report_jobs ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE report_jobs FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON report_jobs")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON report_jobs
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── media_assets safety net ──────────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS media_assets (
                id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id        UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                inspection_id    UUID NOT NULL
                    REFERENCES inspections(id) ON DELETE CASCADE,
                finding_id       UUID
                    REFERENCES findings(id) ON DELETE CASCADE,
                filename         VARCHAR(500) NOT NULL,
                s3_key           VARCHAR(1024) NOT NULL,
                s3_bucket        VARCHAR(255) NOT NULL DEFAULT '',
                content_type     VARCHAR(100) NOT NULL DEFAULT 'application/octet-stream',
                file_size_bytes  INTEGER,
                sort_order       INTEGER NOT NULL DEFAULT 0,
                uploaded_at      TIMESTAMPTZ,
                created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT uq_media_assets_s3_key UNIQUE (s3_key)
            )
        """))
        # Migration 011: pre-existing tables (created before content_type/s3_bucket
        # existed) still have the old mime_type column and lack s3_bucket.
        await conn.execute(text("""
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
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = 'ix_media_assets_tenant_inspection'
                ) THEN
                    CREATE INDEX ix_media_assets_tenant_inspection
                        ON media_assets (tenant_id, inspection_id);
                END IF;
                IF NOT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = 'ix_media_assets_finding_id'
                ) THEN
                    CREATE INDEX ix_media_assets_finding_id
                        ON media_assets (finding_id);
                END IF;
            END $$
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON media_assets TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE media_assets FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON media_assets")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON media_assets
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── report_snapshots safety net ──────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS report_snapshots (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id       UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                inspection_id   UUID NOT NULL
                    REFERENCES inspections(id) ON DELETE CASCADE,
                published_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
                published_by    UUID NOT NULL
                    REFERENCES inspector_profiles(id) ON DELETE RESTRICT,
                content_hash    VARCHAR(64) NOT NULL,
                snapshot_json   JSONB NOT NULL,
                pdf_s3_key      VARCHAR(1024),
                created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = 'ix_report_snapshots_tenant_inspection'
                ) THEN
                    CREATE INDEX ix_report_snapshots_tenant_inspection
                        ON report_snapshots (tenant_id, inspection_id);
                END IF;
            END $$
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON report_snapshots TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE report_snapshots ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE report_snapshots FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON report_snapshots")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON report_snapshots
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

        # ── inspector_narrative_library safety net ───────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inspector_narrative_library (
                id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id        UUID NOT NULL
                    DEFAULT (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid
                    REFERENCES tenants(id) ON DELETE CASCADE,
                inspector_id     UUID NOT NULL
                    REFERENCES inspector_profiles(id) ON DELETE CASCADE,
                system           VARCHAR(50) NOT NULL,
                trigger_keywords TEXT[] NOT NULL DEFAULT '{}',
                narrative_text   TEXT NOT NULL,
                usage_count      INTEGER NOT NULL DEFAULT 0,
                created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = 'ix_inspector_narrative_library_tenant_inspector_system'
                ) THEN
                    CREATE INDEX ix_inspector_narrative_library_tenant_inspector_system
                        ON inspector_narrative_library (tenant_id, inspector_id, system);
                END IF;
            END $$
        """))
        await conn.execute(
            text("GRANT SELECT, INSERT, UPDATE, DELETE ON inspector_narrative_library TO app_role")
        )
        await conn.execute(
            text("ALTER TABLE inspector_narrative_library ENABLE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("ALTER TABLE inspector_narrative_library FORCE ROW LEVEL SECURITY")
        )
        await conn.execute(
            text("DROP POLICY IF EXISTS tenant_isolation ON inspector_narrative_library")
        )
        await conn.execute(text("""
            CREATE POLICY tenant_isolation ON inspector_narrative_library
            USING (
                tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            )
        """))

    yield engine

    # Tear down only the rows this test session created — leave schema intact
    # so Alembic's version stamp stays valid. CASCADE propagates to
    # inspector_profiles, properties, and any future child tables via FK constraints.
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE tenants CASCADE"))

    await engine.dispose()
