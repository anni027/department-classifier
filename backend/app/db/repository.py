"""The only place SQL lives. `core/` never imports this module."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection

from app.db.models import sessions


@dataclass
class SessionRecord:
    id: uuid.UUID
    questions_asked: list[str]
    responses: dict[str, int]
    trait_scores: dict[str, float]
    probabilities: dict[str, float]
    completed: bool
    recommended_department: str | None


class SessionRepository:
    def __init__(self, conn: Connection):
        self._conn = conn

    def create(self, trait_scores: dict[str, float]) -> SessionRecord:
        session_id = uuid.uuid4()
        self._conn.execute(
            insert(sessions).values(
                id=session_id,
                questions_asked=[],
                responses={},
                trait_scores=trait_scores,
                probabilities={},
                completed=False,
                recommended_department=None,
            )
        )
        self._conn.commit()
        return SessionRecord(
            id=session_id,
            questions_asked=[],
            responses={},
            trait_scores=trait_scores,
            probabilities={},
            completed=False,
            recommended_department=None,
        )

    def get(self, session_id: uuid.UUID) -> SessionRecord | None:
        row = self._conn.execute(select(sessions).where(sessions.c.id == session_id)).mappings().first()
        if row is None:
            return None
        return SessionRecord(
            id=row["id"],
            questions_asked=row["questions_asked"],
            responses=row["responses"],
            trait_scores=row["trait_scores"],
            probabilities=row["probabilities"],
            completed=row["completed"],
            recommended_department=row["recommended_department"],
        )

    def update(self, session_id: uuid.UUID, **fields) -> None:
        self._conn.execute(update(sessions).where(sessions.c.id == session_id).values(**fields))
        self._conn.commit()
