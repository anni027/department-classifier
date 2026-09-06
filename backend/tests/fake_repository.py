"""Test-only in-memory stand-in for SessionRepository.

Implements the same create/get/update surface so route handlers don't know
the difference. Never shipped in app/ - the real repository is Postgres-
backed (app/db/repository.py); this exists purely to make API-layer tests
fast and DB-free.
"""
import uuid

from app.db.repository import SessionRecord


class FakeSessionRepository:
    def __init__(self):
        self._records: dict[uuid.UUID, SessionRecord] = {}

    def create(self, trait_scores: dict[str, float]) -> SessionRecord:
        session_id = uuid.uuid4()
        record = SessionRecord(
            id=session_id,
            questions_asked=[],
            responses={},
            trait_scores=trait_scores,
            probabilities={},
            completed=False,
            recommended_department=None,
        )
        self._records[session_id] = record
        return record

    def get(self, session_id: uuid.UUID) -> SessionRecord | None:
        return self._records.get(session_id)

    def update(self, session_id: uuid.UUID, **fields) -> None:
        record = self._records[session_id]
        for key, value in fields.items():
            setattr(record, key, value)
