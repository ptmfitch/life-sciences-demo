import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../lib/api";
import { ErrorBoundary } from "../components/ErrorBoundary";

const DEFAULT_FIELDS = ["temperature_c", "optical_density", "activity_index"];
const HEATMAP_COLS = 4;

function parseFieldsParam(raw: string | null): string[] {
  if (!raw) return [...DEFAULT_FIELDS];
  const parsed = raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  return parsed.length > 0 ? parsed : [...DEFAULT_FIELDS];
}

function formatQualityKey(key: string): string {
  return key.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function DashboardsPage({ showToast }: { showToast: (msg: string) => void }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<{
    device_ids: string[];
    assay_run_ids: string[];
    test_names: string[];
    metrics: string[];
  } | null>(null);
  const [deviceId, setDeviceId] = useState(() => searchParams.get("device") || "");
  const [assayId, setAssayId] = useState(() => searchParams.get("assay") || "");
  const [fields, setFields] = useState(() => parseFieldsParam(searchParams.get("fields")));
  const [timeseries, setTimeseries] = useState<Record<string, unknown> | null>(null);
  const [compare, setCompare] = useState<Record<string, unknown> | null>(null);
  const [statusDist, setStatusDist] = useState<Record<string, unknown> | null>(null);
  const [quality, setQuality] = useState<Record<string, unknown> | null>(null);
  const [heatmap, setHeatmap] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api
      .dashFilters()
      .then(setFilters)
      .catch((e) => showToast(e instanceof Error ? e.message : "Failed to load filters"));
  }, [showToast]);

  async function refresh() {
    try {
      const params = new URLSearchParams();
      params.set("fields", fields.join(","));
      if (deviceId) params.set("device_id", deviceId);
      if (assayId) params.set("assay_run_id", assayId);
      const [ts, cmp, st, q, hm] = await Promise.all([
        api.timeseries(params),
        api.compare("activity_index"),
        api.statusDistribution(),
        api.quality(),
        api.wellHeatmap(assayId || undefined),
      ]);
      setTimeseries(ts);
      setCompare(cmp);
      setStatusDist(st);
      setQuality(q);
      setHeatmap(hm);
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Dashboard query failed");
    }
  }

  // Persist filters in the URL so presenters can deep-link.
  useEffect(() => {
    const next = new URLSearchParams();
    if (deviceId) next.set("device", deviceId);
    if (assayId) next.set("assay", assayId);
    next.set("fields", fields.join(","));
    setSearchParams(next, { replace: true });
  }, [deviceId, assayId, fields, setSearchParams]);

  // Auto-fetch when filters change; Refresh remains an immediate override.
  useEffect(() => {
    const handle = window.setTimeout(() => {
      void refresh();
    }, 300);
    return () => window.clearTimeout(handle);
    // refresh closes over current filter values; deps intentionally match ticket scope
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId, assayId, fields]);

  const points = (timeseries?.points as Array<Record<string, unknown>>) || [];
  const compareRows = (compare?.rows as Array<Record<string, unknown>>) || [];
  const statusRows = (statusDist?.rows as Array<Record<string, unknown>>) || [];
  const qualitySummary = (quality?.summary as Record<string, number>) || {};
  const cells = (heatmap?.cells as Array<Record<string, unknown>>) || [];

  const chartPoints = points.map((p) => ({
    ...p,
    demo_attention_threshold: 72,
  }));

  return (
    <ErrorBoundary title="Dashboards page error">
      <div className="space-y-6">
        <section className="rounded-2xl border border-line bg-card p-5 shadow-card">
          <h2 className="text-xl font-semibold">Historical dashboards</h2>
          <p className="mt-1 text-sm text-muted">
            Charts render from mapped Postgres telemetry. Demo thresholds are illustrative only.
          </p>
          <div className="mt-4 flex flex-wrap gap-3 items-end">
            <label className="text-sm">
              <span className="mb-1 block text-xs text-muted">Device</span>
              <select
                className="rounded-xl border border-line bg-canvas px-3 py-2"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
              >
                <option value="">All devices</option>
                {(filters?.device_ids || []).map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-xs text-muted">Assay run</span>
              <select
                className="rounded-xl border border-line bg-canvas px-3 py-2"
                value={assayId}
                onChange={(e) => setAssayId(e.target.value)}
              >
                <option value="">All assay runs</option>
                {(filters?.assay_run_ids || []).map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <div className="text-sm">
              <span className="mb-1 block text-xs text-muted">Metrics</span>
              <div className="flex flex-wrap gap-2">
                {(filters?.metrics || fields).map((m) => (
                  <label key={m} className="flex items-center gap-1 text-xs">
                    <input
                      type="checkbox"
                      checked={fields.includes(m)}
                      onChange={(e) => {
                        setFields((prev) =>
                          e.target.checked ? [...prev, m] : prev.filter((x) => x !== m)
                        );
                      }}
                    />
                    {m}
                  </label>
                ))}
              </div>
            </div>
            <button
              type="button"
              onClick={() => void refresh()}
              className="rounded-xl bg-accent px-3 py-2 text-sm font-medium text-white"
            >
              Refresh charts
            </button>
          </div>
          <div className="mt-3 rounded-xl bg-accentSoft px-3 py-2 text-xs text-accent">
            Active filters — device: {deviceId || "all"} · assay: {assayId || "all"} · fields:{" "}
            {fields.join(", ")}
          </div>
        </section>

        <div className="grid gap-4 xl:grid-cols-2">
          <Card title="Telemetry time series">
            {chartPoints.length === 0 ? (
              <Empty />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartPoints}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e6e5e0" />
                  <XAxis dataKey="elapsed_seconds" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  {fields.map((f, i) => (
                    <Line
                      key={f}
                      type="monotone"
                      dataKey={f}
                      stroke={["#1d6b5c", "#1d4ed8", "#b45309", "#0f766e", "#6b7280"][i % 5]}
                      dot={false}
                      strokeWidth={1.8}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>

          <Card title="Device / assay comparison (activity index)">
            {compareRows.length === 0 ? (
              <Empty />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={compareRows.slice(0, 12)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e6e5e0" />
                  <XAxis dataKey="device_id" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="avg_value" fill="#1d6b5c" name="Avg activity" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Card>

          <Card title="Activity index with demo thresholds">
            {chartPoints.length === 0 ? (
              <Empty />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartPoints}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e6e5e0" />
                  <XAxis dataKey="elapsed_seconds" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="activity_index"
                    stroke="#1d6b5c"
                    dot={false}
                    strokeWidth={1.8}
                  />
                  <Line
                    type="monotone"
                    dataKey="demo_attention_threshold"
                    stroke="#b45309"
                    strokeDasharray="4 4"
                    name="Demo attention threshold"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
            <p className="mt-2 text-xs text-muted">
              Dashed line is a demo attention threshold (72), not a validated assay cutoff.
            </p>
          </Card>

          <Card title="Status distribution">
            {statusRows.length === 0 ? (
              <Empty />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={statusRows}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e6e5e0" />
                  <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="n" fill="#1d4ed8" name="Readings" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Card>

          <Card title="Data quality summary">
            {Object.keys(qualitySummary).length === 0 ? (
              <Empty />
            ) : (
              <div className="grid grid-cols-2 gap-3 text-sm">
                {Object.entries(qualitySummary).map(([k, v]) => (
                  <div key={k} className="rounded-xl bg-canvas px-3 py-2">
                    <div className="text-[10px] text-muted">{formatQualityKey(k)}</div>
                    <div className="font-semibold">{v}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Well × activity heatmap">
            {cells.length === 0 ? <Empty /> : <WellActivityHeatmap cells={cells} />}
          </Card>
        </div>
      </div>
    </ErrorBoundary>
  );
}

function WellActivityHeatmap({ cells }: { cells: Array<Record<string, unknown>> }) {
  const byId = new Map(cells.map((c) => [String(c.well_id), c]));
  let maxIndex = 0;
  for (const id of byId.keys()) {
    const row = id.charCodeAt(0) - 65;
    const col = Number.parseInt(id.slice(1), 10) - 1;
    if (Number.isFinite(row) && Number.isFinite(col) && row >= 0 && col >= 0) {
      maxIndex = Math.max(maxIndex, row * HEATMAP_COLS + col);
    }
  }
  const wellCount = Math.max(maxIndex + 1, cells.length, 24);
  const rowCount = Math.ceil(wellCount / HEATMAP_COLS);

  return (
    <div
      className="grid gap-2"
      style={{ gridTemplateColumns: `auto repeat(${HEATMAP_COLS}, minmax(0, 1fr))` }}
    >
      <div />
      {Array.from({ length: HEATMAP_COLS }, (_, col) => (
        <div key={`col-${col}`} className="text-center text-[10px] font-medium text-muted">
          {col + 1}
        </div>
      ))}
      {Array.from({ length: rowCount }, (_, row) => {
        const rowLetter = String.fromCharCode(65 + row);
        return (
          <div key={`row-${rowLetter}`} className="contents">
            <div className="flex items-center pr-1 text-[10px] font-medium text-muted">{rowLetter}</div>
            {Array.from({ length: HEATMAP_COLS }, (_, col) => {
              const wellId = `${rowLetter}${col + 1}`;
              const cell = byId.get(wellId);
              const act = Number(cell?.avg_activity || 0);
              const intensity = Math.min(1, act / 100);
              return (
                <div
                  key={wellId}
                  className="rounded-xl p-3 text-center text-xs text-ink"
                  style={{
                    background: `rgba(29,107,92,${0.12 + intensity * 0.45})`,
                  }}
                  title={`Activity ${act.toFixed(1)}`}
                  aria-label={`Well ${wellId}, activity ${act.toFixed(1)}`}
                >
                  <div className="font-mono">{wellId}</div>
                  <div>{cell ? act.toFixed(0) : "—"}</div>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-line bg-card p-5 shadow-card">
      <h3 className="mb-3 font-semibold">{title}</h3>
      {children}
    </section>
  );
}

function Empty() {
  return (
    <div className="flex h-[220px] items-center justify-center rounded-xl border border-dashed border-line text-sm text-muted">
      No loaded telemetry yet — run ETL first.
    </div>
  );
}
