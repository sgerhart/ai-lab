# MCP

Two directions (do not conflate):

1. **Agents as MCP clients** (FEAT-013) — deny-unlisted allowlist:
   [`allowlist.json`](allowlist.json) plus operator
   `~/.ai-lab/mcp-servers.json`. Runtime: `mcp_client.py` / IWO-029.
2. **Lab as MCP server for IDEs** (FEAT-005 / IWO-042) — stdio server that
   proxies a small tool set to the control-plane HTTP API:

```bash
export AI_LAB_API_BASE=http://127.0.0.1:8088   # or http://mac-mini:8088
export AI_LAB_API_TOKEN=...                    # or rely on ~/.ai-lab/api.token
./scripts/lab-mcp-server.sh
```

Cursor (operator machine only — do not commit tokens):

Prefer DefenseClaw on Air:

```bash
defenseclaw mcp set ai-lab --connector cursor \
  --command "$PWD/scripts/lab-mcp-server.sh" \
  --env AI_LAB_API_BASE=http://mac-mini:8088
```

If scan refuses a local bash launcher (npx/uvx only), record a finding and use
`--skip-scan` only after a manual `lab_health` smoke (F-014 / IWO-046).

Example `~/.cursor/mcp.json` (no token — script reads `~/.ai-lab/api.token` or
`mac-mini-api.token`):

```json
{
  "mcpServers": {
    "ai-lab": {
      "command": "/ABS/PATH/ai-lab/scripts/lab-mcp-server.sh",
      "env": {
        "AI_LAB_API_BASE": "http://mac-mini:8088"
      }
    }
  }
}
```

Tools exposed: `lab_health`, `lab_memory_search`, `lab_memory_upsert`,
`lab_scheduler_status`.

Adding an *outbound* agent MCP server is a security change — see
[../../docs/runbooks/adding-an-mcp-server.md](../../docs/runbooks/adding-an-mcp-server.md)
if present.
