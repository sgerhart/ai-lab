# Troubleshooting

1. Is this a **repo** problem or a **host** problem? Run `./scripts/preflight.sh` first.
2. Compose not started is the expected state until authorization. `connection refused` on 5432 is not a bug.
3. Tailscale: `tailscale status` on each host (when installed). Short names: `mac-mini`, `mac-studio`, `mac-air`. Tailnet suffix is not in Git.
4. Studio jobs stuck `queued`: expected if the Studio is off (ADR 0009).
5. Failed agent job: [../runbooks/troubleshooting-failed-agent-job.md](../runbooks/troubleshooting-failed-agent-job.md).
6. Do not restart Postgres with `compose down -v` unless you intend to destroy the volume.
