import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    # Kept as a local-dev convenience default. It cannot silently weaken
    # production: there is no Postgres on localhost inside the container, and
    # require_production_config() below refuses to start if DATABASE_URL was
    # not supplied explicitly when ENV=production.
    database_url: str = "postgresql+psycopg://taqneeq:taqneeq@localhost:5434/taqneeq"
    cors_origins: str = "http://localhost:3000"
    data_dir: str = "app/data"

    @field_validator("database_url")
    @classmethod
    def _pin_driver(cls, value: str) -> str:
        """Force the psycopg3 driver when the URL does not name one.

        Railway (and Render, Heroku and most managed Postgres providers) hand
        out a bare `postgresql://` URL, and Railway's older plugins used
        `postgres://`. SQLAlchemy reads `postgresql://` as *psycopg2*, which
        this project does not install — so the app dies at import with
        "ModuleNotFoundError: No module named 'psycopg2'" even though the URL
        looks entirely valid. Rewriting the scheme to the driver pinned in
        requirements.txt is what makes the provider's own variable usable
        as-is, with no hand-editing of the connection string.

        A URL that already names a driver (`postgresql+psycopg://`, or an
        explicit `postgresql+asyncpg://`) is returned untouched.
        """
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


def require_production_config() -> None:
    """Fail at startup, not on the first request, if production is misconfigured.

    Checks the environment directly rather than the parsed setting, because a
    default is indistinguishable from an explicitly-supplied identical value
    once pydantic has loaded it.
    """
    if not settings.is_production:
        return

    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("ENV=production requires DATABASE_URL to be set explicitly")
    if not os.getenv("CORS_ORIGINS"):
        raise RuntimeError("ENV=production requires CORS_ORIGINS to be set explicitly")
    if "*" in settings.cors_origins_list:
        raise RuntimeError("CORS_ORIGINS must not be '*' in production")
