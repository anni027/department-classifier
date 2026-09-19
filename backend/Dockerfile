# Taqneeq Classifier API
#
# Runtime only — no build step, since the app is pure Python and the data
# files it serves live in the repo.
FROM python:3.11-slim

# PORT defaults to 8000 for the self-hosted (Lightsail) stack and for a plain
# `docker run`. Railway and most PaaS inject their own PORT and expect the app
# to bind to it — the CMD at the bottom honors whatever is set here.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=app/data \
    PORT=8000

WORKDIR /app

# Dependencies first: this layer is cached unless requirements.txt changes.
# psycopg[binary] ships wheels, so no compiler toolchain is needed here.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root. The app only ever reads from its own directory.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Uses the app's own health route, which reports whether departments and
# questions actually loaded — not just whether the port is open.
# Reads PORT rather than hard-coding 8000, so the check keeps matching the
# CMD below when a platform injects a different port.
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import os,sys,urllib.request; port=os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/health', timeout=4).status == 200 else 1)"

# `sh -c` so ${PORT} expands at runtime, `exec` so uvicorn replaces the shell
# and stays PID 1 — without it the SIGTERM a platform sends to stop the
# container goes to a shell that never forwards it, and shutdown hangs until
# the platform SIGKILLs it. Defaults to 8000, which is what Lightsail uses.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
