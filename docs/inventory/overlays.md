# Local overlays

Committed docs describe roles. Live facts that identify the home network stay on disk, ignored by Git.

## File convention

```text
hosts/<name>/local.inventory.yaml
```

Patterns ignored by Git (see `.gitignore`):

- `**/*.local.md`
- `**/*.local.yml`
- `**/*.local.yaml`
- `**/*.local.json`
- `**/inventory.local.*`
- `**/local.inventory.yaml` (the documented overlay filename; `*.local.yaml` does **not** match it)
- `hosts/**/local/`

## Example

Copy [`hosts/_template/local.inventory.yaml.example`](../../hosts/_template/local.inventory.yaml.example) to `hosts/<name>/local.inventory.yaml` and fill it on the workstation. Never `git add` that file. The validator flags likely overlay filenames if they are staged.

## What belongs in an overlay

- RFC1918 and public IPs
- MAC addresses, serial numbers
- SSH `HostName` / `User` / `IdentityFile`
- BIOS/firmware versions if they uniquely identify hardware
- Tailscale MagicDNS suffix and IPv4 (observed on a live node; still not committed while the repo is public)
