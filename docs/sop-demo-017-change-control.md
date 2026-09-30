DEMO / SYNTHETIC · for enablement only

# SOP-DEMO-017 — Change control for the synthetic acceptance calculation

Illustrative only. This procedure is a teaching script for a regulated engineering demo. It produces evidence for your validated process. It does not make the AstraLume BioTest console, this repository, or any calculation validated.

Synthetic data only — not medical, clinical, diagnostic, or regulatory evidence.

## 1. Purpose

Describe how a change that touches the specimen acceptance calculation is classified, recorded, and held for a person to accept.

## 2. Scope

In scope:

- `server/app/validated/` — activity and temperature disposition, reported rounding, and the reference-standard catalog
- Tests under `server/tests/` that exercise that package
- `server/app/audit_trail/` — the append-only who / what / when / why record

Out of scope: live run start/stop controls, CSV file names, chart styling, and anything outside this repository. Production quality systems are not this file.

## 3. Definitions

| Term | Meaning in this demo |
| --- | --- |
| Change request | A record id of the form `CR-` plus five digits (`CR-\d{5}`) that points at one change |
| Reported value | A number after half-up rounding to one decimal place, which is what the acceptance panel shows |
| Revalidation | A new confirmation that the calculation still meets the requirements in the validation plan, performed by people in your process |
| Minor change | A change that stays inside an already written requirement and is documented with test evidence |
| Evidence | The pull request, the requirement ids it touches, the tests, and the audit record. The tooling produces evidence for your validated process |

## 4. Change-request identifier

4.1 Every change under §2 that edits `server/app/validated/` names a change-request id in the pull request description.

4.2 `CR-00042` is the example record for the baseline that introduced the panel. A later change uses a new id. Citing `CR-00042` again does not identify the later change.

4.3 The person who writes the description does not approve their own change by adding the id. The id is a reference. Acceptance is §8.

## 5. Classification

Pick one tier and record the reason.

### 5.1 None

Use **none** when the diff cannot change a numeric result, a limit, a unit, or an audit record. Examples: a comment, a doc typo, a chart label that does not call the calculation.

### 5.2 Documented minor change

Use **minor** when all of the following are true:

- The written limits, units, formula, and rounding rule in the validation plan stay as they are.
- The executable change makes the running code match a requirement that plan already states, or it is a refactor that does not change results.
- The pull request includes test evidence for the behavior it touches.
- A human QA role accepts the classification. The disposition shown for a specimen may move from the previous executable result to the result the requirement already stated. That movement alone does not indicate revalidation.

A minor change is still documented. It is not an invisible edit.

### 5.3 Revalidation likely

Use **revalidation likely** when any of the following are true:

- The change edits a limit, unit, formula, or rounding rule as written in the validation plan.
- The effect on existing results cannot be explained as restoring an already written requirement.
- The author cannot point at a URS id for the new behavior.

Revalidation likely means your process would schedule a new confirmation. This SOP does not perform that confirmation.

## 6. Evidence to attach

For a change under `server/app/validated/`:

- The change-request id in the pull request description (§4)
- The URS ids from the validation plan that the diff touches
- A test diff under `server/tests/` when validated Python code changes
- The regulatory-impact tier from §5, with the reason

Bugbot rules in `.cursor/BUGBOT.md` check the id and the test diff. A bot finding is a prompt for a person. It is not the quality decision.

## 7. Audit-trail changes

Any modification under `server/app/audit_trail/` needs a QA impact assessment before merge. The assessment asks whether the record still shows who, what, when, and why, and whether older rows stay unchanged.

The application inserts rows and does not provide an update or delete path. A database rule ignores `UPDATE` and `DELETE` on `audit_events`. Changing that behavior is in scope for the assessment.

## 8. Human approval

8.1 A bot may draft a classification, a comment, or a change-record. A bot does not approve, sign, or merge.

8.2 The draft stops with an explicit handoff: a named human role (QA or the change owner) accepts or sends it back.

8.3 Signing the change record, releasing the calculation, and any revalidation activity happen outside this repository, in your process.

## 9. What this SOP does not claim

This file is a synthetic procedure for enablement. Following it during a demo does not validate the software. The console remains illustrative only.
