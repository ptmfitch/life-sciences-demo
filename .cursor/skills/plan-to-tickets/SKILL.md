---
name: plan-to-tickets
description: >-
  Convert Cursor plan-mode output into detailed Jira tickets in PLSD that a
  cloud agent can implement without extra context. Use when the user asks to
  break a plan into tickets, create Jira work from a plan, turn plan mode into
  backlog items, or prepare cloud-agent-ready issues for
  fe-anysphere-demo / PLSD.
---

# Plan to tickets

Turn an approved (or draft) Cursor plan into **cloud-agent-ready** Jira issues in **PLSD**.

## Defaults (do not ask unless overridden)

| Setting | Value |
|---------|--------|
| Site | `https://fe-anysphere-demo.atlassian.net` |
| Cloud ID | Resolve via `getAccessibleAtlassianResources` (site URL above) |
| Project | `PLSD` |
| Board | https://fe-anysphere-demo.atlassian.net/jira/software/projects/PLSD/boards/1041 |
| Status | **To Do** (new issues land here by default; do not leave in other statuses) |
| MCP | `user-Atlassian-MCP-Server` (`createJiraIssue`, etc.) |

If the user pastes a different project/board URL, use that instead.

## When to run

- User attaches or references a plan (`.cursor/plans/*.plan.md`, plan mode output, or “the plan we just made”)
- User asks to break work into tickets / backlog / Jira for a cloud agent

## Workflow

```
Progress:
- [ ] 1. Load plan source
- [ ] 2. Decompose into cloud-agent-sized tickets (internally)
- [ ] 3. Present breakdown; wait for confirmation (unless user said create now)
- [ ] 4. Create parent issue, then children in PLSD
- [ ] 5. Return table of keys + links (board + browse URLs)
```

### 1. Load plan source

Prefer, in order:

1. Plan file path the user cites or that is attached in context
2. Latest relevant file under `.cursor/plans/` matching the work
3. The plan text already in the conversation (overview, todos, file paths, approach)

Read the full plan. Also skim cited source files if the plan is thin—tickets must include enough concrete detail for a cloud agent that has **no chat history**.

### 2. Decompose for cloud agents

Each child ticket must be **independently implementable** in one cloud agent run.

**Sizing**

- Prefer **2–8** child tickets; split if a ticket would touch many unrelated areas
- One ticket ≈ one coherent change set (same layer or same feature slice)
- Separate **verify/QA** only when verification is non-trivial or blocked on deploy/restart
- Do **not** create filler tickets (“update README”) unless the plan requires them

**Hierarchy (PLSD team-managed)**

| Plan size | Parent | Children |
|-----------|--------|----------|
| Small (≤3 implementable units) | `Story` | `Subtask` with `parent=<Story key>` |
| Larger / multi-area | `Epic` | `Task` (or `Bug` / `Story` as appropriate) with `parent=<Epic key>` |

Issue-type hints:

- **Bug** — incorrect behavior / regression
- **Story** — user-facing capability (parent or rare standalone)
- **Task** — technical implementation under an Epic
- **Subtask** — implementation slice under a Story

**Every child description must be self-contained.** Assume the cloud agent only sees that issue.

Required sections in each child ticket — follow [ticket-template.md](ticket-template.md):

- Context (why / current vs desired)
- Scope (in / out)
- Implementation steps (ordered, concrete)
- Files to change (paths + what to do)
- Acceptance criteria (checkbox-style)
- Verify (commands or UI steps)
- Dependencies (blocked by / blocks other keys after create, or plan-local labels like “after Ticket 1”)

Parent description: goal, approach summary, list of child themes, overall acceptance, link/path to the plan file if known.

### 3. Present breakdown (confirm)

Unless the user already said to create without review, show:

```markdown
Proposed PLSD backlog (To Do):

**Parent:** [Story|Epic] <summary>
**Children:**
1. [Subtask|Task|Bug] <summary> — <one-line scope>
2. ...

Create these in PLSD?
```

Revise if they ask; then create.

### 4. Create in Jira

1. `getAccessibleAtlassianResources` → cloud ID for fe-anysphere-demo
2. Optionally `getVisibleJiraProjects` / issue types for `PLSD` if unsure of type names
3. `createJiraIssue` for the **parent first**; capture `key`
4. `createJiraIssue` for each child with `parent` set; `contentFormat: "markdown"`
5. Confirm each issue `status.name` is **To Do**. If not, `getTransitionsForJiraIssue` + `transitionJiraIssue` into To Do

Do not assign people unless asked. Do not transition to In Progress.

### 5. Summary output

Return a compact table:

| Key | Type | Summary | URL |
|-----|------|---------|-----|
| PLSD-n | … | … | browse link |

Include the [board link](https://fe-anysphere-demo.atlassian.net/jira/software/projects/PLSD/boards/1041). Mention that tickets are written for cloud-agent pickup.

## Writing rules for ticket bodies

- Use **exact repo paths** from the plan (`server/app/config.py`, not “the config”)
- Include **before → after** when changing defaults or literals (e.g. `DEMO_SPEED=12` → `1`)
- Call out **restarts**, migrations, or env reloads when needed
- State **what not to change** when the plan explicitly leaves files alone
- Prefer steps a cloud agent can execute; avoid “consider” / “maybe”
- Keep summaries action-oriented: `Set DEMO_SPEED to 1 in config and env`

## Anti-patterns

- Vague tickets (“improve performance”) with no files or acceptance checks
- One mega-ticket that restates the whole plan
- Creating issues outside PLSD without user override
- Skipping confirmation when the user did not ask to create immediately
- Relying on chat context the cloud agent will not have
