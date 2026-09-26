# IWO-079 — MCP server intake

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** M  
**Feature:** [FEAT-005](../features/FEAT-005-python-client-mcp.md)  
**Services / Areas:** platform, docs, tests

## Problem

The lab can speak MCP, and nothing is registered for an agent to call. Cursor's `ai-lab` entry only lets the IDE call the lab. Studio has no agent definitions, and `~/.ai-lab/mcp-servers.json` does not exist.

## What shipped

- `POST /v1/mcp/intake` saves a `lab`, `third-party`, or `draft` stdio server and leaves it unlisted.
- `POST /v1/mcp/servers/{id}/authorize` is the operator listing step.
- `PUT /v1/mcp/servers/{id}/bindings` names which declared tools one agent may call.
- Privileged and network capabilities still wait for run approval.
- The built-in candidate is `scripts/lab-mcp-server.sh`. It is a host process. It is not a container.
- A command that references the Docker socket is rejected. Credential fields store a name, not a secret.

## Out of scope

Starting the server on the mini, editing Cursor's `mcp.json`, and creating a Studio agent.

## Closeout

- Verification evidence: `python3 -m unittest tests.test_mcp_intake tests.test_personal_agent_studio tests.test_security_platform`
- Host deploy performed? No
