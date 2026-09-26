# Inference (Ollama)

Target host: Studio. Do not treat the Air daemon as lab serving.

Suggested unit (not applied):

```ini
# /opt/homebrew/etc/ollama or launchctl env — exact path is host-specific.
# OLLAMA_HOST=127.0.0.1:11434
```

Studio `com.ai-lab.ollama` uses `OLLAMA_HOST=0.0.0.0:11434` so LAN and Tailscale clients share one process (ADR 0041). Lab clients still call `http://mac-studio:11434`.

Pulls: [../../docs/runbooks/adding-a-model.md](../../docs/runbooks/adding-a-model.md)
