"""Rate limiting on session creation.

The default `client` fixture disables the limiter (see conftest), so these
tests build their own client with it switched on.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_departments, get_questions, get_repository, get_traits
from app.main import app
from tests.conftest import noop_lifespan
from tests.fake_repository import FakeSessionRepository


@pytest.fixture
def limited_client(departments, questions, traits):
    app.dependency_overrides[get_departments] = lambda: departments
    app.dependency_overrides[get_questions] = lambda: questions
    app.dependency_overrides[get_traits] = lambda: traits
    app.dependency_overrides[get_repository] = lambda: FakeSessionRepository()

    app.state.limiter.enabled = True
    app.state.limiter.reset()

    # Same lifespan skip the shared `client` fixture uses — without it these
    # tests reach for a real Postgres and pass only by accident.
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = noop_lifespan
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.router.lifespan_context = original_lifespan
        app.state.limiter.reset()
        app.state.limiter.enabled = False
        app.dependency_overrides.clear()


def _start(client, ip):
    return client.post("/api/v1/classification/start", headers={"X-Real-IP": ip})


def test_start_is_rate_limited(limited_client):
    """Session creation is the only endpoint that writes new rows, so it is
    the one an attacker would loop on. 30/minute is the cap.
    """
    codes = [_start(limited_client, "203.0.113.10").status_code for _ in range(40)]

    assert codes.count(201) == 30, f"expected 30 successes, got {codes.count(201)}"
    assert 429 in codes, "limit never tripped"
    # Once tripped it stays tripped for the window, rather than flapping.
    assert codes[-1] == 429


def test_limit_is_per_client_not_global(limited_client):
    """The failure mode this guards against: keying on the socket address
    puts every student behind the reverse proxy into one bucket, so the first
    burst locks out the whole campus.
    """
    for _ in range(30):
        _start(limited_client, "203.0.113.10")
    assert _start(limited_client, "203.0.113.10").status_code == 429

    # A different client is unaffected.
    assert _start(limited_client, "198.51.100.77").status_code == 201


def test_forged_header_cannot_mint_a_fresh_bucket(limited_client):
    """X-Real-IP is only trustworthy because Caddy overwrites it with
    `header_up X-Real-IP {remote_host}` (no `+`, so it replaces). This test
    documents that the app trusts the header — if that Caddyfile line is ever
    removed, an attacker rotates the header to bypass the limit entirely.
    """
    for _ in range(30):
        _start(limited_client, "203.0.113.10")

    assert _start(limited_client, "203.0.113.99").status_code == 201


def test_forwarded_for_keys_the_limit_when_real_ip_is_absent(limited_client):
    """Railway sets no Caddy, so X-Real-IP is absent (or, with its CDN in the
    path, the CDN edge address — see app/api/ratelimit.py). Falling back to
    the leftmost X-Forwarded-For entry is what keeps the limit per-student
    there. Without the fallback every caller keys on the proxy's IP and the
    global default of 120/minute covers the whole campus at once.
    """

    def start(forwarded_for):
        return limited_client.post(
            "/api/v1/classification/start",
            headers={"X-Forwarded-For": forwarded_for},
        )

    for _ in range(30):
        assert start("203.0.113.10").status_code == 201
    assert start("203.0.113.10").status_code == 429

    # A different caller is unaffected.
    assert start("198.51.100.77").status_code == 201

    # A chained header keys on the client, not on the proxy hop that appended
    # it, so the two entries do not share a bucket.
    assert start("198.51.100.78, 70.41.3.18, 150.172.238.178").status_code == 201
