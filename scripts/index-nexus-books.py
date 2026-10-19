#!/usr/bin/env python3
"""Knowledge Nexus Book Indexer CLI (IWO-105).

Indexes EPUB and PDF books from Knowledge Nexus into Qdrant for semantic search.
Usage:
  ./scripts/index-nexus-books.py --book "04_Books_Library/Software_Engineering/Looks_Good_to_Me_.pdf"
  ./scripts/index-nexus-books.py --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.nexus_rag import (  # noqa: E402
    NexusRagStore,
    index_book,
    index_served_documents,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Index Nexus library books into Qdrant")
    parser.add_argument("--book", help="Relative path of a specific book to index")
    parser.add_argument("--all", action="store_true", help="Index all books in 04_Books_Library")
    args = parser.parse_args()

    store = NexusRagStore()
    if not store.ensure_collection():
        print(f"Error: Unable to connect to Qdrant at {store.url} or initialize collection.", file=sys.stderr)
        return 1

    if args.book:
        print(f"Indexing book: {args.book} ...")
        count = index_book(args.book, store=store)
        print(f"Successfully indexed {count} chunks for '{args.book}' into Qdrant.")
        return 0

    if args.all:
        print("Indexing all books in Knowledge Nexus 04_Books_Library into Qdrant...")
        results = index_served_documents(store=store)
        total_chunks = sum(results.values())
        print(f"\nIndexed {len(results)} books ({total_chunks} total chunks).")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
