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
