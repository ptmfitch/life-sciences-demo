DEMO / SYNTHETIC · for enablement only

# Sample Compliance Evidence Pack

Pre-baked fallback comment for the pull request that fixes the reported bug. Paste it as a pull request comment when the live automation is slow. It is an example, not a live review, and it is not an approval.

Illustrative only. This comment produces evidence for your validated process.

---

DEMO / SYNTHETIC · for enablement only
Illustrative only. This comment produces evidence for your validated process. It is not an approval.

## Compliance Evidence Pack

### Change summary

The draft pull request addresses the reported bug on the Dashboards specimen acceptance panel. In this example the diff is limited to the validated calculation. Audit-trail files are unchanged. This pack does not restate a root cause; the diff is the source for what changed.

### Impacted requirements

- URS-014 — reported activity and the activity disposition the panel displays
- URS-015 — overall disposition, because it follows the activity result

No written limit, unit, formula, or rounding rule in the validation plan is edited in this example.

### Risk tier

**minor**

SOP-DEMO-017 §5.2. The written requirements stay as they are, and the example diff does not revise a limit, unit, formula, or rounding rule. QA has not accepted this tier.

### Test results

Not run in this example comment.

The repository's check is `cd server && uv run pytest -q`. This example assumes that command was not executed for the fix, and that the diff does not yet include a file under `server/tests/`.

### Bugbot findings

| Finding | Flagged | Status |
| --- | --- | --- |
| Missing change control reference | yes | open — description has no new `CR-#####`. `CR-00042` is the example baseline and does not identify this change |
| Missing test evidence | yes | open — validated code is in the diff and `server/tests/` is not |
| Audit-trail change requires QA impact assessment | yes | not raised — `server/app/audit_trail/` is unchanged in this example |
| Possible patient or subject identifier | yes | not raised — no new patient or subject literal in this example |

Regulatory-impact note from the rules: **minor**, for the same §5.2 reason as the tier above. A human decides.

### Open questions for QA

- Which new change-request id (`CR-` plus five digits, other than CR-00042) should go in the description?
- Which test diff will accompany the validated code change?
- Do you accept the minor tier under SOP-DEMO-017 §5.2, or do you want this treated as revalidation likely under §5.3?

Stopping here. This example does not approve, sign, or merge.
