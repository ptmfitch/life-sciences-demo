const styles: Record<string, string> = {
  pending: "bg-canvas text-muted border-line",
  running: "bg-emerald-50 text-healthy border-emerald-100",
  paused: "bg-slate-100 text-paused border-slate-200",
  stopped: "bg-slate-100 text-paused border-slate-200",
  complete: "bg-teal-50 text-complete border-teal-100",
  attention: "bg-amber-50 text-attention border-amber-100",
  interrupted: "bg-rose-50 text-failed border-rose-100",
  normal: "bg-emerald-50 text-healthy border-emerald-100",
};

export function StatusBadge({ status }: { status: string }) {
  const cls = styles[status] || styles.pending;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}
    >
      {status}
    </span>
  );
}