"""Training entrypoint that refuses to start until a human authorizes an experiment."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ai-lab training (refuses by default)")
    parser.add_argument("--download-dataset", action="store_true")
    parser.add_argument("--start", action="store_true")
    args = parser.parse_args(argv)
    print(
        "Refusing to train or download datasets. Authorize a specific experiment in a work order first.",
        file=sys.stderr,
    )
    if args.download_dataset or args.start:
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
