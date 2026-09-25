# Agent catalog

| ID | Purpose | Backend | Data scope | Network | Status |
|----|---------|---------|------------|---------|--------|
| coding-assistant | Inspect a workspace; patch and commit only in a harness worktree after approval | routed | declared workspace; writes only under `~/.ai-lab/worktrees/` | none | IWO-056 reads; IWO-058 isolated writes. Push denied |
| development | Bounded repo changes + tests + PR summary | routed | declared workspace only | GitHub if scoped token | Local plan: repo_read + git_status (Studio worker executes this; no push) |
| research | Evidence-bearing reports | routed | authorized sources | allowlisted HTTP | Local plan: limitations report, no fetch, no invented citations |
| lab-operations | Read-only health and drift notes | routed | lab configs + health URLs | Tailscale health | Local plan: loopback port probe + compose stub |
| lab-docs-architect | This repo (Cursor) | Cursor | this repository | local Git | Active in chat, not the harness |
