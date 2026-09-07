# Taqneeq Classifier API
#
# Runtime only — no build step, since the app is pure Python and the data
# files it serves live in the repo.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=app/data

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
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
