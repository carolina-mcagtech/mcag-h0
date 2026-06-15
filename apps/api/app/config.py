# app/config.py
from typing import Optional

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: Optional[str] = None
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    cors_origins: list[str] = ["http://localhost:3000"]

    environment: str = "local"
    database_secret_arn: Optional[str] = None
    database_admin_secret_arn: str = ""
    # ADR-024 fix: dedicated secret for Alembic migrations (mcagadmin), separate
    # from the app runtime user. Falls back to database_secret_arn for local dev.
    migrations_database_secret_arn: Optional[str] = None
    use_secrets_manager: bool = False
    internal_api_token: str = "change-me-internal-token"
    # ADR-018: key for POST /tenants; must be set in production
    admin_api_key: str = ""
    # ADR-018: gate for /internal/* routes — disabled by default, never public
    internal_routes_enabled: bool = False

    # Legacy fields — used by app/shared/auth/cognito.py
    cognito_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_region: str = "us-east-1"

    # New canonical Cognito fields (ALB / ECS contract)
    cognito_user_pool_id: str = ""
    cognito_jwks_uri: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwks_url(self) -> str:
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com"
            f"/{self.cognito_pool_id}/.well-known/jwks.json"
        )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v  # type: ignore[return-value]


settings = Settings()
