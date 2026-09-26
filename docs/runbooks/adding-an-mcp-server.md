# Adding an MCP server

**Prerequisites:** ADR if the server can execute code or reach the network. Allowlist entry. Human review.

**Effects:** Would expose tools to the harness. Default is **deny**.

**Steps:**
1. Submit an intake. `origin` is `lab` for `ai-lab`, `third-party` for someone else's stdio server, or `draft` for a server a coding agent wrote in an isolated worktree.
2. The record stores an id, a stdio command, declared capabilities, a network class (`none`, `loopback`, `tailnet-client`, or `public-https`), and a credential name. The secret stays in the Keychain or a gitignored env file. `GET /v1/mcp/intake` lists `virustotal` and `cve-lookup` as unlisted candidates. Their first bindings are hash, domain, and IP reports, and NVD, OSV, and CISA KEV lookups. URL submission, corpus search, exploit search, Shodan IP lookup, Nuclei, and Metasploit checks are not in those bindings.
3. The server stays denied until `POST /v1/mcp/servers/{id}/authorize`.
4. Bind an agent to the declared tools with `PUT /v1/mcp/servers/{id}/bindings`. A privileged or network capability still waits for approval on the run.
5. Do not submit a server that wraps the Docker socket. MCP servers are host stdio processes, not containers.

**Verify:** `assert_allowed("<id>")` succeeds in tests; unknown ids still raise `McpDenied`.

**Rollback:** Remove the allowlist row; rotate any token it used.
