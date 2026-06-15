# app/config.py
from typing import Annotated, Optional

from pydantic import computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: Optional[str] = None
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    environment: str = "local"
    database_secret_arn: Optional[str] = None
    # Aurora cluster endpoint / database name to use instead of the values
    # baked into the Secrets Manager managed-master-password secret (which
    # may not reflect the actual cluster writer endpoint or app database).
    db_host: Optional[str] = None
    db_name: Optional[str] = None
    db_port: Optional[int] = None
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

    # Multi-client pool support: token issuer is validated against
    # cognito_pool_id, but the client id (aud for ID tokens, client_id for
    # access tokens) must be in this allowlist. Defaults to
    # [cognito_client_id] when not set.
    cognito_allowed_client_ids: Annotated[list[str], NoDecode] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwks_url(self) -> str:
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com"
            f"/{self.cognito_pool_id}/.well-known/jwks.json"
        )

    @field_validator("cognito_allowed_client_ids", "cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @model_validator(mode="after")
    def default_cognito_allowed_client_ids(self) -> "Settings":
        if not self.cognito_allowed_client_ids:
            self.cognito_allowed_client_ids = [self.cognito_client_id]
        return self


settings = Settings()
