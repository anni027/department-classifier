"""Per-client rate limiting.

The only control that bounds how many session rows an anonymous caller can
create, so it is the difference between a bored student's loop being a
nuisance and being an outage during recruitment week.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def client_ip(request: Request) -> str:
    """Identify the caller by the address the edge proxy observed, not by the
    socket.

    Behind a reverse proxy every request arrives from the proxy's own IP, so
    keying on `request.client.host` would put every student in one bucket and
    the first burst would lock out everyone. Both supported deployments
    terminate the connection somewhere else, so both headers have to be read:

    * **Self-hosted (Caddy).** Caddy sets `X-Real-IP` with `header_up` (no
      `+`), which REPLACES any client-supplied value, so it cannot be forged
      from outside and is preferred.
    * **Railway.** There is no Caddy. Railway's edge proxy owns
      `X-Forwarded-For` and the leftmost entry is the real client — that is
      Railway's documented answer, and the reason this is not simply
      "X-Real-IP or the socket". `X-Real-IP` is the wrong thing to prefer
      there: when Railway's Fastly CDN is in the request path it is set to the
      CDN's own edge address, which is shared by every caller, and keying on a
      shared address is exactly the outage this function exists to prevent.

    The trust this places in `X-Forwarded-For` is Railway's to keep; on
    Lightsail the equivalent guarantee comes from the Caddyfile line
    documented in backend/tests/test_rate_limit.py, where removing it silently
    makes the limit forgeable.
    """
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return get_remote_address(request)


# Generous on purpose. Campus wifi and mobile CGNAT put hundreds of students
# behind a single public IP, so a tight limit takes the launch down rather
# than an attacker. The reaper in app/db/cleanup.py bounds what gets through.
limiter = Limiter(key_func=client_ip, default_limits=["120/minute"])
