import { useEffect, useState } from "react";
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

export function DashboardsPage({ showToast }: { showToast: (msg: string) => void }) {
  const [filters, setFilters] = useState<{
    device_ids: string[];
    assay_run_ids: string[];
    test_names: string[];
    metrics: string[];
  } | null>(null);
  const [deviceId, setDeviceId] = useState("");
  const [assayId, setAssayId] = useState("");
  const [fields, setFields] = useState<string[]>(["temperature_c", "optical_density", "activity_index"]);
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

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
              onClick={refresh}
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
                    <div className="text-[10px] uppercase text-muted">{k}</div>
                    <div className="font-semibold">{v}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Well × activity heatmap">
            {cells.length === 0 ? (
              <Empty />
            ) : (
              <div className="grid grid-cols-4 gap-2">
                {cells.map((c) => {
                  const act = Number(c.avg_activity || 0);
                  const intensity = Math.min(1, act / 100);
                  return (
                    <div
                      key={String(c.well_id)}
                      className="rounded-xl p-3 text-center text-xs text-white"
                      style={{
                        background: `rgba(29,107,92,${0.25 + intensity * 0.75})`,
                      }}
                      title={`Activity ${act.toFixed(1)}`}
                    >
                      <div className="font-mono">{String(c.well_id)}</div>
                      <div>{act.toFixed(0)}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      </div>
    </ErrorBoundary>
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