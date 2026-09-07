#!/usr/bin/env bash
#
# Deploy the Taqneeq Classifier on a single host (see DEPLOY.md).
# Run from the repo root on the server:  ./deploy.sh
#
#   --no-pull    deploy the working tree as-is, without git pull
#   --no-build   restart existing images without rebuilding
#   --logs       follow logs after a successful deploy
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
PULL=1
BUILD=1
FOLLOW_LOGS=0

for arg in "$@"; do
  case "$arg" in
    --no-pull)  PULL=0 ;;
    --no-build) BUILD=0 ;;
    --logs)     FOLLOW_LOGS=1 ;;
    -h|--help)  sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

say()  { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# --- preflight -------------------------------------------------------------
[ -f "$COMPOSE_FILE" ] || fail "run this from the repo root ($COMPOSE_FILE not found)"
command -v docker >/dev/null || fail "docker is not installed — see DEPLOY.md step 2"
docker compose version >/dev/null 2>&1 || fail "the docker compose plugin is missing"

if [ ! -f "$ENV_FILE" ]; then
  fail "$ENV_FILE not found. Copy .env.production.example to $ENV_FILE and fill it in."
fi

# shellcheck disable=SC1090
set -a; . "./$ENV_FILE"; set +a

[ -n "${DOMAIN:-}" ]            || fail "DOMAIN is not set in $ENV_FILE"
[ -n "${POSTGRES_PASSWORD:-}" ] || fail "POSTGRES_PASSWORD is not set in $ENV_FILE"

compose() { docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"; }

say "Deploying $DOMAIN"

# --- source ----------------------------------------------------------------
if [ "$PULL" -eq 1 ]; then
  say "Pulling latest code"
  git pull --ff-only
else
  say "Skipping git pull (--no-pull)"
fi

# --- build -----------------------------------------------------------------
# The frontend bundle hard-codes the API URL at build time, so a DOMAIN change
# only takes effect after a rebuild. That is why --no-build is opt-in.
if [ "$BUILD" -eq 1 ]; then
  say "Building images (API URL baked in: https://$DOMAIN/api/v1)"
  compose build
else
  say "Skipping build (--no-build)"
fi

# --- run -------------------------------------------------------------------
say "Starting stack"
compose up -d --remove-orphans

# --- verify ----------------------------------------------------------------
# Check the backend through its own container rather than through Caddy, so a
# DNS or certificate problem is not misreported as the app being broken.
say "Waiting for the API to report healthy"
for i in $(seq 1 60); do
  if compose exec -T backend python -c \
      "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).status==200 else 1)" \
      >/dev/null 2>&1; then
    printf '\n'
    HEALTH=$(compose exec -T backend python -c \
      "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).read().decode())" 2>/dev/null || true)
    say "API healthy: $HEALTH"
    break
  fi
  printf '.'
  sleep 2
  if [ "$i" -eq 60 ]; then
    printf '\n'
    compose logs --tail 40 backend
    fail "API did not become healthy in 120s (logs above)"
  fi
done

say "Container status"
compose ps

# --- tidy ------------------------------------------------------------------
say "Removing dangling images"
docker image prune -f >/dev/null

say "Done — https://$DOMAIN"
echo "TLS certificates can take up to a minute on the very first deploy."
echo "Logs: docker compose --env-file $ENV_FILE -f $COMPOSE_FILE logs -f"

if [ "$FOLLOW_LOGS" -eq 1 ]; then
  compose logs -f
fi
