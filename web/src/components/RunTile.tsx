import { useEffect, useState } from "react";
import type { Run } from "../lib/types";
import { Sparkline } from "./Sparkline";
import { StatusBadge } from "./StatusBadge";
import { WellGrid } from "./WellGrid";

function Metric({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="rounded-lg bg-canvas px-2 py-1.5">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="font-mono text-sm font-medium">
        {value}
        {unit ? <span className="ml-0.5 text-xs text-muted">{unit}</span> : null}
      </div>
    </div>
  );
}

function fmt(n: number | null | undefined, digits = 2) {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toFixed(digits);
}

export function RunTile({
  run,
  onAction,
}: {
  run: Run & { _pulse?: number };
  onAction: (id: string, action: string) => void;
}) {
  const [pulse, setPulse] = useState(false);
  useEffect(() => {
    if (!run.last_reading_at) return;
    setPulse(true);
    const t = window.setTimeout(() => setPulse(false), 700);
    return () => window.clearTimeout(t);
  }, [run.last_reading_at]);

  const latest = run.latest;
  const elapsed = run.elapsed_seconds ?? run.tick_index ?? 0;

  return (
    <article
      className={`rounded-2xl border border-line bg-card p-4 shadow-card transition ${
        pulse ? "pulse-new" : ""
      }`}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-ink">{run.test_name}</h3>
          <div className="mt-0.5 font-mono text-xs text-muted">{run.assay_run_id}</div>
        </div>
        <StatusBadge status={run.status} />
      </div>

      <div className="mb-3 grid grid-cols-3 gap-2 text-xs text-muted">
        <div>
          <div className="text-xs uppercase">Device</div>
          <div className="font-mono text-ink">{run.device_id}</div>
        </div>
        <div>
          <div className="text-xs uppercase">Rack</div>
          <div className="font-mono text-ink">{run.rack_id}</div>
        </div>
        <div>
          <div className="text-xs uppercase">Wells</div>
          <div className="font-mono text-ink">{run.well_count}</div>
        </div>
      </div>

      <WellGrid wells={run.wells} wellCount={run.well_count} />

      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Metric label="Temp" value={fmt(latest?.temperature_c, 2)} unit="°C" />
        <Metric label="pH" value={fmt(latest?.ph, 2)} />
        <Metric label="Optical density" value={fmt(latest?.optical_density, 3)} />
        <Metric label="Fluorescence" value={fmt(latest?.fluorescence_rfu, 0)} unit="RFU" />
        <Metric label="Dissolved O₂" value={fmt(latest?.dissolved_oxygen_pct, 1)} unit="%" />
        <Metric label="Reagent" value={fmt(latest?.reagent_concentration_mg_l, 1)} unit="mg/L" />
        <Metric label="Activity" value={fmt(latest?.activity_index, 1)} />
        <Metric label="Rows / files" value={`${run.row_count} / ${run.file_count}`} />
      </div>

      <div className="mt-3">
        <div className="mb-1 text-xs uppercase tracking-wide text-muted">
          Activity index (demo)
        </div>
        <Sparkline values={run.sparkline} />
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-muted">
        <span>Elapsed {elapsed}s</span>
        <span>
          {run.last_reading_at
            ? new Date(run.last_reading_at).toLocaleTimeString()
            : "No readings yet"}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {run.status === "pending" || run.status === "stopped" || run.status === "interrupted" ? (
          <Btn onClick={() => onAction(run.id, "start")}>Start</Btn>
        ) : null}
        {run.status === "running" ? (
          <Btn onClick={() => onAction(run.id, "pause")}>Pause</Btn>
        ) : null}
        {run.status === "paused" ? (
          <Btn onClick={() => onAction(run.id, "resume")}>Resume</Btn>
        ) : null}
        {run.status === "running" || run.status === "paused" ? (
          <Btn onClick={() => onAction(run.id, "stop")}>Stop</Btn>
        ) : null}
        <Btn onClick={() => onAction(run.id, "restart")}>Restart</Btn>
        <Btn tone="danger" onClick={() => onAction(run.id, "clear")}>
          Clear
        </Btn>
      </div>
      {run.error_message ? (
        <p className="mt-2 text-xs text-failed">{run.error_message}</p>
      ) : null}
    </article>
  );
}

function Btn({
  children,
  onClick,
  tone = "default",
}: {
  children: React.ReactNode;
  onClick: () => void;
  tone?: "default" | "danger";
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
        tone === "danger"
          ? "border-rose-200 bg-rose-50 text-failed hover:bg-rose-100"
          : "border-line bg-canvas text-ink hover:bg-accentSoft hover:text-accent"
      }`}
    >
      {children}
    </button>
  );
}