# Tests

```bash
./tests/test_structure.sh
python3 -m unittest discover -s tests -v
# After platform extras:
PYTHONPATH=platform/src platform/.venv/bin/python -m unittest tests.test_langgraph_slice tests.test_studio_worker -v
./scripts/eval-dry-run.sh
bash tests/test_scripts_safety.sh
```

CI runs the same without tailnet access.
