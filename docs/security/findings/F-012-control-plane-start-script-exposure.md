# Finding F-012 — Control-plane start script dumped in operator chat

- **Date:** 2026-09-23
- **Severity:** Medium
- **Host:** mac-mini (`~/.ai-lab/start-control-plane.sh`)

## What happened

While diagnosing the lab-site deploy, an agent session printed the mini
control-plane start script. That file includes live `DATABASE_URL` and
`AI_LAB_API_TOKEN` values. Values are **not** repeated here.

## Action required

1. From Air: `./scripts/rotate-control-plane-secrets.sh` (dry-run), then
   `./scripts/rotate-control-plane-secrets.sh --apply` when authorized.
2. On the mini, read the new token from `~/.ai-lab/api-token.rotated` (mode 600);
   paste into Air Studio / browser session storage. Do not commit that file.
3. Prefer `launchctl print` / targeted `grep -c` over `cat` of start scripts in
   future diagnostics.

## Status

Open until the operator confirms `--apply` rotation succeeded. Script landed
2026-09-24; auth also tightened so Tailnet peers must still send Bearer
(see F-013).
