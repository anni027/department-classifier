from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.engine import Connection

from app.core.models import Department, Question
from app.db.database import engine
from app.db.repository import SessionRepository


def get_departments(request: Request) -> list[Department]:
    return request.app.state.departments


def get_questions(request: Request) -> list[Question]:
    return request.app.state.questions


def get_traits(request: Request) -> list[str]:
    return request.app.state.traits


def get_db_connection() -> Generator[Connection, None, None]:
    with engine.connect() as conn:
        yield conn


def get_repository(conn: Connection = Depends(get_db_connection)) -> SessionRepository:
    return SessionRepository(conn)
