from app.sim.simulator import RunIdentity, Simulator, slugify, regime_for_compound
from app.sim.writer import build_filename, maybe_duplicate_row, write_csv


def test_slugify_strips_punctuation():
    assert slugify("Compound A - Rack 01!") == "compound-a-rack-01"
    assert slugify("  ") == "unnamed"


def test_filename_safe():
    name = build_filename("Stability Trial / North Wing", "ALBT-001")
    assert " " not in name
    assert "/" not in name
    assert name.startswith("AstraLume-BioTest-Station-")
    assert "ALBT-001" in name
    assert name.endswith(".csv")


def test_simulator_deterministic():
    identity = RunIdentity(
        test_name="T",
        device_id="ALBT-001",
        rack_id="RACK-01",
        assay_run_id="AR-1",
        compound_code="CMP-A01",
        seed=99,
        regime=regime_for_compound("CMP-A01"),
    )
    a = Simulator(identity).reading_at(10)
    b = Simulator(identity).reading_at(10)
    assert a["temperature_c"] == b["temperature_c"]
    assert a["optical_density"] == b["optical_density"]
    assert a["activity_index"] == b["activity_index"]


def test_simulator_regime_differs():
    base = dict(
        test_name="T",
        device_id="ALBT-001",
        rack_id="RACK-01",
        assay_run_id="AR-1",
        compound_code="CMP-A01",
        seed=7,
    )
    grow = Simulator(RunIdentity(**base, regime="growth")).reading_at(600)
    suppress = Simulator(RunIdentity(**base, regime="suppression")).reading_at(600)
    assert grow["optical_density"] != suppress["optical_density"]


def test_csv_write_and_duplicate(tmp_path):
    identity = RunIdentity(
        test_name="Edge Case",
        device_id="ALBT-002",
        rack_id="RACK-02",
        assay_run_id="AR-2",
        compound_code="CMP-B02",
        seed=1,
        regime="growth",
    )
    sim = Simulator(identity)
    rows = [sim.reading_at(t) for t in range(60)]
    rows = maybe_duplicate_row(rows)
    assert len(rows) >= 60
    # Duplicate planted at tick 42
    assert any(r.get("quality_flag") == "review" for r in rows)
    path = tmp_path / build_filename(identity.test_name, identity.device_id)
    write_csv(path, rows)
    text = path.read_text()
    assert "event_timestamp" in text
    assert "AstraLume BioTest Station" not in path.name  # spaces not in filename
    assert identity.test_name in text