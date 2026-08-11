---
name: quick-start
description: >-
  Start the AstraLume BioTest demo (API + Vite) if needed and open it in the
  Cursor browser tab. Use when the user asks for quick start, to run/start the
  demo or app, or to open the local BioTest UI.
---

# Quick start

Bring up the local AstraLume BioTest demo and open it in Cursor’s browser.

App URL: `http://localhost:5173` (Vite; proxies `/api` → `:8000`).

## Workflow

```
Progress:
- [ ] 1. Run ensure-running.sh
- [ ] 2. Confirm STATUS=already_running or STATUS=started and URL=
- [ ] 3. Open URL in Cursor browser via open_resource
- [ ] 4. Tell the user the app is open (and whether it was already running)
```

## Step 1: Ensure the app is running

From the **repo root**, execute:

```bash
bash .cursor/skills/quick-start/scripts/ensure-running.sh
```

The script:

1. Checks whether API (`:8000/api/health`) and web (`:5173`) already respond
2. If both are up → prints `STATUS=already_running` and `URL=...` (does not restart)
3. If not → follows README quick start (`.env`, `make db`, `make install` if needed, background `make server` / `make web`), waits until healthy, then prints `STATUS=started` and `URL=...`

Logs (when started): `$TMPDIR/astralume-biotest/{server,web}.log`

Do **not** start `make server` / `make web` yourself unless the script fails; use the script.

## Step 2: Open in Cursor browser

Parse `URL=` from the script stdout (default `http://localhost:5173`).

Call the **cursor-app-control** MCP tool `open_resource` with:

```json
{ "uri": "http://localhost:5173" }
```

(Use the exact URL from the script output.)

That opens the app in the Cursor browser tab. Do not rely on opening an external system browser unless `open_resource` fails.

## Step 3: Report

One short line: already running vs freshly started, and the URL.

## Failure

If the script exits non-zero:

1. Tail `$TMPDIR/astralume-biotest/server.log` and `web.log`
2. Check Postgres (`make db` / Homebrew `postgresql@16` on `:5432`)
3. Fix and re-run the script — do not open the browser until both services are healthy
