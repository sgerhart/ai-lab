# Security Assessment — Coding Model Training Platform

**Sub-Platform:** `coding-training/`  
**Feature:** FEAT-024 (Execution-Verified Coding Model Training)  
**Security Plane:** Isolated Linux Sandbox VM on Proxmox (ADR 0043)  
**Author:** Steven Gerhart <sgerhart@gmail.com>  
**Status:** Validated / Approved  

---

## 1. Executive Security Summary

The Coding Model Training Platform executes untrusted, generative AI candidate code as part of its execution-verified reward feedback loop. Untrusted code execution introduces risks including arbitrary remote code execution (RCE), fork bombing, memory exhaustion, network scanning, file exfiltration, and cross-split test tampering.

This security assessment confirms that the platform enforces **defense-in-depth isolation**:
1. **Host Isolation:** Untrusted code is strictly prohibited from executing on macOS host workstations (`mac-air`, `mac-mini`, `mac-studio`).
2. **Hypervisor Segregation:** In compliance with ADR 0043, code execution is restricted to disposable Linux environments on the external Security Compute Plane (Proxmox/ESXi).
3. **Fail-Closed Execution:** Execution is denied by default (`EXECUTION_ENABLED=false`).
4. **Negative Security Test Suite:** 100% of negative security attack vectors (infinite loops, memory bombs, network egress, stdout bombs, unauthorized writes, and syntax errors) are successfully contained.

---

## 2. Threat Model & Mitigations

| Threat Vector | Potential Impact | Implemented Mitigation | Verification Test |
| :--- | :--- | :--- | :--- |
| **Network Egress / Exfiltration** | Attacker calls `socket` / `urllib` to connect to internal tailnet or internet | Unshare network namespace (`CLONE_NEWNET`); host-only interface with no default gateway | `test_network_egress_denied` (PASS) |
| **Memory Exhaustion (OOM Bomb)** | Candidate attempts to allocate gigabytes of RAM to crash the worker host | Linux cgroup `memory.max` (512 MB default) and disposable process kill | `test_memory_allocation_bomb` (PASS) |
| **Infinite Loop / CPU Starvation** | Candidate runs `while True: pass` consuming 100% CPU | Preemptory `SIGKILL` timeout via sandbox policy `wall_timeout_seconds=5.0` | `test_infinite_loop_timeout_containment` (PASS) |
| **Fork Bomb (Process Bomb)** | Candidate spawns exponential subprocesses | cgroup `pids.max = 32` limiting process creation; rootless jail | Hardened jail runtime |
| **Stdout / Log Bombing** | Candidate floods `sys.stdout` with gigabytes of text | Hard limit of 64 KB with deterministic truncation marker `[TRUNCATED]` | `test_stdout_bomb_truncation` (PASS) |
| **Filesystem Mutation / Tampering** | Candidate attempts to overwrite test bundles or harness code | Ephemeral read-only rootfs; execution workspace chroot/overlayfs | `test_unauthorized_filesystem_modification_blocked` (PASS) |
| **Payload Tampering in Transit** | Man-in-the-middle or queue modification of candidate code | SHA-256 candidate digest verification prior to launching sandbox | `test_candidate_hash_mismatch_fails_closed` (PASS) |
| **Test Case Disclosure** | Model prompt extracts hidden test assertions, leaking split | Prompts contain contract docstring only; test bundle unpacked exclusively inside sandbox | `test_prompt_isolation_zero_test_disclosure` (PASS) |

---

## 3. Negative Security Verification Matrix

The test suite in `tests/unit/test_negative_security.py` directly executes malicious payloads against the sandbox worker jail:

| Test Case | Attack Payload | Expected Result | Verified Result |
| :--- | :--- | :--- | :--- |
| `test_infinite_loop_timeout_containment` | `while True: time.sleep(0.01)` | `status == TIMED_OUT`, `elapsed_ms >= 500` | **PASS** |
| `test_memory_allocation_bomb` | `bytearray(2 * 1024**3)` (2 GB alloc) | `failure_class == MEMORY_EXCEEDED` | **PASS** |
| `test_network_egress_denied` | `socket.socket().connect(('1.1.1.1', 80))` | `failure_class == FORBIDDEN_CALL` | **PASS** |
| `test_stdout_bomb_truncation` | `sys.stdout.write('A' * 1_000_000)` | `len(stdout) <= 65536`, `stdout_truncated == True` | **PASS** |
| `test_syntax_error_candidate` | `def broken(x: return 42` | `failure_class == SYNTAX_ERROR` | **PASS** |
| `test_unauthorized_filesystem_modification_blocked` | `Path('/etc/passwd').write_text(...)` | `failure_class == FORBIDDEN_CALL` | **PASS** |

---

## 4. Architectural Sign-Off

The platform security posture is aligned with AI Lab architectural decisions:
- **ADR 0010:** Local-only default bindings (`127.0.0.1`).
- **ADR 0014:** Immutable execution reports with cryptographically signed attestations.
- **ADR 0043:** Hostile workloads isolated to external Security Compute Plane hypervisors.
- **Least Privilege:** Sandbox processes run without root privileges (`UID 65534 / nobody`).
