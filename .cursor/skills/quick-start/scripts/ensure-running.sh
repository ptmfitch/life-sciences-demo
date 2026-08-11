#!/usr/bin/env bash
# Ensure AstraLume BioTest demo is running (API :8000 + Vite :5173).
# Prints STATUS=... and URL=... for the agent; exit 0 on success.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

# Vite often binds IPv6-only localhost; prefer hostname over 127.0.0.1.
WEB_URL="http://localhost:5173"
API_HEALTH="http://127.0.0.1:8000/api/health"
LOG_DIR="${TMPDIR:-/tmp}/astralume-biotest"
mkdir -p "$LOG_DIR"

api_up() {
  curl -sf --max-time 2 "$API_HEALTH" >/dev/null 2>&1
}

web_up() {
  curl -sf --max-time 2 -o /dev/null "http://localhost:5173/" >/dev/null 2>&1 \
    || curl -sf --max-time 2 -o /dev/null "http://127.0.0.1:5173/" >/dev/null 2>&1
}

both_up() {
  api_up && web_up
}

wait_for() {
  local name="$1"
  local fn="$2"
  local tries="${3:-60}"
  local i=0
  while (( i < tries )); do
    if "$fn"; then
      echo "ready: $name" >&2
      return 0
    fi
    sleep 1
    ((i++)) || true
  done
  echo "error: timed out waiting for $name" >&2
  return 1
}

emit_ready() {
  local status="$1"
  echo "STATUS=$status"
  echo "URL=$WEB_URL"
}

if both_up; then
  echo "already running (API + web)" >&2
  emit_ready "already_running"
  exit 0
fi

# --- bootstrap from README quick start ---
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "created .env from .env.example" >&2
fi

echo "ensuring Postgres..." >&2
make db >/dev/null 2>&1 || true

need_install=0
if [[ ! -d web/node_modules ]]; then
  need_install=1
fi
if [[ -f server/pyproject.toml ]] && ! (cd server && uv run python -c "import fastapi" >/dev/null 2>&1); then
  need_install=1
fi

if (( need_install )); then
  echo "running make install..." >&2
  make install
fi

mkdir -p data/telemetry

if ! api_up; then
  echo "starting API (make server)..." >&2
  nohup make server >"$LOG_DIR/server.log" 2>&1 &
  echo $! >"$LOG_DIR/server.pid"
fi

if ! web_up; then
  echo "starting web (make web)..." >&2
  nohup make web >"$LOG_DIR/web.log" 2>&1 &
  echo $! >"$LOG_DIR/web.pid"
fi

wait_for "API :8000" api_up 90
wait_for "web :5173" web_up 90

emit_ready "started"
exit 0
