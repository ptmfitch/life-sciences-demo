"""Specimen acceptance for the synthetic AstraLume console.

Illustrative only — not a validated method. Callers use these results so the
demo can show change-controlled calculation output in the UI.
"""

from app.validated.acceptance import (
    REFERENCE_SPECIMENS,
    activity_result,
    disposition_for_reading,
    evaluate_specimen,
    recalculate_acceptance,
    report_activity,
    temperature_result,
)

__all__ = [
    "REFERENCE_SPECIMENS",
    "activity_result",
    "disposition_for_reading",
    "evaluate_specimen",
    "recalculate_acceptance",
    "report_activity",
    "temperature_result",
]
