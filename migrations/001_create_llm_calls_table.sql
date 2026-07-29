-- Adapt this into an Alembic migration inside whichever host project you're
-- wiring up first (Activity Tracker, Bill Splitter, or AI Chief of Staff).
-- This package does not run migrations itself — each project owns its own DB.

CREATE TABLE IF NOT EXISTS llm_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    project VARCHAR NOT NULL,
    feature VARCHAR NOT NULL,

    provider VARCHAR NOT NULL,
    model VARCHAR,

    prompt_name VARCHAR,
    prompt_version VARCHAR,

    prompt_text TEXT,
    response_text TEXT,

    latency_ms INTEGER NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost_usd FLOAT,

    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    guardrail_flagged BOOLEAN NOT NULL DEFAULT FALSE,

    extra_metadata JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_project_feature ON llm_calls (project, feature);
CREATE INDEX IF NOT EXISTS idx_llm_calls_created_at ON llm_calls (created_at);
