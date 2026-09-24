# F-015 — Studio SSH authentication failure

- **Date:** 2026-09-24
- **Hosts:** Air → `mac-studio`, mini → `mac-studio`
- **Severity:** Medium (blocks host shell; Ollama/Jupyter still reachable)
- **Status:** Open

## Summary

`ssh sgerhart@mac-studio` returns `Permission denied (publickey,password,keyboard-interactive)`
from both `mac-air` and `mac-mini`, while TCP/22 is open on Tailscale.

Studio services still answer:

- Ollama `http://mac-studio:11434` (`llama3.2:3b`)
- Jupyter `http://mac-studio:8888` (token on mini `~/.ai-lab/studio-jupyter.token`)

## Impact

Cannot run `ollama pull`, brew, or LaunchAgent changes via SSH until keys are
fixed on Studio. FEAT-015 / IWO-047 uses Jupyter exec as a temporary operator
path for preflight and gated downloads.

## Mitigation / next

1. On Studio console: ensure `~/.ssh/authorized_keys` includes the operator
   key used from Air (and optionally mini).
2. Prefer Jupyter-mediated installs only for explicit IWOs; restore SSH ASAP.
3. Do not weaken SSH to password auth over the tailnet.

## Related

IWO-047, FEAT-015, hosts/studio/RUNBOOK.md
