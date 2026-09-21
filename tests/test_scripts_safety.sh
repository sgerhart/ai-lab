#!/usr/bin/env bash
# Script safety: dry-run backup, restore refuse, throwaway DSN guards.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

backup_out="$("$ROOT/scripts/backup.sh")"
echo "$backup_out" | grep -q "dry-run" || { echo "FAIL: backup.sh should dry-run"; exit 1; }
echo "$backup_out" | grep -q "iCloud" || { echo "FAIL: backup.sh dry-run should mention iCloud"; exit 1; }

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

set +e
"$ROOT/scripts/backup.sh" --execute --target /tmp/ai-lab-not-icloud >/tmp/ai-lab-backup-icloud.txt 2>&1
rc=$?
set -e
[[ "$rc" -eq 1 ]] || { echo "FAIL: non-iCloud --execute should exit 1 (got $rc)"; exit 1; }
grep -q "iCloud Drive" /tmp/ai-lab-backup-icloud.txt

# Bind policy (ADR 0034)
# shellcheck source=../scripts/lib/bind.sh
source "$ROOT/scripts/lib/bind.sh"
ai_lab_bind_allowed 127.0.0.1 || { echo "FAIL: loopback should be allowed"; exit 1; }
ai_lab_bind_allowed 0.0.0.0 && { echo "FAIL: 0.0.0.0 must be refused"; exit 1; }
ai_lab_bind_allowed 8.8.8.8 && { echo "FAIL: public IP must be refused"; exit 1; }
set +e
AI_LAB_BIND_ADDRESS=0.0.0.0 "$ROOT/scripts/control-plane.sh" >/tmp/ai-lab-bind.txt 2>&1
rc=$?
set -e
[[ "$rc" -eq 2 ]] || { echo "FAIL: control-plane.sh 0.0.0.0 should exit 2 (got $rc)"; exit 1; }

plist="$ROOT/hosts/m1-mini/com.ai-lab.control-plane.plist.example"
grep -q "com.ai-lab.control-plane" "$plist" || { echo "FAIL: launchd example missing label"; exit 1; }
grep -Eiq "TOKEN|PASSWORD|DATABASE_URL" "$plist" && { echo "FAIL: launchd example must not contain secrets"; exit 1; }

rm -rf "$tmpdir" /tmp/ai-lab-restore-no.txt /tmp/ai-lab-restore-live.txt /tmp/ai-lab-restore-ts.txt /tmp/ai-lab-restore-5432.txt /tmp/ai-lab-restore-name.txt /tmp/ai-lab-backup-icloud.txt /tmp/ai-lab-bind.txt
echo "script safety OK"
