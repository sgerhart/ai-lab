## Summary

<!-- What changed and why. -->

## Status honesty

- [ ] I did not claim a service is deployed unless a host was actually changed
- [ ] I did not add secrets, weights, or overlays

## Test plan

- [ ] `./scripts/validate-repo.sh`
- [ ] `python3 -m unittest discover -s tests -v`
