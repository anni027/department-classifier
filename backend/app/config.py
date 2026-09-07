import os

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
