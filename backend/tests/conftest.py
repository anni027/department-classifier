from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_departments, get_questions, get_repository, get_traits
from app.core.data_loader import load_departments, load_questions, load_traits
from app.main import app
from tests.fake_repository import FakeSessionRepository


@asynccontextmanager
async def _noop_lifespan(_app):
    yield

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"


@pytest.fixture(scope="session")
def departments():
    return load_departments(DATA_DIR / "departments.json")


@pytest.fixture(scope="session")
def questions():
    return load_questions(DATA_DIR / "questions.json")


@pytest.fixture(scope="session")
def traits():
    return load_traits(DATA_DIR / "questions.json")


@pytest.fixture
def initial_trait_scores(traits):
    return {trait: 0.5 for trait in traits}


@pytest.fixture
def client(departments, questions, traits):
    """TestClient wired to the real routes but a fake in-memory repository -
    no Postgres needed for API-layer tests. Startup (which touches the real
    DB) is skipped entirely; departments/questions/traits are injected via
    dependency overrides instead of app.state.
    """
    app.dependency_overrides[get_departments] = lambda: departments
    app.dependency_overrides[get_questions] = lambda: questions
    app.dependency_overrides[get_traits] = lambda: traits
    fake_repo = FakeSessionRepository()
    app.dependency_overrides[get_repository] = lambda: fake_repo

    # Rate limiting is middleware, so dependency overrides do not bypass it.
    # Tests fire many requests from one "client" and would otherwise 429.
    app.state.limiter.enabled = False

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan  # skip real-DB startup for API tests
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.router.lifespan_context = original_lifespan
        app.dependency_overrides.clear()
