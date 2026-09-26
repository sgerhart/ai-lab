#!/usr/bin/env bash
# Install com.ai-lab.defenseclaw-report on the Air (IWO-061).
# Dry-run by default. --apply writes the plist and bootstraps launchctl.
# The agent posts a DefenseClaw summary every 10 minutes. It does not start DefenseClaw.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="$ROOT/hosts/m3-air/com.ai-lab.defenseclaw-report.plist.example"
LABEL="com.ai-lab.defenseclaw-report"
DEST_DIR="${HOME}/Library/LaunchAgents"
DEST="${DEST_DIR}/${LABEL}.plist"
APPLY=0

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --help|-h)
      echo "Usage: $0 [--apply]"
      echo "  Default: dry-run (print planned paths)."
      echo "  --apply: install the Air LaunchAgent for the current user."
      exit 0
      ;;
    *)
      echo "unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$EXAMPLE" ]]; then
  echo "missing example plist: $EXAMPLE" >&2
  exit 1
fi

OPERATOR="$(id -un)"
echo "operator=$OPERATOR"
echo "example=$EXAMPLE"
echo "dest=$DEST"
echo "label=$LABEL"
echo "interval=600s"

if [[ "$APPLY" -ne 1 ]]; then
  echo "dry-run: would render OPERATOR→${OPERATOR}, write $DEST, and launchctl bootstrap"
  echo "Pass --apply on the Air when authorized."
  exit 0
fi

mkdir -p "$DEST_DIR" "${HOME}/.ai-lab"
umask 077
sed "s|/Users/OPERATOR|/Users/${OPERATOR}|g" "$EXAMPLE" >"$DEST"
chmod 644 "$DEST"

UID_NUM="$(id -u)"
DOMAIN="gui/${UID_NUM}"
launchctl bootout "${DOMAIN}/${LABEL}" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$DEST"
launchctl enable "${DOMAIN}/${LABEL}" 2>/dev/null || true
launchctl kickstart -k "${DOMAIN}/${LABEL}" 2>/dev/null || true

echo "installed: $DEST"
launchctl print "${DOMAIN}/${LABEL}" 2>/dev/null | awk '/state =|pid =|runs =/' | head -n 8
echo "log: ${HOME}/.ai-lab/defenseclaw-report.log"
echo "ok"
