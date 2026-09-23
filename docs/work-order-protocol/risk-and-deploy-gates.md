# Risk tiers and AI Lab deploy gates

Upstream risk tiers (blast radius, not effort) from
`dentroio/work-order-protocol` `docs/risk-tiers.md`:

| Tier | Typical work | Human verification |
|------|----------------|--------------------|
| P0 | Auth, secrets, data loss, privacy, destructive ops | Always |
| P1 | Schema, API contracts, core workflows, production behavior | Always |
| P2 | Features, UI, non-critical fixes with tests | Usually |
| P3 | Docs, examples, status-only | Usually no |

## AI Lab additions (stricter)

These actions are **never** authorized by “IWO Accepted” alone, even if the
diff looks like docs or a small script change. They require an **explicit human
authorization** in the active conversation (or a human-set Deploy gate):

- `brew bundle --apply` / host package mutation
- `colima start|stop|delete`, Docker/Compose `up`/`down` for lab stack
- Model `pull`, weight/dataset download
- `backup.sh --execute` / any live restore
- Firewall, SSH config, Tailscale ACL changes
- Binding listeners beyond loopback / this host’s Tailscale IPv4 (ADR 0034)
- Privileged agent tools: `git_push`, `gh_pr_merge`, `deploy` (ADR 0018)
- Creating runtime jobs that are meant to mutate hosts

Docs-only IWOs that *describe* deploy steps remain P3 only if they do not
perform those steps.

## Lab-operations agent

Initial policy is **read-only**. New write tools need an ADR and policy change
reviewed by a human — not a silent IWO.

## Adjacent systems

Clarion, the agentic factory, and other product stacks on the Air are
**out of scope** for AI Lab IWOs unless a Feature + ADR explicitly bridges them
(ADR 0007, 0025). Do not reuse Clarion Vault credentials.
