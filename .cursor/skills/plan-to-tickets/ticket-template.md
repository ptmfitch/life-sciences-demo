# Cloud-agent ticket template

Use this structure for every **child** issue description (`contentFormat: "markdown"`).

```markdown
## Context
<1–3 sentences: current behavior vs desired outcome. Include why if non-obvious.>

## Scope
**In**
- <concrete deliverable>
- <…>

**Out**
- <explicit non-goals / files to leave alone>

## Implementation
1. <step with file path and exact change>
2. <…>
3. <…>

## Files
| Path | Change |
|------|--------|
| `path/to/file` | <what to edit> |

## Acceptance criteria
- [ ] <observable result>
- [ ] <…>

## Verify
1. <command or UI steps>
2. <expected signal of success>

## Dependencies
- Blocked by: <PLSD-… or “none”>
- Blocks: <PLSD-… or “none”>

## Notes for cloud agent
- Repo: life-sciences-demo
- Do not expand scope beyond this ticket
- <restarts, env, seed data, ports, etc.>
```

## Parent template

```markdown
## Goal
<plan overview in 2–4 sentences>

## Approach
<chosen approach from the plan; no open options>

## Child work
1. <theme of child 1>
2. <theme of child 2>

## Overall acceptance
- [ ] <end-to-end success check>

## Plan source
`<path to .cursor/plans/…>` or “conversation plan”
```

## Example (from a 1 Hz sim plan)

**Summary:** `Set DEMO_SPEED to 1 in config and env files`

**Description:**

```markdown
## Context
Live BioTest runs tick at DEMO_SPEED=12 (~12 readings/sec), so Monitor UI updates too fast. Target is 1 reading per wall-clock second.

## Scope
**In**
- Default and env `DEMO_SPEED` → `1`

**Out**
- No changes to `server/app/runs/manager.py` or `web/src/lib/sse.ts` (they already follow tick interval / SSE)

## Implementation
1. In `server/app/config.py`, change `demo_speed: float = 12.0` to `1.0`.
2. In `.env.example` and `.env`, change `DEMO_SPEED=12` to `DEMO_SPEED=1`.

## Files
| Path | Change |
|------|--------|
| `server/app/config.py` | `demo_speed` default `12.0` → `1.0` |
| `.env.example` | `DEMO_SPEED=12` → `1` |
| `.env` | `DEMO_SPEED=12` → `1` |

## Acceptance criteria
- [ ] `tick_interval_seconds` resolves to `1.0` with default settings
- [ ] Example and local env document `DEMO_SPEED=1`

## Verify
1. Restart the API (settings load at process start).
2. Confirm config/env values are `1` (grep or health payload if it exposes `demo_speed`).

## Dependencies
- Blocked by: none
- Blocks: verification ticket (Monitor 1 Hz check)

## Notes for cloud agent
- Repo: life-sciences-demo
- Do not expand scope beyond this ticket
- API restart required before behavior changes are observable
```
