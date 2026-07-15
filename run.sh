#!/usr/bin/env bash
#
# Virtual Office — one command to build, start and seed the whole stack.
#
#   ./run.sh          build + start + load the demo workspace
#   ./run.sh --fresh   same, but wipe all existing data first
#
# First run compiles 9 Spring services and 2 frontends inside Docker and takes ~15–25 min.
# Later runs are cached and take ~1 min. Nothing is installed on the host: no JDK, no Node,
# no Maven — only Docker is required.
set -euo pipefail
cd "$(dirname "$0")"

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
blue()  { printf '\033[0;34m%s\033[0m\n' "$1"; }
warn()  { printf '\033[0;33m%s\033[0m\n' "$1"; }
die()   { printf '\033[0;31m%s\033[0m\n' "$1" >&2; exit 1; }

# ── Preflight ────────────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || die "Docker is not installed. See https://docs.docker.com/get-docker/"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required (try: docker compose version)"
docker info >/dev/null 2>&1 || die "The Docker daemon is not running. Start Docker Desktop / dockerd and retry."

if [ ! -f .env ]; then
  cp .env.example .env
  warn "No .env — created one from .env.example."
  warn "Voice needs real Agora keys: set AGORA_APP_ID and AGORA_APP_CERTIFICATE, then re-run."
fi

if [ "${1:-}" = "--fresh" ]; then
  warn "Wiping all containers and data volumes…"
  docker compose --profile seed down -v --remove-orphans || true
fi

# ── Build + start ────────────────────────────────────────────────────────────
blue "==> Building and starting the stack (first run: ~15–25 min)…"
docker compose up --build -d

# ── Demo data ────────────────────────────────────────────────────────────────
# The seeder blocks on depends_on: service_healthy for everything it calls, so no sleep is
# needed here. It is idempotent — existing accounts fall back to login, and it will not
# duplicate the workspace. Set SEED_FORCE=1 in .env to rebuild tasks/messages anyway.
blue "==> Loading the demo workspace (waits for services to report healthy)…"
docker compose --profile seed up --build seed
# The 3-month chat history goes straight into MongoDB: the REST API cannot backdate a message.
docker compose --profile seed up --build seed-history

# ── Where to look ────────────────────────────────────────────────────────────
green ""
green "Ready."
green ""
green "  Web client ......... http://localhost:3001"
green "  2D office .......... http://localhost:5000"
green "  API gateway ........ http://localhost:8080"
green "  Grafana ............ http://localhost:3005   (admin / admin)"
green "  Prometheus ......... http://localhost:9091"
green "  RabbitMQ ........... http://localhost:15672"
green ""
green "  Log in with any account from seed/credentials.md, e.g."
green "    maya.hassan@northstar.io  /  ${SEED_PASSWORD:-Northstar@2026}   (owner)"
green ""
warn "  Voice needs the microphone, which browsers only grant on https:// or http://localhost."
warn "  Opening the app from another device via http://<lan-ip>:3001 will show chat but no mic."
green ""
echo "  Status:  docker compose ps"
echo "  Logs:    docker compose logs -f <service>"
echo "  Stop:    docker compose down          (keeps data)"
echo "  Reset:   ./run.sh --fresh             (wipes data, re-seeds)"
