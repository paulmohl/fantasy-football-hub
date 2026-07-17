import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # Database — DO provides postgresql://, asyncpg needs postgresql+asyncpg://
    database_url: str = "postgresql+asyncpg://ffhub:ffhub@localhost:5432/ffhub"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_db_scheme(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        # asyncpg doesn't accept sslmode (psycopg2-only param) — strip it
        v = re.sub(r"[?&]sslmode=[^&]*", "", v).rstrip("?&")
        return v

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    @field_validator("redis_url", mode="before")
    @classmethod
    def fix_redis_scheme(cls, v: str) -> str:
        v = (v or "").strip().strip("\"'")
        if not v:
            return "redis://localhost:6379/0"
        if not v.startswith(("redis://", "rediss://", "unix://")):
            return f"redis://{v}"
        return v

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15

    is_production: bool = False

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Email (fastapi-mail)
    mail_server: str = ""
    mail_port: int = 587
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "noreply@fantasyfootballhub.com"
    mail_tls: bool = True

    # Sentry
    sentry_dsn: str = ""

    # Sleeper (no auth needed — public API)
    sleeper_api_base: str = "https://api.sleeper.app/v1"

    # Yahoo OAuth (Phase 3)
    yahoo_client_id: str = ""
    yahoo_client_secret: str = ""
    yahoo_redirect_uri: str = "http://localhost:8000/api/v1/auth/yahoo/callback"

    # ESPN (unofficial API — no auth key, uses session cookies for private leagues)
    espn_api_base: str = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"

    # Active NFL season year — increment each September; used by ESPN routes
    nfl_season_year: int = 2025


settings = Settings()
