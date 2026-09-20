#!/usr/bin/env bash
# Phase 0 structure and policy tests.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/scripts/validate-repo.sh"
