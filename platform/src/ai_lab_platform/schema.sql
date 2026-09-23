-- Authoritative schema for production Postgres. Applied by PostgresStore._init.
CREATE TABLE IF NOT EXISTS work_orders (
    id UUID PRIMARY KEY,
    objective TEXT NOT NULL,
    agent TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS work_orders_status_idx ON work_orders (status);

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    work_order_id UUID REFERENCES work_orders (id),
    at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor TEXT NOT NULL,
    event TEXT NOT NULL,
    detail JSONB NOT NULL DEFAULT '{}'
);

-- FEAT-010 / IWO-002: conversations and agent runs (not Implementation WOs).
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    agent TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS conversation_messages_conv_idx
    ON conversation_messages (conversation_id, created_at);

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations (id) ON DELETE SET NULL,
    work_order_id UUID,
    agent TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS agent_runs_status_idx ON agent_runs (status);
CREATE INDEX IF NOT EXISTS agent_runs_conversation_idx ON agent_runs (conversation_id);
