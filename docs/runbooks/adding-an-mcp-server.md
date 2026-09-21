# Adding an MCP server

**Prerequisites:** ADR if the server can execute code or reach the network. Allowlist entry. Human review.

**Effects:** Would expose tools to the harness. Default is **deny**.

**Steps:**
1. Write or update an ADR.
2. Add an object to `platform/mcp/allowlist.json` (`id`, purpose, network).
3. Wire tools through `policy.json`. Store credentials in Keychain / gitignored env (ADR 0027), not Git.
4. Do not enable a server that wraps the Docker socket.

**Verify:** `assert_allowed("<id>")` succeeds in tests; unknown ids still raise `McpDenied`.

**Rollback:** Remove the allowlist row; rotate any token it used.
