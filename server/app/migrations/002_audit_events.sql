-- Append-only demo record of who, what, when, and why.
-- Illustrative evidence shape for a process you validate elsewhere.

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_audit_events_recorded_at ON audit_events (recorded_at DESC);

CREATE RULE audit_events_no_update AS ON UPDATE TO audit_events DO INSTEAD NOTHING;

CREATE RULE audit_events_no_delete AS ON DELETE TO audit_events DO INSTEAD NOTHING;
