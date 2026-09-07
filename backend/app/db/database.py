from sqlalchemy import create_engine

from app.config import settings

# Pool sizing is deliberate, not decoration. Endpoints are sync `def`, so
# Starlette runs them on a ~40-thread pool; with SQLAlchemy's defaults (5 + 10
# overflow, 30s timeout) about 15 concurrent requests exhaust the pool and the
# next 25 each block a worker thread for half a minute. That turns a small
# burst into an outage.
#
# Sizing the pool to the threadpool means no request ever queues on it, and the
# short timeout is a backstop that fails fast instead of holding a thread.
# 40 total is well under Postgres 16's default max_connections of 100.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
    pool_timeout=5,
    pool_recycle=1800,
)
