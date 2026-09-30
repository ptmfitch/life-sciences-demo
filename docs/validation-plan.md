DEMO / SYNTHETIC · for enablement only

# Validation plan — synthetic specimen acceptance

Illustrative only. This plan lists requirements for the demo calculation so a review can trace a diff to an id and a test. It produces evidence for your validated process. It is not a validation report, and the calculation is not validated.

Synthetic data only — not medical, clinical, diagnostic, or regulatory evidence. See [SYNTHETIC_MODEL.md](SYNTHETIC_MODEL.md).

Companion procedure: [SOP-DEMO-017](sop-demo-017-change-control.md).

## 1. Item under discussion

The specimen acceptance package at `server/app/validated/` and the append-only audit package at `server/app/audit_trail/`.

The Dashboards **Specimen acceptance** panel and the Monitor **Spec** mark call `evaluate_specimen` / `disposition_for_reading`. ETL loads call `etl_load_record`. **Recalculate dispositions** calls `acceptance_recalculation_record`.

## 2. Intended use in the demo

Show a change-controlled number (pass or fail against a written limit) moving through a pull request, a review rule, an evidence comment, and a human handoff. The numbers are synthetic reference standards plus whatever telemetry the local simulator has loaded.

## 3. Requirements

| Id | The system shall | Code | Tests that exercise it |
| --- | --- | --- | --- |
| URS-010 | Append one audit event when an ETL load commits rows, naming who (`console.etl`), what (`etl_load_committed`), when (timestamp), and why (the commit reason), plus row counts | `etl_load_record`, `insert_audit_event` | `server/tests/test_audit_trail.py::test_etl_load_record_names_who_what_when_why` |
| URS-011 | Append one audit event when specimen acceptance is recalculated from the dashboard, with the same who / what / when / why shape | `acceptance_recalculation_record` | `server/tests/test_audit_trail.py::test_recalculation_record_names_who_what_when_why` |
| URS-012 | Pass temperature when the reported temperature, half-up to one decimal place, is from 36.0 °C through 38.0 °C inclusive; otherwise fail | `report_temperature`, `temperature_result` | `server/tests/test_acceptance.py::test_temperature_bounds` |
| URS-013 | Fail activity when the activity index is clearly above the upper spec, and pass when it is clearly below | `activity_result` | `server/tests/test_acceptance.py::test_activity_clear_pass_and_fail` |
| URS-014 | Report activity half-up to one decimal place. Pass activity when that reported value is less than or equal to 72.0 | `report_activity`, `activity_result`, `evaluate_specimen` | `server/tests/test_acceptance.py::test_reported_activity_precision`, `server/tests/test_acceptance.py::test_exact_limit_passes` |
| URS-015 | Set the overall disposition to PASS only when activity and temperature are both PASS | `combine_results`, `evaluate_specimen` | `server/tests/test_acceptance.py::test_overall_fails_when_temperature_fails` |

URS-014 is the requirement the acceptance panel states in its rule sentence. The panel shows the reported activity.

## 4. Reference standards

The catalog `REFERENCE_SPECIMENS` in `server/app/validated/acceptance.py` is the fixed input for the panel. Labels: RS-01, RS-02, RS-03, RS-05, RS-07. They are synthetic. They are not patients, subjects, or clinical samples.

Loaded assay rows on the same panel are averages from `telemetry_readings` passed through the same functions.

## 5. Trace rules for a reviewer

- A diff under `server/app/validated/` names the URS ids whose functions it edits.
- A diff that changes those functions ships a test change under `server/tests/` in the same pull request (SOP-DEMO-017 §6).
- Classification uses SOP-DEMO-017 §5. Restoring code so it matches a row in §3, without editing the written limit, unit, formula, or rounding rule, is a documented minor change (§5.2). Editing a written limit, unit, formula, or rounding rule is revalidation likely (§5.3).
- A bot may draft that classification. A person accepts it (SOP-DEMO-017 §8).

## 6. What this plan does not cover

Operational run status (`normal` / `attention` and the demo attention line at 72 on the activity chart) is a separate live-monitor label. It is not this disposition. Data-quality flags from the simulator (`pass` / `review` / `missing_check`) are not specimen acceptance.
