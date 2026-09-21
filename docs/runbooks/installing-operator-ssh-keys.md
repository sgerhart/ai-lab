# Installing operator SSH keys

**Prerequisites:** Tailscale MagicDNS working (`tailscale ping mac-mini`). Remote Login enabled on the target Mac (System Settings → General → Sharing → Remote Login). This Air is the SSH client.

**Effects:** Creates `~/.ssh/ai-lab_ed25519` on the Air (not in Git). Installs that public key in `authorized_keys` on lab Macs. Adds `Host mac-mini` / `mac-studio` / `mac-air` to `~/.ssh/config`. Does **not** change firewall rules or disable password authentication.

Use a **dedicated** lab key. Do not reuse `clarion_dev` or `id_ed25519_github`.

## On the Air (client)

```bash
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/ai-lab_ed25519 -C "ai-lab-operator@mac-air"
# Host blocks: User + IdentityFile ~/.ssh/ai-lab_ed25519, IdentitiesOnly yes
```

## Install the public key on mac-mini

If password SSH still works from the Air:

```bash
ssh-copy-id -i ~/.ssh/ai-lab_ed25519.pub sgerhart@mac-mini
```

If BatchMode publickey is denied and you are sitting at the mini, copy `~/Library/Mobile Documents/com~apple~CloudDocs/ai-lab-ssh/install-on-mac-mini.sh` (iCloud) or the Taildrop inbox, then run it **on the mini**.

**Verify:** `ssh -o BatchMode=yes sgerhart@mac-mini 'hostname; sysctl -n machdep.cpu.brand_string'` — expect Apple M1. The mini operator login is `sgerhart` (Air is `stevengerhart`).

**Rollback:** Remove the `ai-lab-operator@mac-air` line from the mini's `~/.ssh/authorized_keys`. Delete `~/.ssh/ai-lab_ed25519` on the Air. Restore `~/.ssh/config` from `~/.ssh/config.bak.ai-lab-*` if needed.

Do not commit keys, `*.pub`, or filled SSH URIs.
