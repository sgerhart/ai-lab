# Download Antares-1B weights + CLI zip onto Studio (IWO-047).
# Runs inside Studio Jupyter kernel. Requires HF gated access + token file.
import os
from pathlib import Path

home = Path.home()
dest = home / ".ai-lab" / "antares" / "antares-1b"
cli_dest = home / ".ai-lab" / "antares" / "cli"
dest.mkdir(parents=True, exist_ok=True)
cli_dest.mkdir(parents=True, exist_ok=True)

token = None
for p in (
    home / ".ai-lab" / "hf.token",
    home / ".ai-lab" / "huggingface.token",
    home / ".cache" / "huggingface" / "token",
):
    if p.is_file():
        token = p.read_text(encoding="utf-8").strip()
        print("token_file", str(p), "chars", len(token))
        break
if not token:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or None
    print("token_env", "set" if token else "missing")

if not token:
    raise SystemExit(
        "HF token required for gated repo fdtn-ai/antares-1b. "
        "Accept the model gate on Hugging Face, then write the token to "
        "~/.ai-lab/hf.token on Studio (chmod 600)."
    )

from huggingface_hub import list_repo_files, snapshot_download

repo = "fdtn-ai/antares-1b"
print("listing", repo)
files = list_repo_files(repo, token=token)
print("file_count", len(files))
for name in files:
    if name.lower().endswith(".zip") or "cli" in name.lower():
        print("cli_candidate", name)

print("snapshot_download ->", dest)
path = snapshot_download(repo_id=repo, local_dir=str(dest), token=token)
print("snapshot_ok", path)

zips = sorted(dest.rglob("*.zip"))
print("zips", [str(z.relative_to(dest)) for z in zips[:10]])
for z in zips:
    target = cli_dest / z.name
    if not target.exists():
        target.write_bytes(z.read_bytes())
        print("cli_copied", target.name, "bytes", target.stat().st_size)

marker = home / ".ai-lab" / "antares" / "DOWNLOAD_OK"
marker.write_text(f"repo={repo}\npath={path}\n", encoding="utf-8")
print("marker", marker)
print("done")
