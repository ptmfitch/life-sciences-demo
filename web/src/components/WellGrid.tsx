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
      <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wide text-muted">
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
        {labels.map((id) => (
          <div
            key={id}
            className="aspect-square rounded-full border border-white/60 shadow-inner"
            style={{ background: cellColor(byId.get(id)) }}
            title={`${id}: OD ${byId.get(id)?.optical_density ?? "—"}`}
          />
        ))}
      </div>
    </div>
  );
}