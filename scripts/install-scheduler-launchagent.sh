#!/usr/bin/env bash
# Install com.ai-lab.scheduler-tick LaunchAgent (FEAT-009 / IWO-052).
# Dry-run by default. Pass --apply to write plist + bootstrap launchctl.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="$ROOT/hosts/m1-mini/com.ai-lab.scheduler-tick.plist.example"
LABEL="com.ai-lab.scheduler-tick"
DEST_DIR="${HOME}/Library/LaunchAgents"
DEST="${DEST_DIR}/${LABEL}.plist"
APPLY=0

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --help|-h)
      echo "Usage: $0 [--apply]"
      echo "  Default: dry-run (print planned paths)."
      echo "  --apply: install LaunchAgent for the current user (mini)."
      exit 0
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

if [[ "$APPLY" -ne 1 ]]; then
  echo "dry-run: would render OPERATOR→${OPERATOR}, write $DEST, and launchctl bootstrap"
  echo "Pass --apply on mac-mini when authorized."
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
launchctl print "${DOMAIN}/${LABEL}" 2>/dev/null | head -n 25 || true
echo "log: ${HOME}/.ai-lab/scheduler-tick.log"
echo "ok"
