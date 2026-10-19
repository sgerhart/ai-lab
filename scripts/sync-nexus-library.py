#!/usr/bin/env python3
"""Copy new Nexus books from iCloud Information into ~/.ai-lab/nexus.

Dry-run unless --apply is passed. Does not delete files and does not replace
the Nexus page itself.

  ./scripts/sync-nexus-library.py
  ./scripts/sync-nexus-library.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_library import scan_served_library, sync_icloud_library  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync the iCloud Nexus library into the local mirror")
    parser.add_argument("--apply", action="store_true", help="Copy files. Without this flag, only list them.")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds to allow for each library folder")
    args = parser.parse_args()

    result = sync_icloud_library(apply=args.apply, timeout_s=args.timeout)
    copied = result.get("copied") or []
    errors = result.get("errors") or []
    mode = "Copied" if args.apply else "Would copy"
    print(f"{mode} {len(copied)} book file(s).")
    for name in copied:
        print(f"  {name}")
    for error in errors:
        print(f"Error: {error}", file=sys.stderr)
    if args.apply and result.get("ok"):
        library = scan_served_library()
        print(f"Library scan sees {library['count']} book(s).")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
