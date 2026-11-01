# Security Compute VM Templates (FEAT-019 / IWO-073)

This directory defines immutable baseline template profiles and validation contracts for Cybersecurity Vise analysis guests.

## Template Invariants (ADR 0043)

1. **Immutability:** Golden templates are read-only (`immutable: true`). Analysis jobs clone templates ephemerally; mutating calls to base templates are strictly refused.
2. **Network Isolation:** Analysis templates require single-NIC isolated network attachment (`network_policy: "isolated"`).
3. **Clean Snapshot:** Jobs verify an authorized clean baseline snapshot (`clean-baseline`) prior to launching untrusted samples.
4. **Disposable Credentials:** No production credentials, tokens, or persistent keys may be embedded in templates (`disposable_credentials_policy: "ephemeral-per-job"`).
5. **Sensor & Tool Manifest:** Required tools (e.g. Wireshark, Yara, Sysinternals) and sensors (Auditd, Sysmon, OSQuery) are declared in the manifest schema and verified during preflight.

## Baseline Profiles

- `linux-baseline.json`: Ubuntu 24.04 LTS static/behavioral analysis baseline.
- `windows-baseline.json`: Windows 11 Enterprise (23H2) static/behavioral analysis baseline.
