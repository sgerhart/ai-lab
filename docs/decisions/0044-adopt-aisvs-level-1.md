# ADR 0044 — Adopt OWASP AISVS 1.0 Level 1 as the AI verification catalogue

- **Status:** Proposed
- **Date:** 2026-10-05
- **Related:** ADR 0017, 0018, 0021, 0026, 0040, 0043; FEAT-014, FEAT-015, FEAT-018, FEAT-019; IWO-085–IWO-094

## Context

AI Lab already has a security stack: DefenseClaw on the Air, Antares on the Studio, the security platform module under `platform/src/ai_lab_platform/security/`, and the specified Security Compute Plane (FEAT-019, ADR 0043). Those pieces answer different questions. None of them is a checklist of testable requirements for the lab’s own agents, MCP servers, local models, and retrieval.

The OWASP Artificial Intelligence Security Verification Standard (AISVS) 1.0, released 24 June 2026, is that checklist. It has 12 chapters and three assurance levels. Level 1 is the baseline for any AI application, including internal tools. Verifying Level N assumes the same level of the OWASP Application Security Verification Standard (ASVS). AISVS leaves general application security, generic supply chain, infrastructure hardening, and AI governance to ASVS, SCVS, CIS, NIST, and ISO/IEC 42001.

Upstream text: [OWASP AISVS](https://owasp.org/www-project-artificial-intelligence-security-verification-standard-aisvs-docs/) and [github.com/OWASP/AISVS](https://github.com/OWASP/AISVS) (`1.0/`). The standard is CC BY-SA 4.0. This repository stays all-rights-reserved (ADR 0021), so requirement prose is not copied into Git.

## Decision

1. Adopt **AISVS 1.0 Level 1** as the AI-specific verification catalogue for the lab’s own agents, MCP servers, local models, and retrieval. The home is FEAT-018.
2. Record coverage as a gap register: requirement ID, lab evidence in our own words, and a status of met, partial, gap, or not applicable. Cite the upstream identifier. Do not vendor the PDF or paste requirement sentences.
3. DefenseClaw, Antares, Vise, and the security platform remain the enforcement and evidence tools. AISVS measures them. It does not replace them.
4. A row marked met is an evidence claim about a control that exists. It is not a certification, and it is not an ASVS assessment. The lab has no ASVS assessment.
5. Level 2 and Level 3 requirements may be noted when a control already exists. They are not the adoption bar.
6. Accepting this ADR does not authorize host deploy, model pulls, or new public listeners.

## Consequences

- The Level 1 gap register is [docs/security/aisvs-level-1.md](../security/aisvs-level-1.md) (IWO-085, in review). IWO-086 through IWO-094 are Draft and close the gap and partial rows. Each stays inside its own acceptance criteria. This ADR remains Proposed until a human accepts it.
- Chapters that do not apply to this lab, such as training-pipeline controls while the lab only consumes models, are marked not applicable with a reason.
- An ASVS companion assessment is a separate decision.

## Alternatives considered

- Vendor the AISVS markdown or PDF. Rejected. CC BY-SA 4.0 ShareAlike would attach to copied text, which conflicts with ADR 0021. ADR 0036 already set the pattern: link upstream, adapt only what the lab needs.
- Treat AISVS as a scanner or a fourth runtime service. Rejected. The standard says what to verify. DefenseClaw, Antares, and Vise remain the tools.
- Adopt Level 2 as the bar now. Rejected until a human accepts that target. Level 2 assumes ASVS Level 2, which this lab has not assessed.
