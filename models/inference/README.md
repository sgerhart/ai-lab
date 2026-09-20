# Inference (Ollama)

Target host: Studio. Do not treat the Air daemon as lab serving.

Suggested unit (not applied):

```ini
# /opt/homebrew/etc/ollama or launchctl env — exact path is host-specific.
# OLLAMA_HOST=127.0.0.1:11434
```

For M1→Studio access, set `OLLAMA_HOST` to the Studio Tailscale IP at deploy time. Never `0.0.0.0` without an ADR.

Pulls: [../../docs/runbooks/adding-a-model.md](../../docs/runbooks/adding-a-model.md)
