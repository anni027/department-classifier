"""Connection strings from managed Postgres providers.

Railway (and Render, Heroku) hand out a bare ``postgresql://`` URL. SQLAlchemy
resolves that to psycopg2, which this project does not install, so without the
rewrite in Settings these deployments die at import with a ModuleNotFoundError
that never mentions the connection string.
"""
import pytest

from app.config import Settings


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        # Railway's `${{Postgres.DATABASE_URL}}`, and Render's equivalent.
        ("postgresql://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        # Railway's older plugin style, which SQLAlchemy rejects outright.
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        # A URL that already names a driver is left exactly as given.
        ("postgresql+psycopg://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql+asyncpg://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
    ],
)
def test_provider_urls_are_pinned_to_the_installed_driver(given, expected):
    assert Settings(database_url=given).database_url == expected
