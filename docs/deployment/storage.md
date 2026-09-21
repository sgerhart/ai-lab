# Storage layout

Git holds instructions. Large data lives on hosts.

| Kind | Default location (placeholders) | Git? |
|------|---------------------------------|------|
| Model weights / Ollama blobs | `{{STUDIO_MODEL_ROOT}}` default `$HOME/.ollama/models` | No |
| MLX / HF caches | `{{STUDIO_MODEL_ROOT}}/hf` | No |
| Training data | `{{STUDIO_MODEL_ROOT}}/datasets` | No |
| Checkpoints | `{{STUDIO_MODEL_ROOT}}/checkpoints` | No |
| Experiment outputs | `{{STUDIO_MODEL_ROOT}}/experiments` | No |
| Postgres/Qdrant/Redis volumes | Docker volumes on **M1** | No |
| Agent artifacts | Postgres metadata + files under `{{M1_ARTIFACT_ROOT}}` | No |
| Logs | host paths / compose logs | No |
| Backups | iCloud Drive `…/CloudDocs/ai-lab-backups` (ADR 0030) | No |

`AI_LAB_MODEL_ROOT` is the Studio override for a future Thunderbolt NVMe (ADR 0033; not initial setup).

The Studio internal 1 TB SSD is the initial store. Do not fill it with untracked copies of product databases.
