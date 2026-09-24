# IWO-046 — Scan lab MCP before Cursor trust (FEAT-014)

**Status:** Done (accepted risk)  
**Priority:** P2  
**Effort:** S  
**Owner:** human (operator)  
**Feature:** [FEAT-014](../features/FEAT-014-defenseclaw-operator-governance.md)  

## Outcome

DefenseClaw default scan **blocked** for `scripts/lab-mcp-server.sh` (launcher
not in npx/uvx allowlist). Finding [F-014](../security/findings/F-014-defenseclaw-local-mcp-scan-skip.md).
Manual `lab_health` smoke passed; Cursor entry added with `--skip-scan` under
IWO-054.
