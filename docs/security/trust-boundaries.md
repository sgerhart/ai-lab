# Trust boundaries

| Zone | Trust for secrets | Examples |
|------|-------------------|----------|
| Operator session on Air | High | Cursor, this repo, `gh` |
| M1 loopback | High if bind is 127.0.0.1 | local compose |
| Studio loopback | High for local Ollama | workers on Studio |
| Tailnet | Medium — identity of *nodes*, not of apps | MagicDNS |
| GitHub public remote | Low | `sgerhart/ai-lab` today |
| Cloud LLM APIs | Untrusted with private data unless work order allows | OpenAI, Anthropic |
| Home LAN RFC1918 | Medium, mixed with Clarion VMs | not the AI-lab transport |

Compromise of the Air should not include Postgres data if the Air only has a client role and no copied dumps. Compromise of the Studio should not erase the queue (state is on M1). Compromise of the M1 is a full lab incident — rotate DB passwords, Tailscale, and API tokens using [../runbooks/rotating-credentials.md](../runbooks/rotating-credentials.md).
