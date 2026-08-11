# AstraLume BioTest — Synthetic Telemetry Demo

Local-first demo of a life-sciences testing workflow:

1. **Monitor** — start/control synthetic AstraLume BioTest Station runs from the web UI  
2. **Live tiles** — well-panel visuals, metrics, sparklines via Server-Sent Events  
3. **CSV output** — one-minute files under `data/telemetry/`  
4. **ETL** — scan → inspect → map → dry run → load into local Postgres  
5. **Dashboards** — historical charts from loaded telemetry  

> **Illustrative only.** Synthetic data — not medical, clinical, diagnostic, or scientifically validated. See [docs/SYNTHETIC_MODEL.md](docs/SYNTHETIC_MODEL.md).

## Prerequisites

- Python 3.12+ and [uv](https://github.com/astral-sh/uv)
- Node 20+ and npm
- Postgres 16 (Docker Compose **or** Homebrew `postgresql@16`)

## Quick start

```bash
cp .env.example .env

# Option A — Docker Compose
docker compose up -d db

# Option B — Homebrew Postgres (already used if Docker/Colima is unavailable)
# brew services start postgresql@16
# create role/db biotest / biotest as in .env

make install
make server   # http://127.0.0.1:8000
make web      # http://127.0.0.1:5173
```

Open **http://localhost:5173**.

## Demo flow

1. On **Monitor**, add a named test (e.g. `Compound A - Rack 01`), then add multiple runs.
2. Start tests — watch tiles update (well colours, metrics, sparklines).
3. Pause / resume / stop individual runs; try bulk controls.
4. Confirm CSVs appear in `data/telemetry/`.
5. Open **ETL**, rescan, inspect a file, review mapping, dry run, then load.
6. Open **Dashboards** and refresh charts.
7. Rescan and load again — already-ingested files are skipped.

## Simulation speed

`DEMO_SPEED` controls wall-clock pace (`tick_interval_seconds = 1 / DEMO_SPEED`). The default is **`DEMO_SPEED=1`** (one simulated reading per wall-clock second), so Monitor tiles / SSE update about once per second. Raise it (e.g. `12`) only when you want a faster demo; a full `MAX_RUNTIME_MINUTES=30` run then finishes sooner.

## Editing live during the demo

The API runs with `--reload`. Active runs **auto-resume** from Postgres checkpoints after a restart (deterministic simulator). The UI SSE connection reconnects and receives a full snapshot. Vite HMR hot-swaps frontend edits.

If a syntax error stops the reload, fix it and save — durable state lives in Postgres and CSVs.

## Optional debug CLI

```bash
cd server
uv run python -m app.sim.cli --test-name "Debug Run" --minutes 1
```

Not part of the primary demo path.

## Tests

```bash
cd server && uv run pytest -q
```

## Architecture (short)

- **FastAPI** process runs each assay as an **asyncio task** (no subprocesses)
- **SSE** streams `snapshot`, `run_state`, `telemetry`, `etl_progress`
- **Postgres** holds run metadata, source-file registry, raw + typed telemetry
- **React + Vite + Tailwind + Recharts** for Monitor / ETL / Dashboards

## Non-goals

No Snowflake, Databricks, Kafka, Kubernetes, cloud auth, or multi-tenancy in v1.