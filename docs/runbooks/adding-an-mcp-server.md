# Adding an MCP server

**Prerequisites:** Explicit tool permission design. Not implemented in platform/mcp yet.

**Effects:** Would expose tools to the harness. Treat as a security change.

**Steps:** Write an ADR if the server can execute code or reach the network. Allowlist tools. Store credentials in the secret store, not Git. Do not enable a server that wraps the Docker socket.

**Verify:** Policy lists the server; default deny.

**Rollback:** Remove from allowlist; rotate any token it used.
