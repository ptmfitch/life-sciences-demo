"""Acceptance criteria for synthetic specimen activity and temperature.

Illustrative limits only. They are not a validated assay method.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Literal, Sequence

Result = Literal["PASS", "FAIL"]

REPORTED_QUANTUM = Decimal("0.1")
ACTIVITY_UPPER_SPEC = Decimal("72.0")
TEMP_LOW = Decimal("36.0")
TEMP_HIGH = Decimal("38.0")

ACTIVITY_RULE = (
    "Pass when the reported activity index (half-up to 1 decimal place) "
    "is less than or equal to 72.0."
)
TEMPERATURE_RULE = (
    "Pass when the reported temperature (half-up to 1 decimal place) "
    "is from 36.0 °C through 38.0 °C, inclusive."
)
DISCLAIMER = (
    "Illustrative only. Synthetic limits for this demo — not a validated method. "
    "Dispositions are evidence-shaped output for a process you validate elsewhere."
)


@dataclass(frozen=True)
class SpecimenInput:
    label: str
    activity_index: Decimal
    temperature_c: Decimal


@dataclass(frozen=True)
class SpecimenDisposition:
    label: str
    reported_activity: Decimal
    temperature_c: Decimal
    activity_result: Result
    temperature_result: Result
    overall: Result


@dataclass(frozen=True)
class AcceptanceBatch:
    reference: tuple[SpecimenDisposition, ...]
    loaded: tuple[SpecimenDisposition, ...]


REFERENCE_SPECIMENS: tuple[SpecimenInput, ...] = (
    SpecimenInput("RS-01", Decimal("41.24"), Decimal("37.02")),
    SpecimenInput("RS-02", Decimal("72.00"), Decimal("37.00")),
    SpecimenInput("RS-03", Decimal("72.04"), Decimal("37.10")),
    SpecimenInput("RS-05", Decimal("40.10"), Decimal("35.80")),
    SpecimenInput("RS-07", Decimal("88.57"), Decimal("36.95")),
)


def report_activity(activity_index: Decimal) -> Decimal:
    return activity_index.quantize(REPORTED_QUANTUM, rounding=ROUND_HALF_UP)


def report_temperature(temperature_c: Decimal) -> Decimal:
    return temperature_c.quantize(REPORTED_QUANTUM, rounding=ROUND_HALF_UP)


def activity_result(activity_index: Decimal) -> Result:
    if activity_index <= ACTIVITY_UPPER_SPEC:
        return "PASS"
    return "FAIL"


def temperature_result(temperature_c: Decimal) -> Result:
    reported = report_temperature(temperature_c)
    if TEMP_LOW <= reported <= TEMP_HIGH:
        return "PASS"
    return "FAIL"


def combine_results(activity: Result, temperature: Result) -> Result:
    if activity == "PASS" and temperature == "PASS":
        return "PASS"
    return "FAIL"


def evaluate_specimen(specimen: SpecimenInput) -> SpecimenDisposition:
    activity = activity_result(specimen.activity_index)
    temperature = temperature_result(specimen.temperature_c)
    return SpecimenDisposition(
        label=specimen.label,
        reported_activity=report_activity(specimen.activity_index),
        temperature_c=report_temperature(specimen.temperature_c),
        activity_result=activity,
        temperature_result=temperature,
        overall=combine_results(activity, temperature),
    )


def recalculate_acceptance(
    specimens: Sequence[SpecimenInput],
    loaded: Sequence[SpecimenInput] = (),
) -> AcceptanceBatch:
    return AcceptanceBatch(
        reference=tuple(evaluate_specimen(item) for item in specimens),
        loaded=tuple(evaluate_specimen(item) for item in loaded),
    )


def disposition_for_reading(
    activity_index: float | None,
    temperature_c: float | None,
    label: str,
) -> dict[str, Any] | None:
    """Disposition for one live or loaded reading. None when a signal is missing."""
    if activity_index is None or temperature_c is None:
        return None
    disposition = evaluate_specimen(
        SpecimenInput(
            label=label or "reading",
            activity_index=Decimal(str(activity_index)),
            temperature_c=Decimal(str(temperature_c)),
        )
    )
    return disposition_to_dict(disposition)


def disposition_to_dict(disposition: SpecimenDisposition) -> dict[str, Any]:
    return {
        "label": disposition.label,
        "reported_activity": float(disposition.reported_activity),
        "temperature_c": float(disposition.temperature_c),
        "activity_result": disposition.activity_result,
        "temperature_result": disposition.temperature_result,
        "overall": disposition.overall,
    }


def spec_payload() -> dict[str, Any]:
    return {
        "activity_upper_limit": float(ACTIVITY_UPPER_SPEC),
        "activity_decimals": 1,
        "temperature_low_c": float(TEMP_LOW),
        "temperature_high_c": float(TEMP_HIGH),
        "activity_rule": ACTIVITY_RULE,
        "temperature_rule": TEMPERATURE_RULE,
        "disclaimer": DISCLAIMER,
    }
