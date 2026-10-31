# ADR 0004 — Content-Addressed Storage for Artifacts, Datasets, and Checkpoints

- **Status:** Accepted (WO-00)
- **Date:** 2026-10-30
- **Context:** `ai-lab/coding-training/`
- **Related:** `docs/decisions/0003-secrets-and-artifacts-stay-out-of-git.md`, `0014-postgres-qdrant-redis.md`

## Context

The platform generates large volumes of candidate code files, execution stdout/stderr logs, dataset test bundles, and adapter checkpoint weights. Storing raw binary or multiline blobs directly in PostgreSQL degrades relational query performance and bloats database dumps. Storing them in Git violates AI Lab rules (`AGENTS.md`).

## Decision

1. **Content-Addressed Local Artifact Store:**
   - Store all payloads, test bundles, execution artifacts, and adapter checkpoints in a structured content-addressed local filesystem hierarchy:
     ```text
     runs/{run_id}/
       manifest.json
       generations.jsonl
       executions.jsonl
       rewards.jsonl
       evaluations.json
       checkpoints/{checkpoint_id}/
     artifacts/{sha256_prefix}/{sha256_hash}.blob
     ```
   - On `mac-mini`, this is hosted at `~/.ai-lab/training-artifacts/` or a dedicated data volume.
   - On `mac-studio`, checkpoint adapters are persisted to `~/.ai-lab/models/adapters/` (under `AI_LAB_MODEL_ROOT`).

2. **Database Holds Immutable References and Hashes:**
   - PostgreSQL stores metadata, job records, and SHA-256 hashes (`manifest_hash`, `code_hash`, `bundle_hash`, `adapter_hash`).
   - Every file write is atomic (written to a temporary file and atomically moved) and immutable. Existing content-addressed files are never overwritten.

3. **Verifiable Test Bundles:**
   - Each task references a test bundle identified strictly by its SHA-256 digest (`test_bundle_sha256`).
   - The Sandbox Worker verifies the bundle's cryptographic digest before unpacking and execution. If the digest mismatches, the job is aborted as an infrastructure error.

## Consequences

- Database backups remain lean and fast.
- Checkpoints and artifacts are easily archived, synced, or purged by age without corrupting relational foreign keys.
- Complete auditability and provenance from dataset prompt to final model weights.
