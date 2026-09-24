# F-014 — DefenseClaw cannot scan local bash MCP launchers

- **Date:** 2026-09-24
- **Host:** Air (Cursor connector)
- **Severity:** Low (process limitation; not a secret leak)
- **Status:** Accepted risk (operator Continue for lab MCP wire-up)

## Summary

`defenseclaw mcp set ai-lab` refused the default scan:

> refusing to scan local MCP server 'ai-lab': command is not an allowlisted
> stdio launcher (allowed: npx, uvx)

The lab MCP entry is a repo script (`scripts/lab-mcp-server.sh`), not npx/uvx.
Operator added the server with `--skip-scan` after a manual stdio smoke
(`lab_health` → control plane `ok`).

## Mitigation

- No API token in `~/.cursor/mcp.json` (script reads `~/.ai-lab/mac-mini-api.token`).
- Tool surface remains the IWO-042 allowlist only.
- Revisit if DefenseClaw adds allowlist for trusted local paths.

## Related

IWO-046 / IWO-054, FEAT-005, FEAT-014.
