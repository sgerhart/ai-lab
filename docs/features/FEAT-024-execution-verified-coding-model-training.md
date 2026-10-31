# FEAT-024 — Execution-Verified Coding Model Training Platform

- **Status:** In progress (WO-00 Delivered)
- **Created:** 2026-10-30
- **Owner:** Steven Gerhart
- **GitHub issue:** draft only
- **Sub-platform path:** `coding-training/`

## Purpose

Build an operational, observable, and reproducible coding model training and evaluation platform that prompts local small coder models, executes candidate code in an air-gapped Linux VM sandbox on Proxmox against immutable test suites, scores deterministic rewards, curates verified SFT datasets, and trains LoRA/QLoRA adapters and conditional execution-reward RL on Apple Silicon.

## User workflow

1. Operator configures or selects an experiment run in the controller.
2. Controller prompts a local base model (e.g. `Qwen3-0.6B`) to generate candidate implementations for curated Python programming tasks.
3. Controller dispatches candidate code and test bundles to an isolated Linux sandbox worker on Proxmox.
4. Sandbox worker executes code inside a disposable rootless jail (no network, cgroups CPU/memory bounds) against trusted test bundles.
5. Reward service scores candidate results deterministically into PostgreSQL.
6. Passing candidates are mined into verified instruction-tuning datasets.
7. With explicit human approval, SFT or RL LoRA training runs on the Mac Studio using MLX-LM, saving immutable checkpoints and evaluating on holdout tasks.

## Target host(s)

| Role | Host alias | Why |
|------|------------|-----|
| Control plane & DB | `mac-mini` | FastAPI controller, Postgres state, reward scoring, artifact store |
| Model compute | `mac-studio` | Local model generation and MLX-LM LoRA training |
| Operator client | `mac-air` | Cursor / Antigravity IDE, operator dashboard, approvals |
| Sandbox worker | `proxmox-vm` | Isolated Linux VM with host-only bridge for safe code execution |

## Dependencies

- Features: `FEAT-003` (Studio worker), `FEAT-016` (Local coding models), `FEAT-019` (Security Compute Plane)
- ADRs: ADR 0010, ADR 0014, ADR 0017, ADR 0043; `coding-training/docs/adr/0001`–`0005`
- Hosts / services: `mac-mini` (Postgres, Redis), `mac-studio` (MLX), Proxmox (Linux VM)

## Proposed deliverables

- Sub-platform in `coding-training/`
- Architecture document: `coding-training/docs/architecture.md`
- Foundational ADRs: `coding-training/docs/adr/`
- Phase gate records: `coding-training/docs/gates/`
- Typed contracts, services, trainers, and test suites
- Web Console: `coding-training/console/` (React/Vite/TS) with 6 core operational views

## Acceptance criteria

- [x] WO-00: Reconnaissance and ADRs delivered.
- [x] WO-01: Directory scaffold, pyproject, and test harness operational.
- [ ] WO-02: 100+ curated Python tasks with immutable test bundles and disjoint splits.
- [ ] WO-03: Sandbox worker passes 100% of negative security tests; operator approves execution.
- [ ] WO-04: Control plane with idempotent job leases and audit logs.
- [ ] WO-05: Reproducible holdout baseline report.
- [ ] WO-06: Verified SFT LoRA training on Studio with measured adapter weight changes.
- [ ] WO-07: RL backend compatibility spike on Apple Silicon.
- [ ] WO-08: Execution-reward RL training (conditional).
- [ ] WO-09: Complete operator runbooks and clean-start handover.
- [ ] WO-10: Web-based Coding Training Console (Dashboard, Playground, Experiments, Monitor, Models, Datasets) with SSE telemetry.
- [ ] Human approval gates enforced at every phase (no self-approval).

## Out of scope

- Direct execution of untrusted code on macOS workstations (`mac-air`, `mac-mini`, `mac-studio`).
- Training large foundation models from scratch (>3B parameters during pilot).
- Fabricated benchmarks or claiming reward score alone equals model training.
