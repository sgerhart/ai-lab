# Redis

Queue and cache only (ADR 0014). Persistence is off in compose (`--save ""`, AOF no) so a Redis restart cannot be mistaken for durable work-order recovery.

Password is required via `REDIS_PASSWORD`.
