# studio — compute plane

Confirmed: Mac Studio, Apple M5 Max (18 CPU / 40 GPU), 64 GB, 1 TB.

**Does:** Ollama, MLX/uv projects, workers, JupyterLab in a venv.  
**Does not:** own Postgres data. **Does not** pull models in setup.

M5 compatibility is unverified in this workspace. Thunderbolt NVMe is future (ADR 0033); initial disk is the internal 1 TB SSD.

See [RUNBOOK.md](RUNBOOK.md) for the independently executable bring-up.

Clone path: `~/workspace/github/sgerhart/ai-lab` (ADR 0035).

```bash
./hosts/studio/setup.sh --preflight
./hosts/studio/setup.sh --dry-run
# ./hosts/studio/setup.sh --apply
```
