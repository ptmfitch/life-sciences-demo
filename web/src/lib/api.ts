const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  listRuns: () => request<import("./types").Run[]>("/runs"),
  createRuns: (body: {
    test_name?: string;
    quantity?: number;
    well_count?: number;
  }) =>
    request<import("./types").Run[]>("/runs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  start: (id: string) => request(`/runs/${id}/start`, { method: "POST" }),
  pause: (id: string) => request(`/runs/${id}/pause`, { method: "POST" }),
  resume: (id: string) => request(`/runs/${id}/resume`, { method: "POST" }),
  stop: (id: string) => request(`/runs/${id}/stop`, { method: "POST" }),
  restart: (id: string) => request(`/runs/${id}/restart`, { method: "POST" }),
  clear: (id: string) => request(`/runs/${id}`, { method: "DELETE" }),
  bulk: (action: string) =>
    request("/runs/bulk", {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  scan: () => request<{
    directory: string;
    file_count: number;
    total_rows: number;
    newest_file_timestamp: string | null;
    files: import("./types").SourceFile[];
  }>("/etl/scan", { method: "POST" }),
  inspect: (id: string) => request<Record<string, unknown>>(`/etl/files/${id}/inspect`),
  defaultMapping: () => request<Record<string, unknown>>("/etl/mappings/default"),
  saveMapping: (name: string, mapping: Record<string, unknown>) =>
    request("/etl/mappings", {
      method: "POST",
      body: JSON.stringify({ name, mapping }),
    }),
  dryRun: (file_ids: string[], mapping: Record<string, unknown>) =>
    request<import("./types").EtlJob>("/etl/dry-run", {
      method: "POST",
      body: JSON.stringify({ file_ids, mapping }),
    }),
  load: (file_ids: string[], mapping: Record<string, unknown>) =>
    request<import("./types").EtlJob>("/etl/load", {
      method: "POST",
      body: JSON.stringify({ file_ids, mapping }),
    }),
  getJob: (id: string) => request<import("./types").EtlJob>(`/etl/jobs/${id}`),
  cancelJob: (id: string) =>
    request<import("./types").EtlJob>(`/etl/jobs/${id}/cancel`, { method: "POST" }),
  dashFilters: () =>
    request<{
      device_ids: string[];
      assay_run_ids: string[];
      test_names: string[];
      metrics: string[];
    }>("/dash/filters"),
  timeseries: (params: URLSearchParams) =>
    request<Record<string, unknown>>(`/dash/timeseries?${params}`),
  compare: (field: string) =>
    request<Record<string, unknown>>(`/dash/compare?field=${encodeURIComponent(field)}`),
  statusDistribution: () => request<Record<string, unknown>>("/dash/status-distribution"),
  quality: () => request<Record<string, unknown>>("/dash/quality"),
  wellHeatmap: (assay_run_id?: string) =>
    request<Record<string, unknown>>(
      `/dash/well-heatmap${assay_run_id ? `?assay_run_id=${encodeURIComponent(assay_run_id)}` : ""}`
    ),
};