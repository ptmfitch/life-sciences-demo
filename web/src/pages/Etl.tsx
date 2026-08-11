import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import type { EtlJob, SourceFile } from "../lib/types";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { StatusBadge } from "../components/StatusBadge";

const STEPS = ["Scan", "Inspect", "Map", "Dry Run", "Load", "Review"] as const;

export function EtlPage({ showToast }: { showToast: (msg: string) => void }) {
  const [step, setStep] = useState(0);
  const [scan, setScan] = useState<{
    directory: string;
    file_count: number;
    total_rows: number;
    newest_file_timestamp: string | null;
    files: SourceFile[];
  } | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [inspectId, setInspectId] = useState<string | null>(null);
  const [inspection, setInspection] = useState<Record<string, unknown> | null>(null);
  const [mapping, setMapping] = useState<Record<string, unknown> | null>(null);
  const [dryJob, setDryJob] = useState<EtlJob | null>(null);
  const [loadJob, setLoadJob] = useState<EtlJob | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.defaultMapping().then(setMapping).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!loadJob || loadJob.status !== "running") return;
    const t = window.setInterval(async () => {
      try {
        const job = await api.getJob(loadJob.id);
        setLoadJob(job);
        if (job.status === "complete" || job.status === "cancelled") {
          setStep(5);
        }
      } catch {
        /* ignore */
      }
    }, 800);
    return () => window.clearInterval(t);
  }, [loadJob]);

  const enabledFields = useMemo(() => {
    if (!mapping) return [];
    const fields = (mapping.fields || {}) as Record<string, { enabled?: boolean }>;
    const selectedCols = (mapping.selected as string[]) || Object.keys(fields);
    return selectedCols.filter((c) => fields[c]?.enabled !== false);
  }, [mapping]);

  async function doScan() {
    setBusy(true);
    try {
      const result = await api.scan();
      setScan(result);
      setSelected(result.files.filter((f) => f.id && f.ingestion_status !== "ingested").map((f) => f.id));
      setStep(0);
      showToast(`Scanned ${result.file_count} files`);
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  async function doInspect(id: string) {
    setBusy(true);
    try {
      setInspectId(id);
      const data = await api.inspect(id);
      setInspection(data);
      setStep(1);
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Inspect failed");
    } finally {
      setBusy(false);
    }
  }

  async function doDryRun() {
    if (!mapping || selected.length === 0) return;
    setBusy(true);
    try {
      const job = await api.dryRun(selected, mapping);
      setDryJob(job);
      setStep(3);
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Dry run failed");
    } finally {
      setBusy(false);
    }
  }

  async function doLoad() {
    if (!mapping || selected.length === 0) return;
    setBusy(true);
    try {
      const job = await api.load(selected, mapping);
      setLoadJob(job);
      setStep(4);
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ErrorBoundary title="ETL page error">
      <div className="space-y-6">
        <section className="rounded-2xl border border-line bg-card p-5 shadow-card">
          <h2 className="text-xl font-semibold">ETL — CSV into Postgres</h2>
          <p className="mt-1 text-sm text-muted">
            Discover → Inspect → Map → Dry Run → Load → Review. Synthetic source data only.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {STEPS.map((label, i) => (
              <button
                key={label}
                type="button"
                onClick={() => setStep(i)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                  i === step
                    ? "bg-accent text-white"
                    : i < step
                      ? "bg-accentSoft text-accent"
                      : "bg-canvas text-muted"
                }`}
              >
                {i + 1}. {label}
              </button>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-line bg-card p-5 shadow-card space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold">Source directory</h3>
              <p className="font-mono text-xs text-muted">
                {scan?.directory || "Not scanned yet"}
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={doScan}
              className="rounded-xl border border-line bg-canvas px-3 py-2 text-sm font-medium hover:bg-accentSoft"
            >
              Rescan directory
            </button>
          </div>
          {scan && (
            <div className="grid gap-3 sm:grid-cols-4 text-sm">
              <Stat label="Files" value={String(scan.file_count)} />
              <Stat label="Total rows" value={String(scan.total_rows)} />
              <Stat
                label="Newest"
                value={
                  scan.newest_file_timestamp
                    ? new Date(scan.newest_file_timestamp).toLocaleString()
                    : "—"
                }
              />
              <Stat
                label="Pending"
                value={String(
                  scan.files.filter((f) => f.ingestion_status === "pending").length
                )}
              />
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-muted">
                <tr>
                  <th className="py-2 pr-3">Select</th>
                  <th className="py-2 pr-3">Filename</th>
                  <th className="py-2 pr-3">Test</th>
                  <th className="py-2 pr-3">Device</th>
                  <th className="py-2 pr-3">Rows</th>
                  <th className="py-2 pr-3">Size</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2">Inspect</th>
                </tr>
              </thead>
              <tbody>
                {(scan?.files || []).map((f) => (
                  <tr key={f.id || f.filename} className="border-t border-line">
                    <td className="py-2 pr-3">
                      {f.id ? (
                        <input
                          type="checkbox"
                          checked={selected.includes(f.id)}
                          onChange={(e) => {
                            setSelected((prev) =>
                              e.target.checked
                                ? [...prev, f.id]
                                : prev.filter((x) => x !== f.id)
                            );
                          }}
                        />
                      ) : null}
                    </td>
                    <td className="py-2 pr-3 font-mono text-xs">{f.filename}</td>
                    <td className="py-2 pr-3">{f.test_name || "—"}</td>
                    <td className="py-2 pr-3 font-mono text-xs">{f.device_id || "—"}</td>
                    <td className="py-2 pr-3">{f.row_count ?? "—"}</td>
                    <td className="py-2 pr-3">
                      {f.size_bytes != null ? `${Math.round(f.size_bytes / 1024)} KB` : "—"}
                    </td>
                    <td className="py-2 pr-3">
                      <StatusBadge status={f.ingestion_status} />
                      {f.error ? <div className="text-xs text-failed">{f.error}</div> : null}
                    </td>
                    <td className="py-2">
                      {f.id ? (
                        <button
                          type="button"
                          className="text-accent underline text-xs"
                          onClick={() => doInspect(f.id)}
                        >
                          Inspect
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!scan && (
              <p className="py-8 text-center text-sm text-muted">
                Scan the telemetry directory to begin.
              </p>
            )}
          </div>
        </section>

        {inspection && (
          <section className="rounded-2xl border border-line bg-card p-5 shadow-card space-y-4">
            <h3 className="font-semibold">
              Schema inspector — {(inspection.filename as string) || inspectId}
            </h3>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-xs uppercase text-muted">
                    <tr>
                      <th className="py-1 pr-2 text-left">Column</th>
                      <th className="py-1 pr-2 text-left">Category</th>
                      <th className="py-1 pr-2 text-left">Type</th>
                      <th className="py-1 pr-2 text-left">Nulls</th>
                      <th className="py-1 text-left">Examples</th>
                    </tr>
                  </thead>
                  <tbody>
                    {((inspection.columns as Array<Record<string, unknown>>) || []).map(
                      (c) => (
                        <tr key={String(c.name)} className="border-t border-line">
                          <td className="py-1 pr-2 font-mono text-xs">{String(c.name)}</td>
                          <td className="py-1 pr-2 text-xs">{String(c.category)}</td>
                          <td className="py-1 pr-2 text-xs">{String(c.inferred_type)}</td>
                          <td className="py-1 pr-2 text-xs">
                            {String(c.null_count)} ({String(c.null_pct)}%)
                          </td>
                          <td className="py-1 text-xs text-muted">
                            {((c.examples as string[]) || []).join(", ")}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
              <div>
                <div className="mb-2 text-xs uppercase text-muted">Preview rows</div>
                <pre className="max-h-80 overflow-auto rounded-xl bg-canvas p-3 text-[11px] font-mono">
                  {JSON.stringify(inspection.preview, null, 2)}
                </pre>
              </div>
            </div>
            <button
              type="button"
              className="rounded-xl bg-accent px-3 py-2 text-sm font-medium text-white"
              onClick={() => setStep(2)}
            >
              Continue to mapping
            </button>
          </section>
        )}

        {mapping && step >= 2 && (
          <section className="rounded-2xl border border-line bg-card p-5 shadow-card space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-semibold">Field mapping</h3>
              <button
                type="button"
                className="rounded-xl border border-line px-3 py-1.5 text-xs"
                onClick={async () => {
                  try {
                    await api.saveMapping("default", mapping);
                    showToast("Mapping saved");
                  } catch (e) {
                    showToast(e instanceof Error ? e.message : "Save failed");
                  }
                }}
              >
                Save mapping
              </button>
            </div>
            <p className="text-sm text-muted">
              Selected fields: {enabledFields.length}. Required: event_timestamp, device_id,
              assay_run_id, well_id.
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="text-xs uppercase text-muted">
                  <tr>
                    <th className="py-1 pr-2 text-left">Load</th>
                    <th className="py-1 pr-2 text-left">Source</th>
                    <th className="py-1 pr-2 text-left">Destination</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(
                    (mapping.fields || {}) as Record<
                      string,
                      { enabled?: boolean; destination?: string }
                    >
                  ).map(([src, cfg]) => (
                    <tr key={src} className="border-t border-line">
                      <td className="py-1 pr-2">
                        <input
                          type="checkbox"
                          checked={cfg.enabled !== false}
                          onChange={(e) => {
                            setMapping((m) => {
                              if (!m) return m;
                              const fields = {
                                ...(m.fields as Record<string, unknown>),
                                [src]: { ...cfg, enabled: e.target.checked },
                              };
                              return { ...m, fields };
                            });
                          }}
                        />
                      </td>
                      <td className="py-1 pr-2 font-mono text-xs">{src}</td>
                      <td className="py-1 pr-2 font-mono text-xs">
                        {cfg.destination || src}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={busy || selected.length === 0}
                onClick={doDryRun}
                className="rounded-xl bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                Run dry run
              </button>
            </div>
          </section>
        )}

        {dryJob && (
          <section className="rounded-2xl border border-line bg-card p-5 shadow-card space-y-3">
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-attention">
              Dry run complete — no database changes have been made.
            </div>
            <h3 className="font-semibold">Dry run summary</h3>
            <div className="grid gap-3 sm:grid-cols-4 text-sm">
              <Stat label="Processed" value={String(dryJob.processed_rows)} />
              <Stat label="Would insert" value={String(dryJob.inserted_rows)} />
              <Stat label="Warnings" value={String(dryJob.warning_rows)} />
              <Stat label="Rejected" value={String(dryJob.rejected_rows)} />
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={doLoad}
              className="rounded-xl bg-accent px-3 py-2 text-sm font-medium text-white"
            >
              Load into Postgres
            </button>
          </section>
        )}

        {loadJob && (
          <section className="rounded-2xl border border-line bg-card p-5 shadow-card space-y-3">
            <h3 className="font-semibold">Load progress</h3>
            <div className="h-3 overflow-hidden rounded-full bg-canvas">
              <div
                className="h-full bg-accent transition-all"
                style={{ width: `${loadJob.progress_pct || 0}%` }}
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-4 text-sm">
              <Stat label="Progress" value={`${loadJob.progress_pct || 0}%`} />
              <Stat label="Inserted" value={String(loadJob.inserted_rows)} />
              <Stat label="Skipped" value={String(loadJob.skipped_rows)} />
              <Stat label="Rejected" value={String(loadJob.rejected_rows)} />
            </div>
            <p className="text-xs text-muted">
              Phase: {loadJob.current_phase || "—"} · File: {loadJob.current_file || "—"} ·
              Status: {loadJob.status}
              {loadJob.estimated_remaining_seconds != null
                ? ` · ETA ${loadJob.estimated_remaining_seconds}s`
                : ""}
            </p>
            {loadJob.status === "running" ? (
              <button
                type="button"
                className="rounded-xl border border-line px-3 py-1.5 text-sm"
                onClick={() => api.cancelJob(loadJob.id).then(setLoadJob)}
              >
                Cancel load
              </button>
            ) : null}
            {loadJob.status === "complete" ? (
              <div className="text-sm text-healthy">
                Load complete. Open Dashboards to visualise historical telemetry. Re-running
                load will skip already-ingested files.
              </div>
            ) : null}
          </section>
        )}
      </div>
    </ErrorBoundary>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-canvas px-3 py-2">
      <div className="text-[10px] uppercase text-muted">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}