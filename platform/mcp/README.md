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

```json
{
  "mcpServers": {
    "ai-lab": {
      "command": "/ABS/PATH/ai-lab/scripts/lab-mcp-server.sh",
      "env": {
        "AI_LAB_API_BASE": "http://mac-mini:8088",
        "AI_LAB_API_TOKEN": "(paste locally)"
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
