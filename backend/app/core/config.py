from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "postgresql+psycopg://ffhub:ffhub@localhost:5432/ffhub"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Sentry
    sentry_dsn: str = ""

    # Sleeper (no auth needed — public API)
    sleeper_api_base: str = "https://api.sleeper.app/v1"

    # Yahoo OAuth (Phase 1 — Sleeper only, Yahoo in later phase)
    yahoo_client_id: str = ""
    yahoo_client_secret: str = ""
    yahoo_redirect_uri: str = "http://localhost:8000/api/v1/auth/yahoo/callback"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
