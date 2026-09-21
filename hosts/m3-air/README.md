# m3-air — human / development plane

Confirmed: MacBook Air, Apple M3, **16 GB**, 512 GB.

**Does:** IDE, Git, SSH, dashboards, approvals.  
**Does not:** always-on control-plane compose. Do not `compose up` the lab stack here (port collisions with Clarion are likely).

Clone path: `~/workspace/github/sgerhart/ai-lab` (ADR 0035). Operator login is `stevengerhart`.

See [RUNBOOK.md](RUNBOOK.md) for the independently executable bring-up.

```bash
./hosts/m3-air/setup.sh --preflight
./hosts/m3-air/setup.sh --dry-run
# ./hosts/m3-air/setup.sh --apply
```
