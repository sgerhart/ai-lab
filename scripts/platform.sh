#!/usr/bin/env bash
# Local harness CLI. Binds loopback only for `serve`. Does not deploy to the M1.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/platform/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m ai_lab_platform "$@"
