"""CLI script to compile tasks and generate immutable bundles."""

from __future__ import annotations

import sys
from pathlib import Path

# Add packages to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "services"))
sys.path.insert(0, str(ROOT))

from packages.datasets import DatasetPackager, DatasetValidator


def main() -> int:
    print("Compiling curated Python tasks and immutable test bundles...")
    packager = DatasetPackager()
    manifest, tasks = packager.package_dataset("dataset_v1.json")
    print(f"Compiled {len(tasks)} tasks across splits: {manifest.splits}")
    print(f"Manifest SHA-256: {manifest.manifest_hash}")

    print("\nRunning dataset verification...")
    validator = DatasetValidator()
    report = validator.validate_dataset(tasks)

    if not report.is_valid:
        print("FAIL: Dataset validation failed!", file=sys.stderr)
        for err in report.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("PASS: Dataset validation succeeded!")
    print(f"  - Total tasks: {report.total_tasks}")
    print(f"  - Splits: {report.splits_count}")
    print(f"  - Distinct families: {len(report.families_count)}")
    print(f"  - Family leaks: {len(report.family_leaks)} (disjointness confirmed)")
    print(f"  - Failed reference solutions: {len(report.failed_reference_solutions)}")
    print(f"  - Corrupted bundles: {len(report.corrupted_bundles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
