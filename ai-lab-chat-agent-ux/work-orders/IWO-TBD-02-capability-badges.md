# IWO-TBD-02 — MCP and built-in capability badges
**Status:** Proposed · **Depends on:** IWO-TBD-01

## Objective
Show what the assistant can actually use, including built-in, custom, and third-party MCP servers, with accurate health and permissions.

## Work
1. Inventory existing MCP server registry, stdio transport, built-in tools, allowlists and status endpoints; extend rather than duplicate.
2. Expose a sanitized capability DTO: stable ID, name, origin type, publisher if known, transport, execution host, connection state, last check, available tools, permitted tools, risk classification, enabled-for-conversation state.
3. Render compact badges in chat with accessible details panel and overflow handling.
4. Distinguish configured, connected, authorized, and used; mark stale health unknown.
5. Escape all untrusted labels/descriptions; redact credentials and sensitive URLs.

## Acceptance
- Built-in, custom MCP, and third-party MCP appear distinctly.
- Connected-but-not-authorized does not appear usable.
- Disconnected/stale servers do not show green.
- Details show mini vs remote execution accurately.
- Unknown or malicious metadata cannot inject markup; no secret leakage.
- Unit/API/UI tests cover unavailable and stale states.

## Out of scope / gates
No automatic server installation, MCP privilege expansion, arbitrary command execution, or tool approval from badge click.
