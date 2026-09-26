# Roadmap

Deployment onto machines requires a separate human authorization. Repository files may exist earlier.

Status columns (do not collapse them):

| Column | Meaning |
|--------|---------|
| **Code** | Implemented and tested in Git (or N/A for docs-only) |
| **Deployed** | Running on the intended lab host after authorization |
| **Live verified** | Operator exercised the live path; evidence noted |
| **Future** | Tracked as a feature (`FEAT-*`), not a phase checkbox |

## Phases 0–7 (historical build)

| Phase | Deliverable | Code | Deployed | Live verified |
|-------|-------------|------|----------|---------------|
| 0 | Foundation, ADRs, validation | Yes | n/a | n/a |
| 1 | Host bootstrap, network docs, preflight | Yes | Partial (M1 apply; Studio no) | Air↔mini Tailscale/SSH |
| 2 | M1 compose, backup/restore scripts, health | Yes | Yes (compose on mini) | Healthchecks; iCloud dump written; **restore untested** |
| 3 | Studio tooling, model-serving config | Yes | No | No |
| 4 | Minimum harness (LangGraph + FastAPI + store) | Yes | Partial (API on mini) | Submit/health from Air; Studio dispatch fails closed |
| 5 | Dev / research / lab-ops agents | Deterministic plans yes | No Studio worker | Unit/laptop tests only |
| 6 | SLM training / eval | Catalog + FakeBackend dry-run | No | No pulls |
| 7 | Hardening, recovery testing | CI + throwaway restore | Backup script used once | Live M1 restore **untested** |

Evidence: [phases/repo-complete.md](phases/repo-complete.md), [`features/index.md`](features/index.md), [`features/PLAN-mini-first.md`](features/PLAN-mini-first.md).

## Mini-first personal-agent platform (current)

Core purpose: always-on personal agents + AI experimentation. Current capability table: [features/index.md](features/index.md).

| Slice | Work | Code | Deploy | Live |
|-------|------|------|--------|------|
| Harness | IWO-002–007, 020, 031 | Done | Mini `:8088` | Chat and tool loop |
| Studio UI | FEAT-004 / FEAT-013 / IWO-059 / IWO-063 | Chat-first shell at `/`. Sidebar label is Agent Studio | Mini `/` | Used. Agent Studio layout and lab-health pass still open (D-019) |
| Models | FEAT-003 / IWO-055 | Profiles in Git; catalog not marked pulled | Studio Ollama | Four tags installed 2026-09-25, including `qwen3.6:35b-a3b`. Role Save not recorded |
| Coding | FEAT-016 IWO-055/056/058 | Read + isolated patch/commit | HTML on mini | Unit only for the patch path |
| Coding eval / PR | IWO-057, FEAT-007 | Bench script done. PR path not started | Studio Ollama for the bench | 2026-09-25: three large tags each scored 4/4. Fixture did not drop the coding profile |
| Memory / schedule / IDE MCP | IWO-040–042, 052–054 | Done | Mini + Air | Live |
| Jupyter / Antares | FEAT-006 / FEAT-015 | Done for current UI and services | Studio | Live. Antares not set to survive reboot |
| Studio worker `:8090` | FEAT-003 optional | Scripts | No | No |

## Security platform and Security Compute

Direction only ([ADR 0043](decisions/0043-shared-antares-and-security-compute-plane.md), proposed). Nothing in this section is deployed. These documents do not authorize a hypervisor connection, VM changes, network changes, guest tools, or sample execution.

| Slice | Work | Code | Deploy | Live |
|-------|------|------|--------|------|
| AI Security Platform | [FEAT-018](features/FEAT-018-ai-security-platform.md), IWO-065–067 | Unit-tested | No | No |
| Security Center and Agent Studio posture | IWO-068–069 | Draft | No | No |
| Cybersecurity Vise | [FEAT-019](features/FEAT-019-cybersecurity-vise.md), IWO-070–071 unit, IWO-072–075 Draft | Unit-tested, not deployed | No | No |
| Security compute agent | [FEAT-020](features/FEAT-020-security-compute-agent.md), IWO-076–078 | Draft | No | No |

IWO-065, IWO-066, and IWO-067 are in Git and unit-tested. They are not deployed. Remaining order when a human accepts the drafts: IWO-070 and IWO-074 follow IWO-066. IWO-068 and IWO-076 follow IWO-067. IWO-069 follows IWO-066 and IWO-067. IWO-071, then IWO-072 and IWO-073, then IWO-077, then IWO-078. IWO-075 follows IWO-069, IWO-070, and IWO-074. Agent Studio posture (IWO-068) waits until that pass.

The hypervisor is the operator's empty Proxmox server (D-020: Intel i7, 64 GB). Still operator-supplied, and not invented here: management endpoint (D-021), isolated analysis network (D-022), quarantine storage (D-023), and template images (D-024). Lookup MCP stays on the trusted hosts ([mcp-servers.md](architecture/mcp-servers.md), IWO-080). Active tool MCP waits on an isolated guest (IWO-081). This roadmap does not connect to Proxmox.

## Next

Operator is deciding the Agent Studio layout (D-019). Do not treat the current canvas as final. Do not pull more models, enable paid APIs, or deploy hosts without a separate yes. Security platform code that is unit-tested (IWO-065–067, 070–071, 079–080) is not deployed. The remaining security IWOs stay Draft.

Still open: a harder coding bench, pull-request delivery (FEAT-007), the thin hardening notes on FEAT-016, and a browser pass of the Findings pane. Live M1 restore is still untested.
