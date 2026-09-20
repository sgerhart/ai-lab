# Versioning and updates

- Pin container tags in `infrastructure/compose.yaml` (not `:latest`).
- Pin Python deps with `uv.lock` once `uv lock` has been run on a project.
- Host packages: Brewfile is the desired set, not a freeze of every keg version. Record `brew bundle dump` output in a gitignored overlay if a host must be bit-for-bit.
- macOS upgrades: [../runbooks/upgrading-macos.md](../runbooks/upgrading-macos.md) — pause compose and inference first.
- Update containers: [../runbooks/updating-containers.md](../runbooks/updating-containers.md).
- Update Python: [../runbooks/updating-python-dependencies.md](../runbooks/updating-python-dependencies.md).

Do not auto-upgrade engines on the M1; 16 GB leaves little room for surprise Docker VM growth.
