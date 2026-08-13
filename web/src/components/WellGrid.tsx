import type { WellState } from "../lib/types";

function cellColor(well?: WellState) {
  if (!well) return "#e6e5e0";
  const od = well.optical_density ?? 0;
  const fluo = Math.min(1, (well.fluorescence_rfu ?? 0) / 700);
  const intensity = Math.min(1, od * 0.65 + fluo * 0.35);
  const r = Math.round(29 + (180 - 29) * intensity);
  const g = Math.round(107 + (80 - 107) * intensity);
  const b = Math.round(92 + (40 - 92) * intensity);
  return `rgb(${r},${g},${b})`;
}

function legendSwatch(intensity: number) {
  return cellColor({
    well_id: "",
    optical_density: intensity,
    fluorescence_rfu: intensity * 700,
    activity_index: 0,
  });
}

function wellAriaLabel(id: string, well?: WellState) {
  if (!well) return `${id}: empty`;
  const od = well.optical_density?.toFixed(3) ?? "—";
  const fluo = well.fluorescence_rfu?.toFixed(0) ?? "—";
  const activity = well.activity_index?.toFixed(1) ?? "—";
  return `${id}: OD ${od}, fluorescence ${fluo}, activity ${activity}`;
}

export function WellGrid({
  wells,
  wellCount = 24,
}: {
  wells?: WellState[] | null;
  wellCount?: number;
}) {
  const cols = 4;
  const rows = Math.ceil(wellCount / cols);
  const byId = new Map((wells || []).map((w) => [w.well_id, w]));
  const labels = Array.from({ length: wellCount }, (_, i) => {
    const row = String.fromCharCode(65 + Math.floor(i / cols));
    const col = (i % cols) + 1;
    return `${row}${col}`;
  });

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs uppercase tracking-wide text-muted">
        <span>Synthetic assay panel</span>
        <span>
          {rows}×{cols} wells
        </span>
      </div>
      <div
        className="grid gap-1 rounded-xl border border-line bg-canvas p-2"
        style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
        title="Synthetic visualisation — not a scientific simulator"
      >
        {labels.map((id) => {
          const well = byId.get(id);
          return (
            <div
              key={id}
              role="img"
              className="aspect-square rounded-full border border-white/60 shadow-inner"
              style={{ background: cellColor(well) }}
              title={`${id}: OD ${well?.optical_density ?? "—"}`}
              aria-label={wellAriaLabel(id, well)}
            />
          );
        })}
      </div>
      <div className="mt-2">
        <div className="flex items-center gap-2 text-xs text-muted">
          <span>Low</span>
          <div className="flex flex-1 items-center gap-1">
            <span
              className="h-3 flex-1 rounded-sm border border-line"
              style={{ background: legendSwatch(0) }}
              title="Low"
            />
            <span
              className="h-3 flex-1 rounded-sm border border-line"
              style={{ background: legendSwatch(0.5) }}
              title="Mid"
            />
            <span
              className="h-3 flex-1 rounded-sm border border-line"
              style={{ background: legendSwatch(1) }}
              title="High"
            />
          </div>
          <span>High</span>
        </div>
        <p className="mt-1 text-xs text-muted">
          Synthetic OD + fluorescence (illustrative)
        </p>
      </div>
    </div>
  );
}
