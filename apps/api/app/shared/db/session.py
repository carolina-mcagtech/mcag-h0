# app/shared/db/session.py
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from functools import lru_cache

import boto3
from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)


def _build_url_from_secret(secret_arn: str) -> str:
    """Build an asyncpg URL from a Secrets Manager DB secret.

    Aurora's managed-master-password secret carries username/password/port
    (and often host/dbname), but the cluster's actual writer endpoint and
    app database name are supplied via DB_HOST / DB_NAME env vars and take
    precedence when set.
    """
    client = boto3.client("secretsmanager", region_name="us-east-1")
    secret = client.get_secret_value(SecretId=secret_arn)
    data = json.loads(secret["SecretString"])
    host = settings.db_host or data.get("host")
    dbname = settings.db_name or data.get("dbname")
    if not host or not dbname:
        raise RuntimeError(
            "DB host/dbname unresolved: set DB_HOST and DB_NAME env vars "
            "(Aurora managed secrets do not include host/dbname)."
        )
    return (
        f"postgresql+asyncpg://{data['username']}:{data['password']}"
        f"@{host}:{data['port']}/{dbname}"
    )


@lru_cache(maxsize=1)
def _get_database_url(sync: bool = False) -> str:
    if settings.database_url is not None:
        url = settings.database_url
    elif settings.database_secret_arn is not None:
        url = _build_url_from_secret(settings.database_secret_arn)
    else:
        raise ValueError("Neither DATABASE_URL nor DATABASE_SECRET_ARN is set")

    if sync:
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        url = url.replace("postgresql://", "postgresql+psycopg2://")

    return url


@lru_cache(maxsize=1)
def _get_migrations_database_url(sync: bool = False) -> str:
    """Return DB URL for Alembic migrations, run as mcagadmin (not the app user).

    Uses MIGRATIONS_DATABASE_SECRET_ARN when set. Falls back to
    DATABASE_SECRET_ARN, then DATABASE_URL, for local-dev compatibility.
    """
    secret_arn = settings.migrations_database_secret_arn or settings.database_secret_arn

    if secret_arn:
        url = _build_url_from_secret(secret_arn)
    elif settings.database_url is not None:
        url = settings.database_url
    else:
        raise ValueError(
            "Neither MIGRATIONS_DATABASE_SECRET_ARN, DATABASE_SECRET_ARN nor DATABASE_URL is set"
        )

    if sync:
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        url = url.replace("postgresql://", "postgresql+psycopg2://")

    return url


@lru_cache(maxsize=1)
def _get_admin_database_url() -> str:
    """Return asyncpg URL for mcagapp_admin (BYPASSRLS). Falls back to regular URL in local dev."""
    if settings.database_admin_secret_arn:
        return _build_url_from_secret(settings.database_admin_secret_arn)
    # Local dev: no separate admin credentials — reuse regular URL
    return _get_database_url()


_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            echo=settings.app_env == "development",
            pool_pre_ping=True,
        )
    return _engine


_admin_engine: AsyncEngine | None = None


def get_admin_engine() -> AsyncEngine:
    """Lazy engine for mcagapp_admin. Small pool — admin ops are infrequent (ADR-010)."""
    global _admin_engine
    if _admin_engine is None:
        _admin_engine = create_async_engine(
            _get_admin_database_url(),
            echo=settings.app_env == "development",
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
        )
    return _admin_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


def get_admin_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_admin_engine(), expire_on_commit=False)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Standard session dependency. get_session owns the transaction (ADR-023).

    session.begin() starts an explicit transaction. SET LOCAL is called inside it
    so the GUC is active for the entire request. Services must use flush() — never
    commit() — so they stay within this transaction and SET LOCAL survives.
    session.begin() commits on clean exit, rolls back on exception.
    """
    tenant_id: str | None = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No tenant context")

    async with get_session_factory()() as session:
        async with session.begin():
            # SET LOCAL does not support prepared-statement parameters in PostgreSQL.
            # tenant_id is pre-validated as UUID in TenantMiddleware — no injection risk.
            await session.execute(
                text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'")
            )
            session.info["tenant_id"] = uuid.UUID(tenant_id)
            yield session


async def get_admin_session() -> AsyncGenerator[AsyncSession, None]:
    """RLS bypass via mcagapp_admin DB user — BYPASSRLS, not superuser (ADR-010/ADR-018).

    No SET LOCAL needed: the DB user itself carries BYPASSRLS. get_admin_session
    owns the transaction lifecycle (ADR-023); services must flush(), never commit().

    Authorised uses (ADR-018):
    - Tenant creation: no tenant context exists for a brand-new tenant
    - Subdomain / custom-domain resolution in TenantMiddleware
    - Internal API endpoints that must see across all tenants

    Every other endpoint MUST use get_session() where RLS is always active.
    Never add new call-sites here without updating ADR-018.
    """
    async with get_admin_session_factory()() as session:
        async with session.begin():
            yield session
