# Studio JupyterLab and Air access

**Host:** `mac-studio` as `stevengerhart`  
**Client:** `mac-air` (browser or local Jupyter picking the Studio kernel)

Ordinary notebook cells run **on the Studio**. They do **not** go through the mini agent harness.

## Layout on Studio

| Path | Role |
|------|------|
| `~/workspace/github/sgerhart/ai-lab` | Repo clone |
| `~/.ai-lab/jupyter/.venv` | JupyterLab + ipykernel env |
| Kernel display name | `Python (mac-studio M5)` |
| Bind | `127.0.0.1:8888` only (never `0.0.0.0`) |
| Token | `~/.ai-lab/jupyter/token` (mode 600) |

## Start JupyterLab on Studio

```bash
ssh mac-studio
~/.ai-lab/jupyter/start-jupyterlab.sh
```

Or from Air (foreground over SSH):

```bash
ssh mac-studio '~/.ai-lab/jupyter/start-jupyterlab.sh'
```

## Access from Air (preferred — lab site on mini)

No SSH tunnel. Studio Jupyter must listen on its **Tailscale IPv4**
(`hosts/studio/start-jupyterlab.sh.example`). Mini holds a copy of the Jupyter
token at `~/.ai-lab/studio-jupyter.token` (sync:
`./scripts/sync-studio-jupyter-token.sh`) and env:

```bash
STUDIO_JUPYTER_URL=http://mac-studio:8888
STUDIO_OLLAMA_URL=http://mac-studio:11434
```

**Lab API token** (not a cloud key) — already on the mini:

```bash
ssh mac-mini 'cat ~/.ai-lab/api.token'
```

Paste into Lab / Agents / API keys. Details: http://mac-mini:8088/help#token

Then on Air:

1. Open `http://mac-mini:8088/lab` (or the mini Tailscale name/IP you use).
2. Paste the lab API token from above.
3. Click **Open Jupyter**.

## Access from Air (legacy SSH tunnel)

```bash
# Terminal A — keep open
ssh -N -L 8888:127.0.0.1:8888 mac-studio

# Terminal B / browser
TOKEN=$(ssh mac-studio 'cat ~/.ai-lab/jupyter/token')
open "http://127.0.0.1:8888/lab?token=${TOKEN}"
```

Cells execute on the Studio (check with a hardware cell).

## Access from Air Jupyter / Cursor (remote kernel)

After the Studio kernel is registered locally on the Air:

```bash
jupyter kernelspec list   # should show studio-m5
```

Select **Python (mac-studio M5)** in the notebook UI. The kernelspec starts
`ipykernel` over SSH on the Studio.

## Ollama on Studio

```bash
export OLLAMA_HOST=127.0.0.1:11434
# brew services or `ollama serve` — see hosts/studio/RUNBOOK.md
curl -sS http://127.0.0.1:11434/api/tags
```

Do **not** `ollama pull` until authorized ([adding-a-model.md](adding-a-model.md)).

## Verify

In a notebook using the Studio kernel (**restart the kernel** after GPU packages were installed):

```python
import platform, socket, pathlib
print(platform.processor(), platform.machine())
print(socket.gethostname())
print(pathlib.Path.home())
```

Expect Studio hostname / M5 / `stevengerhart` home — not the Air.

### GPU (Metal / MLX / MPS)

Installed in `~/.ai-lab/jupyter/.venv`: `mlx`, `mlx-lm`, `torch` (Apple Silicon). No CUDA.

```python
import mlx.core as mx
import torch

print("mlx default device:", mx.default_device())
a = mx.random.normal((2048, 2048))
b = mx.random.normal((2048, 2048))
c = a @ b
mx.eval(c)
print("mlx matmul ok")

print("mps available:", torch.backends.mps.is_available())
x = torch.randn(2048, 2048, device="mps")
y = x @ x
torch.mps.synchronize()
print("torch mps matmul ok:", y.device)
```

Expect `Device(gpu, 0)` (or similar) from MLX and `mps:0` from PyTorch.

### Inference smoke (Ollama + MLX-LM)

First models (authorized 2026-09-23): Ollama `llama3.2:3b` (~2.0 GB) and
`mlx-community/Llama-3.2-3B-Instruct-4bit` (HF cache). Sample notebook on Studio:
`~/ai-lab-notebooks/studio-inference-smoke.ipynb`.

**Ollama (loopback on Studio):**

```python
import json, urllib.request

payload = json.dumps({
    "model": "llama3.2:3b",
    "prompt": "Reply in one short sentence: hello from Studio Ollama.",
    "stream": False,
    "options": {"num_predict": 48},
}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:11434/api/generate",
    data=payload,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=120) as resp:
    print(json.load(resp)["response"].strip())
```

**MLX-LM (GPU):**

```python
from mlx_lm import load, generate

model, tokenizer = load("mlx-community/Llama-3.2-3B-Instruct-4bit")
messages = [{"role": "user", "content": "In one short sentence, say hello from Apple Silicon MLX."}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print(generate(model, tokenizer, prompt=prompt, max_tokens=64, verbose=False).strip())
```

Do not commit weights. Catalog rows stay `pull_authorized: false` / not `status: pulled`
([adding-a-model.md](adding-a-model.md)).

## Persistence on Studio

LaunchAgents (user domain):

- `com.ai-lab.ollama` — `OLLAMA_HOST=127.0.0.1:11434`
- `com.ai-lab.jupyterlab` — loopback `:8888`

Brew's `sh.brew.ollama` plist is disabled so it does not fight the loopback agent.

## Air kernelspec

Registered at `~/Library/Jupyter/kernels/studio-m5` (`Python (mac-studio M5)`).
Select it in Jupyter / Cursor; cells run on Studio over SSH (`ssh -L` ZMQ bridge).

