#!/usr/bin/env bash
# Run a command against a read-only repo snapshot under sandbox-exec (IWO-048).
# Dry-run by default. No Docker required (Studio has none).
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${ANTARES_SANDBOX_PROFILE:-$ROOT/hosts/studio/antares-sandbox.sb}"
APPLY=0
REPO=""
CMD=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --repo) REPO="${2:-}"; shift 2 ;;
    --) shift; CMD=("$@"); break ;;
    --help|-h)
      echo "Usage: $0 --repo /path/to/repo [--apply] -- <command...>"
      echo "  Copies repo to a temp snapshot, runs command with network denied."
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$REPO" || ! -d "$REPO" ]]; then
  echo "--repo must be an existing directory" >&2
  exit 2
fi
if [[ ${#CMD[@]} -eq 0 ]]; then
  echo "missing command after --" >&2
  exit 2
fi
if [[ ! -f "$PROFILE" ]]; then
  echo "missing sandbox profile: $PROFILE" >&2
  exit 1
fi

SNAP="$(mktemp -d /tmp/ai-lab-antares-XXXXXX)"
cleanup() { /bin/rm -r "$SNAP" 2>/dev/null || true; }
trap cleanup EXIT

echo "repo=$REPO"
echo "snapshot=$SNAP/repo"
echo "profile=$PROFILE"
echo "cmd=${CMD[*]}"

if [[ "$APPLY" -ne 1 ]]; then
  echo "dry-run: would rsync snapshot and sandbox-exec the command"
  echo "Pass --apply to execute."
  exit 0
fi

mkdir -p "$SNAP/repo" "$SNAP/work"
rsync -a --delete "$REPO"/ "$SNAP/repo"/
export AI_LAB_ANTARES_REPO="$SNAP/repo"
export AI_LAB_ANTARES_WORK="$SNAP/work"

# Probe: network should fail inside sandbox
if sandbox-exec -f "$PROFILE" /usr/bin/curl -sS -m 2 https://example.com -o /dev/null 2>/dev/null; then
  echo "sandbox FAILED: network still allowed" >&2
  exit 1
fi
echo "sandbox_network_denied=ok"

sandbox-exec -f "$PROFILE" /usr/bin/env \
  AI_LAB_ANTARES_REPO="$SNAP/repo" \
  AI_LAB_ANTARES_WORK="$SNAP/work" \
  "${CMD[@]}"
echo "ok"
