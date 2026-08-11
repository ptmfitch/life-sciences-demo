"""Pure synthetic signal model for AstraLume BioTest Station.

Illustrative only — not scientifically or clinically validated.
Deterministic given (seed, tick_index).
"""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


DEVICE_NAME = "AstraLume BioTest Station"
CSV_COLUMNS = [
    "event_timestamp",
    "test_name",
    "device_name",
    "device_id",
    "rack_id",
    "well_id",
    "assay_run_id",
    "sample_id",
    "compound_code",
    "elapsed_seconds",
    "temperature_c",
    "ph",
    "optical_density",
    "fluorescence_rfu",
    "dissolved_oxygen_pct",
    "reagent_concentration_mg_l",
    "activity_index",
    "status",
    "quality_flag",
]

WELL_LABELS = [f"{row}{col}" for row in "ABCDEF" for col in range(1, 5)]  # 24 wells


def slugify(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name.strip()).strip("-").lower()
    return slug[:48] or "unnamed"


def well_id_for_tick(tick: int, well_count: int = 24) -> str:
    wells = WELL_LABELS[:well_count]
    return wells[tick % len(wells)]


@dataclass
class RunIdentity:
    test_name: str
    device_id: str
    rack_id: str
    assay_run_id: str
    compound_code: str
    well_count: int = 24
    seed: int = 0
    regime: str = "suppression"  # growth | suppression


class Simulator:
    """Deterministic per-tick synthetic readings."""

    def __init__(self, identity: RunIdentity):
        self.identity = identity
        self._rng = random.Random(identity.seed)

    def reading_at(self, tick: int, started_at: datetime | None = None) -> dict[str, Any]:
        """Generate the reading for absolute tick index (0-based)."""
        # Re-seed from identity + tick for exact replay / resume
        rng = random.Random(self.identity.seed * 1_000_003 + tick)

        started = started_at or datetime.now(timezone.utc)
        ts = started.timestamp() + tick
        event_ts = datetime.fromtimestamp(ts, tz=timezone.utc)

        # Temperature: 37C +/- noise, with one scripted excursion around tick 90
        temp = 37.0 + rng.gauss(0, 0.08)
        quality = "pass"
        if 88 <= tick <= 95:
            temp = 39.2 + rng.gauss(0, 0.1)
            quality = "review"

        # pH: slow bounded drift
        ph = 7.2 + 0.25 * math.sin(tick / 180.0) + rng.gauss(0, 0.02)
        ph = max(6.8, min(7.6, ph))

        # Optical density: growth or suppression regime
        t = tick / 60.0
        if self.identity.regime == "growth":
            od = 0.15 + 0.85 / (1 + math.exp(-0.35 * (t - 8)))
        else:
            od = 0.9 * math.exp(-0.12 * t) + 0.08
        od = max(0.02, min(1.2, od + rng.gauss(0, 0.015)))

        # Fluorescence loosely correlates with microbial activity (OD)
        fluo = 120 + od * 480 + rng.gauss(0, 18)
        fluo = max(20.0, fluo)

        # Dissolved oxygen: slow walk
        do = 85 - 8 * math.sin(tick / 240.0) + rng.gauss(0, 0.6)
        do = max(55.0, min(98.0, do))
        dissolved: float | None = round(do, 2)
        # ~0.5% missing optional values
        if rng.random() < 0.005:
            dissolved = None
            if quality == "pass":
                quality = "missing_check"

        # Reagent concentration: slow decay
        reagent = max(0.5, 50.0 * math.exp(-0.004 * tick) + rng.gauss(0, 0.15))

        # Derived activity index (demo metric only)
        activity = 100 * (
            0.45 * (od / 1.2)
            + 0.25 * ((fluo - 20) / 700)
            + 0.15 * (1 - abs(temp - 37) / 5)
            + 0.15 * ((do - 55) / 43 if dissolved is not None else 0.5)
        )
        activity = max(0.0, min(100.0, activity))

        # Operational status (not clinical)
        if activity >= 72:
            status = "attention"
        else:
            status = "normal"

        well = well_id_for_tick(tick, self.identity.well_count)
        sample_id = f"S-{self.identity.assay_run_id[-4:]}-{well}"

        row = {
            "event_timestamp": event_ts.isoformat().replace("+00:00", "Z"),
            "test_name": self.identity.test_name,
            "device_name": DEVICE_NAME,
            "device_id": self.identity.device_id,
            "rack_id": self.identity.rack_id,
            "well_id": well,
            "assay_run_id": self.identity.assay_run_id,
            "sample_id": sample_id,
            "compound_code": self.identity.compound_code,
            "elapsed_seconds": tick,
            "temperature_c": round(temp, 3),
            "ph": round(ph, 3),
            "optical_density": round(od, 4),
            "fluorescence_rfu": round(fluo, 2),
            "dissolved_oxygen_pct": dissolved,
            "reagent_concentration_mg_l": round(reagent, 3),
            "activity_index": round(activity, 2),
            "status": status,
            "quality_flag": quality,
        }

        # Plant one duplicate-looking row once per run (tick 42)
        # Caller may choose to emit it; we mark via quality_flag hint
        if tick == 42:
            row["_duplicate_candidate"] = True

        # Per-well ephemeral values for live visualisation
        wells = self._well_snapshot(tick, od, fluo, activity)
        row["wells"] = wells
        return row

    def _well_snapshot(
        self, tick: int, od: float, fluo: float, activity: float
    ) -> list[dict[str, Any]]:
        wells = []
        for i, label in enumerate(WELL_LABELS[: self.identity.well_count]):
            wrng = random.Random(self.identity.seed + tick * 97 + i)
            local_od = max(0.02, od + wrng.gauss(0, 0.04) + (0.08 if i % 5 == 0 else 0))
            local_fluo = max(20.0, fluo + wrng.gauss(0, 25))
            local_act = max(0.0, min(100.0, activity + wrng.gauss(0, 4)))
            wells.append(
                {
                    "well_id": label,
                    "optical_density": round(local_od, 4),
                    "fluorescence_rfu": round(local_fluo, 2),
                    "activity_index": round(local_act, 2),
                }
            )
        return wells


def regime_for_compound(compound_code: str) -> str:
    # Even-coded compounds suppress; odd grow — purely demo convention
    digits = re.sub(r"\D", "", compound_code) or "0"
    return "growth" if int(digits) % 2 else "suppression"