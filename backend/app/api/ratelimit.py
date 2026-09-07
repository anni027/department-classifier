"""Per-client rate limiting.

The only control that bounds how many session rows an anonymous caller can
create, so it is the difference between a bored student's loop being a
nuisance and being an outage during recruitment week.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def client_ip(request: Request) -> str:
    """Identify the caller by the address Caddy observed, not by the socket.

    Behind the reverse proxy every request arrives from Caddy's container IP,
    so keying on `request.client.host` would put every student in one bucket
    and the first burst would lock out everyone.

    Caddy sets `X-Real-IP` with `header_up` (no `+`), which REPLACES any
    client-supplied value, so this header cannot be forged from outside. That
    is deliberately different from trusting `X-Forwarded-For` via uvicorn's
    `FORWARDED_ALLOW_IPS=*`, where the leftmost value is attacker-controlled
    and lets a caller rotate its own rate-limit key at will.
    """
    return request.headers.get("x-real-ip") or get_remote_address(request)


# Generous on purpose. Campus wifi and mobile CGNAT put hundreds of students
# behind a single public IP, so a tight limit takes the launch down rather
# than an attacker. The reaper in app/db/cleanup.py bounds what gets through.
limiter = Limiter(key_func=client_ip, default_limits=["120/minute"])
