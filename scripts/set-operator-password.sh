#!/usr/bin/env bash
# Create/update the personal-lab operator username + password (never Git).
# Stores a PBKDF2 hash in ~/.ai-lab/operator.json (mode 600).
#
# Usage:
#   ./scripts/set-operator-password.sh
#   AI_LAB_OPERATOR_USER=steve ./scripts/set-operator-password.sh

set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}/platform/src${PYTHONPATH:+:$PYTHONPATH}"

USER_NAME="${AI_LAB_OPERATOR_USER:-}"
if [[ -z "$USER_NAME" ]]; then
  printf "Username: "
  read -r USER_NAME
fi
printf "Password (min 8 chars, not echoed): "
read -rs PASS1
printf "\nConfirm password: "
read -rs PASS2
printf "\n"
if [[ "$PASS1" != "$PASS2" ]]; then
  echo "passwords do not match" >&2
  exit 1
fi

export USER_NAME
export PASS="$PASS1"
python3 - <<'PY'
import os
from ai_lab_platform.operator_auth import set_operator_password

meta = set_operator_password(os.environ["USER_NAME"], os.environ["PASS"])
print(f"ok username={meta['username']} path={meta['path']}")
print("Open Studio and sign in with that username and password.")
PY
