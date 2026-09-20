# Python environment strategy

See ADR 0015.

## New lab projects (uv)

| Project | Path | Purpose |
|---------|------|---------|
| platform | `platform/` | Agent harness |
| mlx | `models/mlx/` | MLX experiments |
| training | `models/training/` | Fine-tune / LoRA |
| evaluations | `models/evaluations/` | Eval runners |

### Create (example: platform)

```bash
cd platform
uv python install 3.11
uv venv --python 3.11
uv sync
```

### Update

```bash
cd platform
uv lock
uv sync
```

### Reproduce on another machine

```bash
cd platform
uv sync --frozen
```

### Remove

```bash
rm -rf platform/.venv
```

Do not `pip install` into the system interpreter.

## Existing projects

`pyenv` remains valid. This repo will not migrate Clarion or other trees. Preflight accepts `uv` from Homebrew *or* pyenv shims.

## Jupyter

Install JupyterLab inside the Studio `models/mlx` or `models/training` uv env, not globally. The Air uses a browser client against that server when the Studio is up.
