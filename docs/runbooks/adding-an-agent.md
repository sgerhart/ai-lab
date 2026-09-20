# Adding an agent

**Prerequisites:** Harness exists. Policy review.

**Effects:** New directory under `agents/<id>/` with README + `policy.json`. Catalog row.

**Steps:** Copy `agents/development/` as a template. Set `read_only` if ops. Privileged tools must be listed and still hit the approval gate. Add a `plan_for()` branch in `platform/src/ai_lab_platform/agent_plans.py` and tests in `tests/test_agent_plans.py`.

**Verify:** `python3 -c` policy JSON parses; catalog lists the id; `python3 -m unittest tests.test_agent_plans -v`.

**Rollback:** Delete the directory and catalog row. Do not leave orphan privileged tools in the harness.
