# Finding F-012 — Control-plane start script dumped in operator chat

- **Date:** 2026-09-23
- **Severity:** Medium
- **Host:** mac-mini (`~/.ai-lab/start-control-plane.sh`)

## What happened

While diagnosing the lab-site deploy, an agent session printed the mini
control-plane start script. That file includes live `DATABASE_URL` and
`AI_LAB_API_TOKEN` values. Values are **not** repeated here.

## Action required

1. Rotate `AI_LAB_API_TOKEN` on the mini; update LaunchAgent/start script;
   update any Air browser sessions.
2. Rotate Postgres password in compose env and update `DATABASE_URL` on the mini.
3. Prefer `launchctl print` / targeted `grep -c` over `cat` of start scripts in
   future diagnostics.

## Status

Open until rotation confirmed by operator.
