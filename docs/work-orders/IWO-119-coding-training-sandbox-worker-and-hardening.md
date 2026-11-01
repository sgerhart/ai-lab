# IWO-119 — Coding Training Sandbox Worker and Hardening

**Status:** Complete (WO-03 Delivered)  
**Priority:** P2  
**Effort:** M  
**Owner:** Steven Gerhart  
**Feature:** FEAT-024  
**Services / Areas:** `coding-training/services/sandbox_worker/`, `coding-training/tests/unit/`, docs

## Problem

Executing untrusted, model-generated Python code presents severe risks: infinite loops, memory denial of service, fork bombs, network exfiltration, or filesystem tampering. AGENTS.md strictly forbids executing untrusted code on macOS host workstations. WO-03 requires building a hardened, disposable sandbox execution worker with process/cgroup bounds, air-gapped egress (`deny_all`), an out-of-band test harness, cryptographic worker attestation, and passing 100% of negative security tests.

## Decision Context

- Implements isolated execution worker based on ADR 0002 (Linux VM sandbox) and ADR 0005 (air-gapped network security).
- Provides dual jail engines:
  - `BubblewrapJail` for Linux container/namespace isolation (`--unshare-all`, `--unshare-net`, `--cap-drop ALL`).
  - `SubprocessJail` for portable execution with session process groups (`os.setsid()`) and strict environment scrubbing.
- Defense-in-depth: Python runtime monkeypatch `block_network_access()` disables all socket creation inside the jail.
- Out-of-band test runner `harness.py` prevents hidden test disclosures.
- Safe dry-run defaults (`EXECUTION_ENABLED=false`) fail closed unless explicitly authorized.

## What To Build / Fix

1. Implement `services/sandbox_worker/harness.py`: Standalone in-jail test execution runner with network block and zero test secret disclosure.
2. Implement `services/sandbox_worker/jail.py`: `SubprocessJail` and `BubblewrapJail` with wall-clock timeout kills (`os.killpg`) and output truncation.
3. Implement `services/sandbox_worker/worker.py`: `SandboxWorker` implementing `SandboxBackend` with candidate SHA-256 verification, immutable bundle checks, strict failure categorization, and `WorkerAttestation`.
4. Implement `services/sandbox_worker/app.py`: FastAPI daemon exposing `/v1/execute`, `/v1/health`, `/v1/attest`.
5. Implement unit test suite `tests/unit/test_sandbox_worker.py` (7 tests).
6. Implement negative security test suite `tests/unit/test_negative_security.py` (6 adversarial tests: syntax error, infinite loop timeout, network denial, memory exhaustion, stdout bombing, filesystem isolation).
7. Document Gate WO-03 closeout record in `coding-training/docs/gates/WO-03.md`.

## Expected Change Surface

- Expected: `coding-training/services/sandbox_worker/`, `coding-training/tests/unit/test_sandbox_worker.py`, `coding-training/tests/unit/test_negative_security.py`, `coding-training/docs/gates/WO-03.md`, `docs/work-orders/IWO-119-coding-training-sandbox-worker-and-hardening.md`.
- Tests: `cd coding-training && make check`.
- Docs/status: `docs/features/index.md`, `docs/features/FEAT-024-execution-verified-coding-model-training.md`.

## Out Of Scope

- Direct execution of untrusted code on macOS workstations (`mac-air`, `mac-mini`, `mac-studio`).
- Production Proxmox VM deployment (deferred to operator host action).
- Training loop orchestration (deferred to WO-04).

## Do NOT Change

- Do not modify existing AI Lab core services (`platform/`, `infrastructure/`).
- Do not run untrusted code on macOS without jail containment.
- Do not enable `EXECUTION_ENABLED=true` by default.

## Closeout & Evidence

- Files created:
  - `coding-training/services/sandbox_worker/harness.py`
  - `coding-training/services/sandbox_worker/jail.py`
  - `coding-training/services/sandbox_worker/worker.py`
  - `coding-training/services/sandbox_worker/app.py`
  - `coding-training/tests/unit/test_sandbox_worker.py`
  - `coding-training/tests/unit/test_negative_security.py`
  - `coding-training/docs/gates/WO-03.md`
- Verification commands run:
  - `cd coding-training && make check` (37 passing unit tests, 0 lint errors)
  - Negative security suite: 100% passed (6/6 adversarial attack vectors contained)
