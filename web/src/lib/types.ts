export type RunStatus =
  | "pending"
  | "running"
  | "paused"
  | "stopped"
  | "complete"
  | "attention"
  | "interrupted"
  | "cleared";

export interface WellState {
  well_id: string;
  optical_density: number;
  fluorescence_rfu: number;
  activity_index: number;
}

export interface TelemetryReading {
  event_timestamp: string;
  test_name: string;
  device_name: string;
  device_id: string;
  rack_id: string;
  well_id: string;
  assay_run_id: string;
  sample_id: string;
  compound_code: string;
  elapsed_seconds: number;
  temperature_c: number | null;
  ph: number | null;
  optical_density: number | null;
  fluorescence_rfu: number | null;
  dissolved_oxygen_pct: number | null;
  reagent_concentration_mg_l: number | null;
  activity_index: number | null;
  status: string;
  quality_flag: string;
  wells?: WellState[];
}

export interface Run {
  id: string;
  test_name: string;
  device_id: string;
  device_name: string;
  rack_id: string;
  assay_run_id: string;
  compound_code: string;
  well_count: number;
  status: RunStatus | string;
  seed: number;
  tick_index: number;
  row_count: number;
  file_count: number;
  started_at?: string | null;
  paused_at?: string | null;
  completed_at?: string | null;
  last_reading_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  elapsed_seconds?: number;
  latest?: TelemetryReading | null;
  wells?: WellState[] | null;
  sparkline?: number[] | null;
}

export interface SourceFile {
  id: string;
  filename: string;
  filepath?: string;
  sha256?: string;
  size_bytes?: number;
  row_count?: number;
  test_name?: string | null;
  device_id?: string | null;
  assay_run_id?: string | null;
  ingestion_status: string;
  modified_at?: string;
  error?: string;
}

export interface EtlJob {
  id: string;
  job_type: string;
  status: string;
  total_rows: number;
  processed_rows: number;
  inserted_rows: number;
  skipped_rows: number;
  rejected_rows: number;
  warning_rows: number;
  quarantined_rows: number;
  current_file?: string | null;
  current_phase?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  result?: Record<string, unknown> | null;
  created_at: string;
  progress_pct?: number;
  estimated_remaining_seconds?: number | null;
}

export type ConnectionState = "live" | "reconnecting" | "offline";