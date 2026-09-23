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
  docs/features docs/work-order-protocol
  hosts/m1-mini hosts/studio hosts/m3-air
  templates
  infrastructure/postgres infrastructure/qdrant infrastructure/redis
  infrastructure/backup infrastructure/monitoring
  platform/src/ai_lab_platform
  agents/development agents/research agents/lab-operations
  models/inference models/mlx models/training models/datasets models/evaluations
  scripts tests .github/workflows
)

REQUIRED_FILES=(
  README.md AGENTS.md AGENT_PROCESS.md LICENSE CHANGELOG.md .gitignore .env.example
  templates/WO-template.md
  .github/ISSUE_TEMPLATE/work_order.md
  docs/architecture/overview.md
  docs/decisions/0008-keep-ai-lab-name-and-expanded-layout.md
  docs/decisions/0019-ollama-initial-inference.md
  docs/decisions/0020-langgraph-orchestration.md
  docs/decisions/0027-initial-secret-store.md
  docs/decisions/0028-github-stays-public.md
  docs/decisions/0029-air-ollama-bind-accepted.md
  docs/decisions/0030-icloud-backup-destination.md
  docs/decisions/0031-m3-air-16gb.md
  docs/decisions/0032-tailscale-machine-names.md
  docs/decisions/0033-studio-nvme-deferred.md
  docs/decisions/0034-tailscale-ipv4-bind.md
  docs/decisions/0035-workspace-github-clone-path.md
  docs/decisions/0036-adopt-work-order-protocol.md
  docs/decisions/0037-mini-owns-personal-agent-loop.md
  docs/decisions/0038-model-provider-billing-classes.md
  docs/decisions/0039-hashicorp-vault-on-mini.md
  docs/phases/repo-complete.md
  docs/features/README.md
  docs/features/TEMPLATE.md
  docs/features/index.md
  docs/features/PLAN-mini-first.md
  docs/features/FEAT-001-work-order-planning-and-approval.md
  docs/features/FEAT-002-durable-background-execution.md
  docs/features/FEAT-003-studio-worker-and-models.md
  docs/features/FEAT-004-agent-chat-and-dashboard.md
  docs/features/FEAT-005-python-client-mcp.md
  docs/features/FEAT-006-studio-jupyterlab.md
  docs/features/FEAT-007-coding-agent-pr-workflow.md
  docs/features/FEAT-008-research-retrieval-memory.md
  docs/features/FEAT-009-scheduled-personal-agents.md
  docs/features/FEAT-010-mini-personal-agent-loop.md
  docs/features/FEAT-011-frontier-model-access.md
  docs/features/FEAT-012-lab-site-and-secret-vault.md
  docs/work-orders/IWO-016-lab-site-connect-hub.md
  docs/work-orders/IWO-017-vault-scaffold.md
  platform/src/ai_lab_platform/connect.py
  platform/src/ai_lab_platform/web/lab.html
  docs/work-order-protocol/README.md
  docs/work-order-protocol/lifecycle-mapping.md
  docs/work-order-protocol/risk-and-deploy-gates.md
  docs/work-orders/IWO-001-adopt-work-order-protocol.md
  docs/work-orders/IWO-002-agent-run-conversation-contract.md
  docs/roadmap.md
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
  platform/src/ai_lab_platform/conversation.py
  platform/src/ai_lab_platform/agent_loop.py
  platform/src/ai_lab_platform/web/agents.html
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
  hosts/m1-mini/inventory.yaml hosts/studio/inventory.yaml hosts/m3-air/inventory.yaml
  hosts/m1-mini/com.ai-lab.control-plane.plist.example
  scripts/lib/bind.sh scripts/lib/compose.sh
  platform/src/ai_lab_platform/web/status.html
)

for d in "${REQUIRED_DIRS[@]}"; do
  [[ -d "$ROOT/$d" ]] && pass "dir $d" || fail "missing directory $d"
done
for f in "${REQUIRED_FILES[@]}"; do
  [[ -f "$ROOT/$f" ]] && pass "file $f" || fail "missing file $f"
done

for id in FEAT-001 FEAT-002 FEAT-003 FEAT-004 FEAT-005 FEAT-006 FEAT-007 FEAT-008 FEAT-009 FEAT-010 FEAT-011 FEAT-012; do
  grep -q "$id" "$ROOT/docs/features/index.md" && pass "features index mentions $id" || fail "features index missing $id"
done
grep -q "FakeBackend" "$ROOT/docs/features/FEAT-010-mini-personal-agent-loop.md" \
  && pass "FEAT-010 notes FakeBackend / plans fixture honesty" \
  || fail "FEAT-010 must distinguish plans fixture from model loop"
grep -q "usage_billed_api\|usage-billed" "$ROOT/docs/decisions/0038-model-provider-billing-classes.md" \
  && pass "ADR 0038 defines usage-billed API class" \
  || fail "ADR 0038 missing usage-billed API class"
grep -q "HashiCorp Vault\|hashicorp/vault" "$ROOT/docs/decisions/0039-hashicorp-vault-on-mini.md" \
  && pass "ADR 0039 defines Vault on mini" \
  || fail "ADR 0039 missing Vault"
grep -q "IWO-002" "$ROOT/docs/features/PLAN-mini-first.md" \
  && pass "mini-first plan names IWO-002" \
  || fail "PLAN-mini-first must identify IWO-002"
grep -qi "self-approval\|self-approve" "$ROOT/docs/features/FEAT-001-work-order-planning-and-approval.md" \
  && pass "FEAT-001 mentions self-approval prohibition" \
  || fail "FEAT-001 must prohibit self-approval"
grep -q "Runtime work order" "$ROOT/docs/features/README.md" \
  && pass "features README defines runtime work orders" \
  || fail "features README missing runtime work order entity"
grep -q "historical implementation-phase" "$ROOT/docs/work-orders/README.md" \
  && pass "work-orders README marks WO-000..007 historical" \
  || fail "work-orders README must distinguish historical phase WOs"
grep -Eqi 'accepting an? implementation work order does|does \*\*not\*\* create' \
  "$ROOT/docs/work-order-protocol/lifecycle-mapping.md" \
  && pass "lifecycle mapping separates IWO accept from runtime" \
  || fail "lifecycle mapping must say accepting IWO does not create runtime jobs"
grep -Eqi 'never\*\* authorized|IWO Accepted' \
  "$ROOT/docs/work-order-protocol/risk-and-deploy-gates.md" \
  && pass "risk/deploy gates keep host mutate gated" \
  || fail "risk-and-deploy-gates must keep host mutate gated"
grep -q "Host deploy / mutate authorized" "$ROOT/.github/ISSUE_TEMPLATE/work_order.md" \
  && pass "GitHub WO template includes AI Lab deploy gate" \
  || fail "GitHub work_order.md must include AI Lab deploy gate"
grep -q "Three kinds" "$ROOT/AGENT_PROCESS.md" \
  && pass "AGENT_PROCESS distinguishes feature/IWO/runtime" \
  || fail "AGENT_PROCESS.md must distinguish three work-order kinds"

for pat in '.env' '*.gguf' '*.safetensors' 'id_ed25519' '*.local.yaml' 'local.inventory.yaml' 'compose.local.env'; do
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

TRACKED_BAD="$(git ls-files | grep -E '(^|/)\.env$|\.local\.(ya?ml|md|json|env)$|inventory\.local\.|(^|/)local\.inventory\.ya?ml$|(^|/)compose\.local\.env$' || true)"
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
