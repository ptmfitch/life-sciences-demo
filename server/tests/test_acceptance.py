"""Acceptance criteria. Illustrative limits only."""

from decimal import Decimal

from app.validated.acceptance import (
    REFERENCE_SPECIMENS,
    SpecimenInput,
    activity_result,
    combine_results,
    disposition_for_reading,
    evaluate_specimen,
    recalculate_acceptance,
    report_activity,
    temperature_result,
)


def test_reported_activity_precision():
    assert report_activity(Decimal("41.24")) == Decimal("41.2")
    assert report_activity(Decimal("41.25")) == Decimal("41.3")
    assert report_activity(Decimal("10.04")) == Decimal("10.0")


def test_activity_clear_pass_and_fail():
    assert activity_result(Decimal("41.2")) == "PASS"
    assert activity_result(Decimal("90")) == "FAIL"


def test_exact_limit_passes():
    assert activity_result(Decimal("72.0")) == "PASS"
    specimen = evaluate_specimen(
        SpecimenInput("limit", Decimal("72.0"), Decimal("37.0"))
    )
    assert specimen.activity_result == "PASS"
    assert specimen.overall == "PASS"
    assert specimen.reported_activity == Decimal("72.0")


def test_temperature_bounds():
    assert temperature_result(Decimal("37.0")) == "PASS"
    assert temperature_result(Decimal("36.0")) == "PASS"
    assert temperature_result(Decimal("38.0")) == "PASS"
    assert temperature_result(Decimal("35.9")) == "FAIL"
    assert temperature_result(Decimal("38.1")) == "FAIL"


def test_overall_fails_when_temperature_fails():
    specimen = evaluate_specimen(
        SpecimenInput("hot", Decimal("40.0"), Decimal("39.2"))
    )
    assert specimen.activity_result == "PASS"
    assert specimen.temperature_result == "FAIL"
    assert specimen.overall == "FAIL"
    assert combine_results("PASS", "FAIL") == "FAIL"
    assert combine_results("PASS", "PASS") == "PASS"


def test_recalculate_counts_clear_cases():
    batch = recalculate_acceptance(
        [
            SpecimenInput("A", Decimal("10.0"), Decimal("37.0")),
            SpecimenInput("B", Decimal("90.0"), Decimal("37.0")),
        ]
    )
    assert [item.overall for item in batch.reference] == ["PASS", "FAIL"]
    assert batch.loaded == ()


def test_reference_catalog_labels():
    assert [item.label for item in REFERENCE_SPECIMENS] == [
        "RS-01",
        "RS-02",
        "RS-03",
        "RS-05",
        "RS-07",
    ]


def test_disposition_for_reading_clear_pass():
    payload = disposition_for_reading(41.2, 37.0, "A1")
    assert payload is not None
    assert payload["overall"] == "PASS"
    assert payload["label"] == "A1"


def test_disposition_for_reading_missing_signal():
    assert disposition_for_reading(41.2, None, "A1") is None
    assert disposition_for_reading(None, 37.0, "A1") is None
