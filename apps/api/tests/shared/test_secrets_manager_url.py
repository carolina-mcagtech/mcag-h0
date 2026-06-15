# tests/shared/test_secrets_manager_url.py
import json
from unittest.mock import MagicMock, patch

from app.shared.db.session import (
    _build_url_from_secret,
    _get_admin_database_url,
    _get_migrations_database_url,
)


def _mock_secretsmanager_client(secret: dict) -> MagicMock:
    client = MagicMock()
    client.get_secret_value.return_value = {"SecretString": json.dumps(secret)}
    return client


def test_build_url_uses_secret_host_and_dbname_by_default():
    secret = {
        "username": "mcagapp",
        "password": "s3cret",
        "host": "secret-endpoint.example.com",
        "port": 5432,
        "dbname": "postgres",
    }
    with (
        patch("app.shared.db.session.boto3.client", return_value=_mock_secretsmanager_client(secret)),
        patch("app.shared.db.session.settings.db_host", None),
        patch("app.shared.db.session.settings.db_name", None),
    ):
        url = _build_url_from_secret("arn:aws:secretsmanager:us-east-1:123:secret:db")

    assert url == "postgresql+asyncpg://mcagapp:s3cret@secret-endpoint.example.com:5432/postgres"


def test_build_url_overrides_host_and_dbname_from_settings():
    """Aurora managed secrets often carry the cluster's default host/dbname,
    not the real writer endpoint / app database — DB_HOST / DB_NAME win."""
    secret = {
        "username": "mcagapp",
        "password": "s3cret",
        "host": "secret-endpoint.example.com",
        "port": 5432,
        "dbname": "postgres",
    }
    with (
        patch("app.shared.db.session.boto3.client", return_value=_mock_secretsmanager_client(secret)),
        patch("app.shared.db.session.settings.db_host", "prod-cluster.cluster-xyz.us-east-1.rds.amazonaws.com"),
        patch("app.shared.db.session.settings.db_name", "mcagtech"),
    ):
        url = _build_url_from_secret("arn:aws:secretsmanager:us-east-1:123:secret:db")

    assert url == (
        "postgresql+asyncpg://mcagapp:s3cret"
        "@prod-cluster.cluster-xyz.us-east-1.rds.amazonaws.com:5432/mcagtech"
    )


def test_migrations_url_uses_db_host_and_db_name_with_aurora_managed_secret():
    """Aurora managed-master-password secrets only carry username/password
    (and sometimes port) — no 'host' or 'dbname' keys. DB_HOST / DB_NAME
    must supply those, or _build_url_from_secret would KeyError."""
    secret = {"username": "mcagadmin", "password": "s3cret"}
    _get_migrations_database_url.cache_clear()
    try:
        with (
            patch(
                "app.shared.db.session.boto3.client",
                return_value=_mock_secretsmanager_client(secret),
            ),
            patch("app.shared.db.session.settings.migrations_database_secret_arn", "arn:migrations"),
            patch("app.shared.db.session.settings.database_secret_arn", None),
            patch("app.shared.db.session.settings.database_url", None),
            patch(
                "app.shared.db.session.settings.db_host",
                "prod-cluster.cluster-xyz.us-east-1.rds.amazonaws.com",
            ),
            patch("app.shared.db.session.settings.db_name", "mcagtech"),
            patch("app.shared.db.session.settings.db_port", None),
        ):
            url = _get_migrations_database_url()
    finally:
        _get_migrations_database_url.cache_clear()

    assert url == (
        "postgresql+asyncpg://mcagadmin:s3cret"
        "@prod-cluster.cluster-xyz.us-east-1.rds.amazonaws.com:5432/mcagtech"
    )


def test_admin_url_uses_db_host_and_db_name_with_aurora_managed_secret():
    """Same Aurora managed-secret shape (no host/dbname) for mcagapp_admin."""
    secret = {"username": "mcagapp_admin", "password": "s3cret"}
    _get_admin_database_url.cache_clear()
    try:
        with (
            patch(
                "app.shared.db.session.boto3.client",
                return_value=_mock_secretsmanager_client(secret),
            ),
            patch("app.shared.db.session.settings.database_admin_secret_arn", "arn:admin"),
            patch(
                "app.shared.db.session.settings.db_host",
                "prod-cluster.cluster-xyz.us-east-1.rds.amazonaws.com",
            ),
            patch("app.shared.db.session.settings.db_name", "mcagtech"),
            patch("app.shared.db.session.settings.db_port", None),
        ):
            url = _get_admin_database_url()
    finally:
        _get_admin_database_url.cache_clear()

    assert url == (
        "postgresql+asyncpg://mcagapp_admin:s3cret"
        "@prod-cluster.cluster-xyz.us-east-1.rds.amazonaws.com:5432/mcagtech"
    )
