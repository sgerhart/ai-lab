# IWO-080 — Read-only third-party MCP candidates

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** M  
**Owner:** implementation agent  
**Feature:** [FEAT-005](../features/FEAT-005-python-client-mcp.md)  
**Services / Areas:** platform, docs, tests

## Problem

Studio has an intake ([IWO-079](IWO-079-mcp-server-intake.md)) and no third-party server recorded. Lookup MCPs for hashes and CVEs are the ones that match that intake. They are stdio HTTPS clients, not hypervisor guests. Placement: [mcp-servers.md](../architecture/mcp-servers.md).

## Decision Context

- Chosen approach: Catalog two candidates the operator can submit later. VirusTotal read reports (hash, domain, IP). One keyless CVE lookup (NVD, OSV, CISA KEV). Both stay unlisted until `authorize`. Bind only the read tools.
- Alternatives rejected: Installing the FuzzingLabs hub or the Snyk roundup's scanners on a Mac. Standing up Proxmox for these lookups. Putting API keys in Git. Enabling VirusTotal URL submission or corpus search on the first binding. Labeling public HTTPS as `tailnet-client`.
- Assumptions: The operator will supply a VirusTotal credential name when they want that server authorized. This draft does not authorize it.
- Open decisions: None for the catalog. The keyless package is `cve-mcp`, stdio only, and it is not vendored. Declared tools are `nvd_get`, `nvd_search`, `kev_check`, `osv_query`, and `osv_get`. Exploit search, Shodan IP lookup, Nuclei, and Metasploit checks stay undeclared.

## What To Build / Fix

When this draft is accepted:

- Document the stdio command shape, declared read tools, and credential name for VirusTotal (`@burtthecoder/mcp-virustotal` stdio only). The process makes public HTTPS calls.
- Document one keyless CVE candidate the same way.
- Tests that an unlisted candidate is denied, URL-submit and corpus-search tools are absent from the first binding, and a credential field rejects a raw secret.
- Do not call the network from tests.

## Expected Change Surface

- Expected: intake catalog entries, a public-https network class, tests
- Tests: unlisted deny, first binding omits URL submit and corpus search, credential field rejects a raw secret
- Docs/status: `docs/features/index.md`, `docs/runbooks/adding-an-mcp-server.md`

## Validation Plan

- Automated: `python3 -m unittest tests.test_mcp_intake`
- Manual: none until an operator authorizes a server
- Evidence to include: unit output. No live VirusTotal or NVD call.

## Out Of Scope

Proxmox, ESXi, VMs, Docker, Nmap, Nuclei, SQLMap, Burp, Shodan search, packet capture, and any live `npx` install.

## Do NOT Change

- No secrets in Git.
- Do not authorize a server as a side effect of merging the catalog.
- Do not weaken deny-unlisted.

## Acceptance Criteria

1. Both candidates are visible from `GET /v1/mcp/intake` and `listed` is false. 2. Authorizing is a separate call. 3. The first VirusTotal binding omits URL submission and corpus search. 4. Tests do not contact VirusTotal or NVD.

## AI Lab gates

- **Creates runtime job on mac-mini?** No
- **Host deploy / mutate authorized by this IWO alone?** **No**
- **Privileged tools expected?** none
- **May run on Air?** Yes — docs and unit tests only

## Execution

- **Risk tier:** P1
- **Depends on:** IWO-079
- **Human verification required:** Yes, before any authorize call
- **Project status record:** `docs/features/index.md`

## Closeout

- Verification evidence: `python3 -m unittest tests.test_mcp_intake tests.test_personal_agent_studio tests.test_security_platform`
- Host deploy performed? No
