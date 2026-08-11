-- Initial schema for AstraLume BioTest synthetic demo

CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY,
    test_name TEXT NOT NULL,
    device_id TEXT NOT NULL,
    device_name TEXT NOT NULL DEFAULT 'AstraLume BioTest Station',
    rack_id TEXT NOT NULL,
    assay_run_id TEXT NOT NULL,
    compound_code TEXT NOT NULL,
    well_count INTEGER NOT NULL DEFAULT 24,
    status TEXT NOT NULL DEFAULT 'pending',
    seed INTEGER NOT NULL DEFAULT 0,
    tick_index INTEGER NOT NULL DEFAULT 0,
    row_count INTEGER NOT NULL DEFAULT 0,
    file_count INTEGER NOT NULL DEFAULT 0,
    output_dir TEXT,
    started_at TIMESTAMPTZ,
    paused_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_reading_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs (status);
CREATE INDEX IF NOT EXISTS idx_test_runs_device_id ON test_runs (device_id);

CREATE TABLE IF NOT EXISTS source_files (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    filepath TEXT NOT NULL,
    sha256 TEXT,
    size_bytes BIGINT,
    row_count INTEGER,
    test_name TEXT,
    device_id TEXT,
    assay_run_id TEXT,
    ingestion_status TEXT NOT NULL DEFAULT 'pending',
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ingested_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_source_files_status ON source_files (ingestion_status);

CREATE TABLE IF NOT EXISTS raw_readings (
    id BIGSERIAL PRIMARY KEY,
    source_file_id UUID NOT NULL REFERENCES source_files (id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_file_id, row_number)
);

CREATE TABLE IF NOT EXISTS telemetry_readings (
    id BIGSERIAL PRIMARY KEY,
    source_file_id UUID REFERENCES source_files (id) ON DELETE SET NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    test_name TEXT NOT NULL,
    device_name TEXT NOT NULL,
    device_id TEXT NOT NULL,
    rack_id TEXT NOT NULL,
    well_id TEXT NOT NULL,
    assay_run_id TEXT NOT NULL,
    sample_id TEXT NOT NULL,
    compound_code TEXT NOT NULL,
    elapsed_seconds INTEGER NOT NULL,
    temperature_c DOUBLE PRECISION,
    ph DOUBLE PRECISION,
    optical_density DOUBLE PRECISION,
    fluorescence_rfu DOUBLE PRECISION,
    dissolved_oxygen_pct DOUBLE PRECISION,
    reagent_concentration_mg_l DOUBLE PRECISION,
    activity_index DOUBLE PRECISION,
    status TEXT,
    quality_flag TEXT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (device_id, assay_run_id, event_timestamp, well_id)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_event_ts ON telemetry_readings (event_timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_device ON telemetry_readings (device_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_assay ON telemetry_readings (assay_run_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_test_name ON telemetry_readings (test_name);
CREATE INDEX IF NOT EXISTS idx_telemetry_status ON telemetry_readings (status);

CREATE TABLE IF NOT EXISTS field_mappings (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    mapping JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS etl_jobs (
    id UUID PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    mapping_id UUID REFERENCES field_mappings (id) ON DELETE SET NULL,
    file_ids JSONB NOT NULL DEFAULT '[]',
    total_rows INTEGER NOT NULL DEFAULT 0,
    processed_rows INTEGER NOT NULL DEFAULT 0,
    inserted_rows INTEGER NOT NULL DEFAULT 0,
    skipped_rows INTEGER NOT NULL DEFAULT 0,
    rejected_rows INTEGER NOT NULL DEFAULT 0,
    warning_rows INTEGER NOT NULL DEFAULT 0,
    quarantined_rows INTEGER NOT NULL DEFAULT 0,
    current_file TEXT,
    current_phase TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);