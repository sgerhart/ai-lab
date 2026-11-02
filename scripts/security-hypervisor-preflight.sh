#!/usr/bin/env bash
# Read-only Security Hypervisor preflight & dry-run (FEAT-020 / IWO-078).
# Never creates a VM in default dry-run mode. Mutating live operations require explicit confirmation.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

for arg in "$@"; do
  case "$arg" in
    --help|-h)
      cat <<'EOF'
Usage: ./scripts/security-hypervisor-preflight.sh [OPTIONS]

Default Mode:
  Runs offline dry-run preflight verification of hypervisor contract, template manifest,
  and isolated network parameters. Prints planned lifecycle steps without creating any VM.

Options:
  --dry-run                     Execute read-only preflight and print planned steps (default)
  --template <id>               Security VM template to validate (default: fixture-linux)
  --network <id>                Isolated network identifier to validate (default: fixture-isolated)
  --provider <name>             Hypervisor provider (fake|proxmox|esxi; default: fake)
  --execute-benign              Execute end-to-end benign test fixtures in CI/fake mode
  --live-authorized             Authorize live hypervisor benign validation (requires --confirm-token)
  --confirm-token <token>       Authorization token: AUTHORIZE_LIVE_BENIGN_VALIDATION
  --help, -h                    Show this help message

Constraints:
  - Live hypervisor operations are refused without --live-authorized and confirmation token.
  - Zero network imports in security domain; no host network mutation without separate IWO.
EOF
      exit 0
      ;;
    --apply)
      echo "refusing --apply: hypervisor mutations require separate authorized IWO and --live-authorized" >&2
      exit 2
      ;;
  esac
done

export PYTHONPATH="${ROOT}/platform/src:${PYTHONPATH:-}"
exec python3 -m ai_lab_platform.security.harness "$@"
