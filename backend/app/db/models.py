"""Single `sessions` table storing session state as JSONB.

One table, no ORM relationships, no Alembic — the schema has no planned
evolution. Add a migration tool only if that changes.
"""
from sqlalchemy import TIMESTAMP, Boolean, Column, MetaData, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = MetaData()

sessions = Table(
    "sessions",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("questions_asked", JSONB, nullable=False, server_default="[]"),
    Column("responses", JSONB, nullable=False, server_default="{}"),
    Column("trait_scores", JSONB, nullable=False),
    Column("probabilities", JSONB, nullable=False, server_default="{}"),
    Column("completed", Boolean, nullable=False, server_default="false"),
    Column("recommended_department", String, nullable=True),
    # Indexed because the session reaper filters on it (app/db/cleanup.py).
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now(), index=True),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)
