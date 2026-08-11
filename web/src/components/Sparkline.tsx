export function Sparkline({ values }: { values?: number[] | null }) {
  const pts = values || [];
  if (pts.length < 2) {
    return (
      <div className="h-10 rounded-lg bg-canvas text-[10px] text-muted flex items-center justify-center">
        Waiting for readings…
      </div>
    );
  }
  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const span = Math.max(max - min, 0.01);
  const w = 120;
  const h = 40;
  const d = pts
    .map((v, i) => {
      const x = (i / (pts.length - 1)) * w;
      const y = h - ((v - min) / span) * (h - 4) - 2;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-10 w-full overflow-visible">
      <path d={d} fill="none" stroke="#1d6b5c" strokeWidth="1.8" />
    </svg>
  );
}