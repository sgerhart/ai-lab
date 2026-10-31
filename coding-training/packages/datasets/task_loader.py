"""Task loading and dataset query utilities."""

from __future__ import annotations

import json
from pathlib import Path

from packages.contracts import DatasetManifest, Split, Task


class TaskLoader:
    """Loads and queries tasks from disk or manifest."""

    def __init__(self, root_dir: Path | str | None = None):
        if root_dir is None:
            # Default to coding-training/datasets
            self.root_dir = Path(__file__).resolve().parents[2] / "datasets"
        else:
            self.root_dir = Path(root_dir)
        self.manifests_dir = self.root_dir / "manifests"
        self.bundles_dir = self.root_dir / "test_bundles"

    def load_manifest(self, manifest_name: str = "dataset_v1.json") -> DatasetManifest:
        manifest_path = self.manifests_dir / manifest_name
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return DatasetManifest(**data)

    def load_tasks(self, manifest_name: str = "dataset_v1.json") -> list[Task]:
        manifest_path = self.manifests_dir / manifest_name
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        tasks_raw = data.get("tasks", [])
        return [Task(**t) for t in tasks_raw]

    def get_tasks_by_split(self, split: Split, manifest_name: str = "dataset_v1.json") -> list[Task]:
        return [t for t in self.load_tasks(manifest_name) if t.split == split]

    def load_bundle_content(self, bundle_sha256: str) -> dict[str, object]:
        bundle_path = self.bundles_dir / f"{bundle_sha256}.json"
        if not bundle_path.exists():
            raise FileNotFoundError(f"Test bundle not found: {bundle_path}")
        return json.loads(bundle_path.read_text(encoding="utf-8"))

    def load_reference_solutions(self) -> dict[str, str]:
        solutions_dir = self.root_dir / "reference_solutions"
        if not solutions_dir.exists():
            return {}
        solutions: dict[str, str] = {}
        for sol_file in solutions_dir.glob("*.py"):
            solutions[sol_file.stem] = sol_file.read_text(encoding="utf-8")
        return solutions
