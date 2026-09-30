DEMO / SYNTHETIC · for enablement only

# Run-sheet — 10-minute regulated SDLC demo

Illustrative only. Synthetic lab console. The tooling produces evidence for your validated process. Nothing in this talk is a validation claim.

Audience: regulated pharma engineering. Length: about 10 minutes. Story: a bug is reported in Slack, a Cursor cloud agent opens a draft pull request, Bugbot applies the repo rules, an automation posts a Compliance Evidence Pack, and a separate reviewer answers a revalidation question and stops for a person.

This sheet says **the reported bug**. The symptom text, the repro clicks, and the cause live in the description of the pull request that added this kit. Do not read a root cause or a file path out loud.

What the repository hooks allow and deny is in [HOOKS.md](HOOKS.md).

## Pre-flight

Do this before the room, not during the ten minutes.

- [ ] Merge the demo-kit pull request yourself (or set the cloud agent's base branch to that branch). This sheet does not merge it. The live fix must branch from the kit so `server/app/validated/`, `.cursor/BUGBOT.md`, and `docs/` are on the base.
- [ ] Bugbot is enabled for the repository, will read `.cursor/BUGBOT.md`, and has **Enable reviews on draft PRs** switched on. Bugbot skips draft pull requests until that switch is on.
- [ ] Making the Bugbot check required in branch protection is what turns flags into a merge block.
- [ ] A Cursor Automation exists for **Draft opened**, **Pull request pushed**, and **Pull request opened**. Drafts need **Draft opened**; **Pull request opened** covers only a non-draft pull request or a draft marked ready. Instructions are the paste block in [evidence-pack-automation.md](evidence-pack-automation.md). It has permission to comment on pull requests.
- [ ] A Slack channel is connected to a Cursor cloud agent. You can hand it a bug report from that channel.
- [ ] MCPs the agents should call (GitHub, Slack, anything else) are connected at **team** level in the Cursor dashboard. Cloud agents do not use MCP servers configured only on your laptop.
- [ ] The GitHub connection can open a **draft** pull request. Every cloud-agent commit is signed. On a scratch run, eyeball the **Verified** badge on the commit.
- [ ] Local console, only if you will show the symptom: `cp .env.example .env`, `make install`, `make server`, `make web`, then open http://localhost:5173. Postgres per the README.
- [ ] Copy the paste-ready Slack bug report from the demo-kit pull request description. Do not add a change-request id. Do not add a suspected cause. `CR-00042` is an example record and must not be pasted into that message.
- [ ] Have these tabs ready: Slack, the Cursor agent run, the GitHub draft pull request, Bugbot, this repo at `docs/demo/sample-evidence-pack.md`, `docs/sop-demo-017-change-control.md`, and `docs/demo/compliance-reviewer-skill.md`.

| In the repository already | You configure in Cursor, Slack, and GitHub |
| --- | --- |
| Acceptance calculation, audit trail, tests, Bugbot rules, SOP-DEMO-017, validation plan, example CR-00042, this run-sheet, the evidence-pack instructions, the sample comment, the reviewer instructions, the hook scripts | Bugbot on the repo with reviews on draft PRs, the Bugbot check required in branch protection when flags should block a merge, the automation (Draft opened, Pull request pushed, and Pull request opened), the Slack-to-cloud-agent connection, team-level MCPs, draft-PR permissions, merging this kit onto the branch the agent starts from |

## Beat 1 — Slack report (0:00–2:00)

**Say:** "A scientist sees a wrong disposition on the acceptance panel and reports it the way they would in Slack. The message is the symptom only. I am not going to guess the cause."

**Click:**

1. If the local app is up, open **Dashboards** and leave the specimen acceptance panel on screen while you read.
2. Paste the Slack bug report from the demo-kit pull request description into the connected channel, aimed at the cloud agent.

**Fallback:** Read that same Slack text aloud from the pull request description. Skip the live channel. The rest of the beats still work if you start the agent from the Cursor UI with that text.

## Beat 2 — Cloud agent draft pull request (2:00–4:30)

**Say:** "The agent should fix the reported bug and open a draft pull request. Every cloud-agent commit is signed."

**Click:**

1. Open the agent run. Wait until it pushes a branch and opens a pull request.
2. Show the pull request is a **draft**.
3. Open the commit and show GitHub's **Verified** badge.
4. Show the diff is small. Do not narrate the fix.

**Fallback:** If the agent is still running at 4:30, leave it on screen and switch to the pre-baked path: "Live generation is still going. I will use the example comment and the SOP so we keep the clock, and we can flip back if the draft appears." Do not invent a diff.

## Beat 3 — Bugbot (4:30–6:30)

**Say:** "Bugbot is using the rules in `.cursor/BUGBOT.md`. For a change under the validated package I expect a flagged finding when the description has no new change-request id, and another when the diff has no test change. An audit-trail edit would ask for a QA impact assessment. The review should also end with a regulatory-impact tier: none, minor, or revalidation likely. Those flags become a merge block only when the Bugbot check is required in branch protection."

**Click:**

1. Open the Bugbot review on the draft pull request.
2. Read the finding titles that actually posted. **Missing change control reference** should appear when the description has no new `CR-#####` (`CR-00042` does not count). **Missing test evidence** appears when `server/tests/` was not in the diff.
3. Point at the regulatory-impact lines if Bugbot wrote them.

**Fallback:** Open `.cursor/BUGBOT.md` and walk those three outcomes against the draft diff yourself. Say Bugbot has not posted yet. Do not mark anything resolved.

## Beat 4 — Evidence pack (6:30–8:00)

**Say:** "A separate automation comments a Compliance Evidence Pack: summary, requirement ids, a risk tier, tests, Bugbot status, and questions for QA. The tier is a proposal. QA has not accepted it. The pack updates in place on later pushes."

**Click:**

1. Refresh the pull request conversation.
2. Open the automation's comment and read the tier and the open questions.

**Fallback:** Open [sample-evidence-pack.md](sample-evidence-pack.md) and read it as the comment you would have posted. Say it is the pre-baked example for the reported bug, not a live review.

## Beat 5 — Reviewer stops for a person (8:00–9:30)

**Say:** "A different agent, not the one that wrote the code, answers a single question: does this change require revalidation per SOP-DEMO-017? It has to cite the SOP. Then it drafts a change record and stops. It does not approve and it does not sign."

**Click:**

1. Start a cloud agent (or a local agent) with [compliance-reviewer-skill.md](compliance-reviewer-skill.md) and the draft pull request URL.
2. When it answers, show the sentence and the section it cited (`§5.2` or `§5.3`).
3. Show the blank change-request id and the line "Stopping for human approval. I will not approve, sign, or merge."
4. Stop. Do not click approve. Do not merge.

**Fallback:** Open `docs/sop-demo-017-change-control.md` at §5.2 and §5.3 and §8. Read the classification rule and the human-handoff rule yourself. Then read the stop sentence from the reviewer instructions. Leave the pull request unapproved.

## Close (9:30–10:00)

**Say:** "What you saw is evidence for a process you already validate: a report, a draft change, review rules that flag findings, a pack a QA reader can scan, and a stop for a person. The console is synthetic. I am not merging."

Leave the fix pull request as a draft.

## If a beat slips

Cut narration, not the stop. Beat 5's handoff is the point of the talk. Beats 2 and 4 have file fallbacks so a slow agent does not eat the close.
