# Reviewing agent permissions

**Steps:** Read `agents/*/policy.json`. Confirm lab-operations `read_only: true`. Confirm privileged tools are a subset of `PRIVILEGED_TOOLS` in `platform/src/ai_lab_platform/approvals.py`. Any new write tool for lab-ops needs an ADR.

**Verify:** `python3 -m json.tool agents/lab-operations/policy.json`

**Rollback:** Revert the policy file in Git.
