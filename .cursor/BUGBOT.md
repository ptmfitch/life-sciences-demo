# Bugbot review rules

DEMO / SYNTHETIC · for enablement only.

These rules are a demo of change-control review for a regulated-style discussion. They produce evidence for your validated process. They do not make this repository validated.

Apply them on every pull request. When a rule says to flag a finding, file that finding with the title below. Bugbot flags the pull request. Making the Bugbot check required in branch protection is what turns those flags into a merge block. Do not approve, sign, or dismiss the finding yourself.

Illustrative only. Synthetic lab data — not medical, clinical, or diagnostic evidence.

## Paths

- Validated calculation: `server/app/validated/**`
- Audit trail: `server/app/audit_trail/**`
- Tests that count as evidence for the validated package: `server/tests/**`
- Change-control SOP: `docs/sop-demo-017-change-control.md`
- Requirements: `docs/validation-plan.md`
- Example change request already used in this repo: `CR-00042` (see `docs/change-requests/CR-00042.md`)

## Missing change control reference

If the pull request changes any file under `server/app/validated/`, read the pull request description.

Flag a finding titled **Missing change control reference** when the description does not contain a change-request id for this change. An id matches `CR-` plus exactly five digits (`CR-\d{5}`).

`CR-00042` is the example historical record. If the only id in the description is `CR-00042`, still raise **Missing change control reference**. Reusing the example does not identify this change.

## Missing test evidence

If the pull request changes any `*.py` file under `server/app/validated/` and does not also change a file under `server/tests/`, flag a finding titled **Missing test evidence**.

A test change counts only when it is in the same pull request diff. Point at the validated files that lack a corresponding test diff. Do not accept "tests already exist on the base branch" as coverage for a new code change.

## Audit-trail change requires QA impact assessment

If the pull request modifies any file under `server/app/audit_trail/` (including migrations that only exist to support that package, when those migrations are in the same diff), flag a finding titled **Audit-trail change requires QA impact assessment**.

Raise it even when the edit looks internal, cosmetic, or limited to comments. State that a human QA role has to assess impact on the append-only record (who, what, when, why) before merge. Do not mark the finding resolved inside the review.

## Patient or subject identifiers

If a changed line adds a string literal that looks like a patient, subject, or medical-record identifier, flag a finding titled **Possible patient or subject identifier**.

Flag literals such as `PAT-12345`, `MRN-001234`, `SUBJ-0009`, `SUBJECT-42`, `PATIENT-7`, NHS-style numbers, or SSN-style numbers.

Do not flag the synthetic lab labels this demo already uses: `RS-` reference standards, `CMP-` compound codes, `ALBT-` device ids, `RACK-` rack ids, `AR-` assay run ids, or generated sample ids of the form `S-<run>-<well>`.

## Regulatory impact

When the pull request touches `server/app/validated/` or `server/app/audit_trail/`, end the review with a regulatory-impact note. Use exactly one tier:

- **none** — docs or comments only, no change to a numeric result, limit, unit, or stored audit record
- **minor** — behavior stays inside an already written requirement in `docs/validation-plan.md`, including a correction that makes code match that requirement without editing the written limit, unit, formula, or rounding rule (SOP-DEMO-017 §5.2)
- **revalidation likely** — the change edits a written limit, unit, formula, or rounding rule, or the impact cannot be explained from the current requirements (SOP-DEMO-017 §5.3)

Give the reasons in a few sentences and cite the SOP section and any URS id you used. Do not call the change validated. Do not call the repository validated. Say that the note produces evidence for your validated process, and that a human decides the tier.
