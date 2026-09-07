import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.ratelimit import limiter
from app.api.routes import classification, departments, health
from app.config import require_production_config, settings
from app.core.data_loader import load_departments, load_questions, load_traits, validate_data
from app.db.cleanup import purge_loop
from app.db.database import engine
from app.db.models import metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    require_production_config()

    data_dir = Path(settings.data_dir)
    departments_data = load_departments(data_dir / "departments.json")
    questions_data = load_questions(data_dir / "questions.json")
    traits = load_traits(data_dir / "questions.json")

    validate_data(departments_data, questions_data, traits)  # fail fast on malformed data

    app.state.departments = departments_data
    app.state.questions = questions_data
    app.state.traits = traits

    metadata.create_all(engine)  # no-op if the `sessions` table already exists

    reaper = asyncio.create_task(purge_loop())

    try:
        yield
    finally:
        reaper.cancel()


# Docs are not reachable through Caddy in production (it proxies only /api/*),
# but disabling them here means that stays true if a catch-all route is ever
# added to the backend.
app = FastAPI(
    title="Taqneeq Department Classifier API",
    version="1.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(classification.router, prefix="/api/v1")
