# tests/test_config.py
from app.config import Settings


def test_cognito_allowed_client_ids_from_csv_env_var(monkeypatch) -> None:
    """COGNITO_ALLOWED_CLIENT_IDS as a CSV env var must not trip pydantic-settings'
    JSON decoding for list[str] fields (NoDecode + _split_csv)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    monkeypatch.setenv("COGNITO_ALLOWED_CLIENT_IDS", "web-client-id, scripts-client-id")

    s = Settings()

    assert s.cognito_allowed_client_ids == ["web-client-id", "scripts-client-id"]


def test_cors_origins_from_csv_env_var(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://app.example.com")

    s = Settings()

    assert s.cors_origins == ["http://localhost:3000", "https://app.example.com"]


def test_cognito_allowed_client_ids_parses_csv_init_string() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        cognito_allowed_client_ids="web-client-id, scripts-client-id",
    )
    assert s.cognito_allowed_client_ids == ["web-client-id", "scripts-client-id"]


def test_cognito_allowed_client_ids_defaults_to_cognito_client_id() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        cognito_client_id="default-client-id",
    )
    assert s.cognito_allowed_client_ids == ["default-client-id"]
