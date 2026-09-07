"""Background purge of old sessions.

Second layer of defence behind rate limiting. Rate limiting is what stops a
flood; this is what stops a burst permanently consuming disk — which matters
because Postgres filling a small Lightsail volume takes down Caddy and its
certificates with it, not just the quiz.

Runs in-process rather than via pg_cron (absent from postgres:16-alpine) or a
host crontab (which the club forgets exists and which breaks silently when a
container is renamed). There is exactly one backend container, so there is no
duplicate-runner problem.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.db.database import engine
from app.db.models import sessions

log = logging.getLogger(__name__)

# Long enough to survive recruitment week and let the club review which
# departments were recommended; short enough that the table cannot grow
# without bound.
RETENTION = timedelta(days=14)
INTERVAL_SECONDS = 6 * 60 * 60


def purge_once() -> int:
    """Delete sessions older than RETENTION. Returns the row count."""
    cutoff = datetime.now(timezone.utc) - RETENTION
    with engine.begin() as conn:
        result = conn.execute(sessions.delete().where(sessions.c.created_at < cutoff))
        return result.rowcount or 0


async def purge_loop() -> None:
    """Purge every INTERVAL_SECONDS, forever.

    Never allowed to raise: a transient database blip must not take down the
    API, so failures are logged and retried on the next tick. Runs the sync
    query in a thread so it cannot block the event loop.
    """
    while True:
        try:
            deleted = await asyncio.to_thread(purge_once)
            if deleted:
                log.info("purged %d session(s) older than %s", deleted, RETENTION)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("session purge failed; will retry next cycle")
        await asyncio.sleep(INTERVAL_SECONDS)
