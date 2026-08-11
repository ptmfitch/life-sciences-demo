from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

RunStatus = Literal[
    "pending",
    "running",
    "paused",
    "stopped",
    "complete",
    "attention",
    "interrupted",
]

BulkAction = Literal[
    "start_all",
    "pause_all",
    "stop_all",
    "clear_completed",
    "clear_all",
]


class CreateRunRequest(BaseModel):
    test_name: str | None = None
    quantity: int = Field(default=1, ge=1, le=20)
    device_id: str | None = None
    rack_id: str | None = None
    assay_run_id: str | None = None
    compound_code: str | None = None
    well_count: int = Field(default=24, ge=4, le=96)
    seed: int | None = None


class RunOut(BaseModel):
    id: UUID
    test_name: str
    device_id: str
    device_name: str
    rack_id: str
    assay_run_id: str
    compound_code: str
    well_count: int
    status: str
    seed: int
    tick_index: int
    row_count: int
    file_count: int
    started_at: datetime | None = None
    paused_at: datetime | None = None
    completed_at: datetime | None = None
    last_reading_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    elapsed_seconds: int = 0
    latest: dict[str, Any] | None = None
    wells: list[dict[str, Any]] | None = None
    sparkline: list[float] | None = None


class BulkRequest(BaseModel):
    action: BulkAction


class TelemetryReading(BaseModel):
    event_timestamp: str
    test_name: str
    device_name: str
    device_id: str
    rack_id: str
    well_id: str
    assay_run_id: str
    sample_id: str
    compound_code: str
    elapsed_seconds: int
    temperature_c: float | None
    ph: float | None
    optical_density: float | None
    fluorescence_rfu: float | None
    dissolved_oxygen_pct: float | None
    reagent_concentration_mg_l: float | None
    activity_index: float | None
    status: str
    quality_flag: str
    wells: list[dict[str, Any]] | None = None


class FieldMappingCreate(BaseModel):
    name: str
    mapping: dict[str, Any]


class FieldMappingOut(BaseModel):
    id: UUID
    name: str
    mapping: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EtlScanOut(BaseModel):
    directory: str
    file_count: int
    total_rows: int
    newest_file_timestamp: datetime | None
    files: list[dict[str, Any]]


class EtlJobRequest(BaseModel):
    file_ids: list[UUID]
    mapping_id: UUID | None = None
    mapping: dict[str, Any] | None = None


class EtlJobOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    total_rows: int
    processed_rows: int
    inserted_rows: int
    skipped_rows: int
    rejected_rows: int
    warning_rows: int
    quarantined_rows: int
    current_file: str | None = None
    current_phase: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None
    created_at: datetime
    progress_pct: float = 0.0
    estimated_remaining_seconds: float | None = None


class DashQuery(BaseModel):
    fields: list[str] = Field(default_factory=lambda: ["temperature_c", "optical_density"])
    device_ids: list[str] | None = None
    assay_run_ids: list[str] | None = None
    test_names: list[str] | None = None
    limit: int = Field(default=2000, ge=10, le=20000)