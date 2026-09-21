#!/usr/bin/env bash
# Validate ai-lab repository shape, git root, and obvious secret/weight leaks.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail() { echo "FAIL: $*" >&2; FAILURES=$((FAILURES + 1)); }
pass() { echo "PASS: $*"; }
FAILURES=0

echo "== ai-lab repository validation =="
echo "root: $ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "not a git work tree"
else
  TOP="$(git rev-parse --show-toplevel)"
  if [[ "$TOP" != "$ROOT" ]] || [[ "$(basename "$TOP")" != "ai-lab" ]]; then
    fail "git toplevel must be ai-lab (found $TOP)"
  else
    pass "git toplevel is ai-lab"
  fi
fi

if [[ -d "$ROOT/ai-infrastructure" ]]; then
  fail "nested ai-infrastructure/ directory exists; it must not"
else
  pass "no nested ai-infrastructure/"
fi

REQUIRED_DIRS=(
  docs/architecture docs/decisions docs/deployment docs/operations
  docs/security docs/models docs/agents docs/runbooks docs/work-orders
  hosts/m1-mini hosts/studio hosts/m3-air
  infrastructure/postgres infrastructure/qdrant infrastructure/redis
  infrastructure/backup infrastructure/monitoring
  platform/src/ai_lab_platform
  agents/development agents/research agents/lab-operations
  models/inference models/mlx models/training models/datasets models/evaluations
  scripts tests .github/workflows
)

REQUIRED_FILES=(
  README.md AGENTS.md LICENSE CHANGELOG.md .gitignore .env.example
  docs/architecture/overview.md
  docs/decisions/0008-keep-ai-lab-name-and-expanded-layout.md
  docs/decisions/0019-ollama-initial-inference.md
  docs/decisions/0020-langgraph-orchestration.md
  docs/decisions/0027-initial-secret-store.md
  docs/phases/repo-complete.md
  platform/mcp/allowlist.json
  infrastructure/compose.yaml
  infrastructure/compose.example.env
  platform/src/ai_lab_platform/orchestrator.py
  platform/src/ai_lab_platform/control_app.py
  platform/src/ai_lab_platform/slice_graph.py
  platform/src/ai_lab_platform/agent_plans.py
  platform/src/ai_lab_platform/postgres_store.py
  platform/src/ai_lab_platform/settings.py
  platform/src/ai_lab_platform/schema.sql
  models/catalog.json
  scripts/eval-dry-run.sh
  scripts/train.sh
  scripts/test-postgres-slice.sh
  scripts/restore-throwaway.sh
  scripts/test-backup-restore.sh
  tests/test_scripts_safety.sh
  agents/lab-operations/policy.json
  scripts/preflight.sh scripts/backup.sh scripts/restore.sh scripts/platform.sh
  scripts/control-plane.sh scripts/studio-worker.sh
  hosts/m1-mini/Brewfile hosts/studio/Brewfile hosts/m3-air/Brewfile
  hosts/m1-mini/RUNBOOK.md hosts/studio/RUNBOOK.md hosts/m3-air/RUNBOOK.md
)

for d in "${REQUIRED_DIRS[@]}"; do
  [[ -d "$ROOT/$d" ]] && pass "dir $d" || fail "missing directory $d"
done
for f in "${REQUIRED_FILES[@]}"; do
  [[ -f "$ROOT/$f" ]] && pass "file $f" || fail "missing file $f"
done

for pat in '.env' '*.gguf' '*.safetensors' 'id_ed25519' '*.local.yaml'; do
  grep -Fq "$pat" "$ROOT/.gitignore" && pass "gitignore contains $pat" || fail ".gitignore missing $pat"
done

[[ -f "$ROOT/.env" ]] && fail ".env exists in repo root" || pass "no .env at repo root"

while IFS= read -r -d '' f; do
  fail "forbidden artifact present: ${f#"$ROOT"/}"
done < <(find "$ROOT" -type f \( -name '*.gguf' -o -name '*.safetensors' -o -name '*.ckpt' \) ! -path '*/.git/*' -print0 2>/dev/null || true)

SCAN_FILE="$(mktemp)"
set +e
grep -R --exclude-dir=.git --exclude-dir=.cursor --exclude-dir=.venv --exclude-dir=__pycache__ -nE \
  'BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-proj-[A-Za-z0-9_-]{20,}' \
  "$ROOT" >"$SCAN_FILE" 2>/dev/null
set -e
if [[ -s "$SCAN_FILE" ]]; then
  fail "possible secret material found"
  cat "$SCAN_FILE" >&2
else
  pass "no PEM/token prefixes found"
fi
rm -f "$SCAN_FILE"

TRACKED_BAD="$(git ls-files | grep -E '(^|/)\.env$|\.local\.(ya?ml|md|json)$|inventory\.local\.' || true)"
[[ -n "$TRACKED_BAD" ]] && fail "git tracking forbidden files: $TRACKED_BAD" || pass "git is not tracking overlays or .env"

if grep -v '^[[:space:]]*#' "$ROOT/infrastructure/compose.yaml" | grep -q '0.0.0.0'; then
  fail "compose.yaml publishes on all interfaces"
else
  pass "compose.yaml does not publish on all interfaces"
fi

for sh in "$ROOT"/scripts/*.sh "$ROOT"/hosts/*/setup.sh; do
  [[ -f "$sh" ]] || continue
  bash -n "$sh" && pass "bash -n ${sh#"$ROOT"/}" || fail "syntax $sh"
done

for json in "$ROOT"/agents/*/policy.json "$ROOT"/models/catalog.json "$ROOT"/platform/mcp/allowlist.json; do
  python3 -m json.tool "$json" >/dev/null && pass "json ${json#"$ROOT"/}" || fail "json $json"
done

echo
if [[ "$FAILURES" -gt 0 ]]; then
  echo "RESULT: $FAILURES failure(s)"
  exit 1
fi
echo "RESULT: OK"
