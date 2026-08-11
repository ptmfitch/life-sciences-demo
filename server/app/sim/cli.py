"""Optional developer CLI for writing synthetic CSVs without the server."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.sim.simulator import RunIdentity, Simulator, regime_for_compound
from app.sim.writer import build_filename, maybe_duplicate_row, write_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Write synthetic AstraLume CSVs (debug only)")
    parser.add_argument("--test-name", default="Debug Run")
    parser.add_argument("--device-id", default="ALBT-001")
    parser.add_argument("--rack-id", default="RACK-01")
    parser.add_argument("--assay-run-id", default="AR-DEBUG-001")
    parser.add_argument("--compound-code", default="CMP-A01")
    parser.add_argument("--minutes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=settings.seed)
    parser.add_argument("--out", type=Path, default=settings.telemetry_path)
    args = parser.parse_args()

    identity = RunIdentity(
        test_name=args.test_name,
        device_id=args.device_id,
        rack_id=args.rack_id,
        assay_run_id=args.assay_run_id,
        compound_code=args.compound_code,
        seed=args.seed,
        regime=regime_for_compound(args.compound_code),
    )
    sim = Simulator(identity)
    started = datetime.now(timezone.utc)
    args.out.mkdir(parents=True, exist_ok=True)

    for minute in range(args.minutes):
        rows = [
            sim.reading_at(minute * 60 + t, started_at=started) for t in range(60)
        ]
        rows = maybe_duplicate_row(rows)
        when = datetime.fromtimestamp(started.timestamp() + minute * 60, tz=timezone.utc)
        path = args.out / build_filename(args.test_name, args.device_id, when)
        write_csv(path, rows)
        print(f"Wrote {path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()