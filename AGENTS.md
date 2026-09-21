# Agent and operator rules

These rules apply to every human and coding agent that edits this repository.

## Identity

- Repository root is the Git toplevel named `ai-lab`.
- Do not create another Git repository.
- Do not create `ai-infrastructure/`.
- Do not rename this repository to `agent-lab`, `ai-factory`, `dentro-ai`, or anything else.
- **Git author for this repo:** `Steven Gerhart <sgerhart@gmail.com>` (local config, ADR 0022). Push via `git@github-sgerhart:sgerhart/ai-lab.git`. Do not use the default `github.com` SSH key (that identity is `dentroio`).

## Read first

Before changing implementation, read:

1. `docs/architecture/overview.md`
2. Relevant ADRs in `docs/decisions/`
3. The work order for the current phase
4. `docs/security/overview.md` if the change touches network, secrets, agents, or isolation

## Authorization

- Building files in Git is not permission to deploy.
- Do not provision hosts, `brew bundle --apply`, `docker compose up`, pull models, or change firewall/SSH/Tailscale ACLs unless the user explicitly authorizes that action.
- Host scripts default to dry-run / preflight. `--apply` is the live path.
- Do not commit or push unless the user explicitly asks.
- Do not silently expand scope beyond the work order.
- Do not invent hostnames, IP addresses, tailnet names, domains, usernames, RAM figures, or credentials.

## Secrets and artifacts

Never add to Git:

- Credentials, tokens, API keys, private keys, kubeconfigs, Tailscale auth keys
- `.env` files with values (`.env.example` and `compose.example.env` with empty placeholders are allowed)
- Model weights, checkpoints, datasets, Docker volumes, virtualenvs
- Sensitive logs and backups

If a secret is found in the tree: stop, remove it, rotate it if it may have leaked, and record a finding in `docs/security/` without pasting the value.

## Honesty

- Do not claim a service works because YAML parses.
- Do not claim a backup works without a restore test.
- Do not claim an agent is autonomous or production-ready when it is scaffolded.
- Do not claim the lab is deployed when only the repository is complete.
- Report failures. Do not conceal them.

## Implementation discipline

- Use bounded work orders.
- Keep documentation aligned with files and commands.
- Add or update tests for meaningful behavior.
- Prefer `uv` for new Python projects when it is available; `python3 -m venv` + `requirements.txt` is the documented fallback.
- Use **LangGraph** for workflow orchestration and resume (ADR 0020). Do not add CrewAI, AutoGen, Temporal, or Celery without a new ADR.
- Keep work-order persistence, dispatch, permissions, and approvals as explicit modules. LangGraph does not replace them.
- Destructive, publishing, merging, and deploy actions require documented approval.

## Validation before claiming work complete

```bash
./scripts/preflight.sh
./scripts/validate-repo.sh
./tests/test_structure.sh
python3 -m unittest discover -s tests -v
```

If Docker is available, also:

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/compose.example.env config
```

That last command still does not start containers.

## Safety defaults

- Bind listeners to `127.0.0.1` unless a deploy-time bind address is set.
- Least privilege for every agent identity.
- A Docker container on macOS is not a malware sandbox. Do not build a malware-analysis environment in this repo.
