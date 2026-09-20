#!/usr/bin/env bash
# Script safety: dry-run backup, restore refuse, throwaway DSN guards.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

backup_out="$("$ROOT/scripts/backup.sh")"
echo "$backup_out" | grep -q "dry-run" || { echo "FAIL: backup.sh should dry-run"; exit 1; }

set +e
"$ROOT/scripts/restore.sh" >/tmp/ai-lab-restore-no.txt 2>&1
rc=$?
set -e
[[ "$rc" -eq 1 ]] || { echo "FAIL: restore.sh without confirm should exit 1 (got $rc)"; exit 1; }
grep -q "Refusing restore" /tmp/ai-lab-restore-no.txt

tmpdir="$(mktemp -d /tmp/ai-lab-restore-guard.XXXXXX)"
mkdir -p "$tmpdir/demo"
echo "SELECT 1;" > "$tmpdir/demo/postgres.sql"
set +e
"$ROOT/scripts/restore.sh" --confirm-restore YES-RESTORE-LIVE --backup-id demo --target "$tmpdir" >/tmp/ai-lab-restore-live.txt 2>&1
rc=$?
set -e
[[ "$rc" -eq 2 ]] || { echo "FAIL: live restore should exit 2 (got $rc)"; exit 1; }
grep -q "will not overwrite live data" /tmp/ai-lab-restore-live.txt

set +e
"$ROOT/scripts/restore-throwaway.sh" --dump "$tmpdir/demo/postgres.sql" --dsn "postgresql://ai_lab:x@10.0.0.1:55433/ai_lab" >/tmp/ai-lab-restore-ts.txt 2>&1
rc=$?
set -e
[[ "$rc" -eq 1 ]] || { echo "FAIL: non-loopback DSN should be refused (got $rc)"; exit 1; }

set +e
"$ROOT/scripts/restore-throwaway.sh" --dump "$tmpdir/demo/postgres.sql" --dsn "postgresql://ai_lab:x@127.0.0.1:5432/ai_lab" >/tmp/ai-lab-restore-5432.txt 2>&1
rc=$?
set -e
[[ "$rc" -eq 1 ]] || { echo "FAIL: port 5432 DSN should be refused (got $rc)"; exit 1; }

set +e
"$ROOT/scripts/restore-throwaway.sh" --dump "$tmpdir/demo/postgres.sql" --container postgres >/tmp/ai-lab-restore-name.txt 2>&1
rc=$?
set -e
[[ "$rc" -eq 1 ]] || { echo "FAIL: compose-like container name should be refused (got $rc)"; exit 1; }

rm -rf "$tmpdir" /tmp/ai-lab-restore-no.txt /tmp/ai-lab-restore-live.txt /tmp/ai-lab-restore-ts.txt /tmp/ai-lab-restore-5432.txt /tmp/ai-lab-restore-name.txt
echo "script safety OK"
