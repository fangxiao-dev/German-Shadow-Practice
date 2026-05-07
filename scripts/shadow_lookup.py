from __future__ import annotations

from pathlib import Path
import argparse

try:
    from scripts.shadow_index import DEFAULT_ROOT, load_or_rebuild_asset_index, lookup_exact, lookup_related
except ModuleNotFoundError:
    from shadow_index import DEFAULT_ROOT, load_or_rebuild_asset_index, lookup_exact, lookup_related


def format_hit(hit: dict) -> str:
    english = hit.get("english", "")
    suffix = f" - {english}" if english else ""
    return f"{hit.get('id', '')} [{hit.get('type', '')}] {hit.get('content', '')}{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up exact and related shadow-practice assets.")
    parser.add_argument("query")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    index = load_or_rebuild_asset_index(args.root)
    exact_hits = lookup_exact(index, args.query)
    related_hits = lookup_related(index, args.query, limit=args.limit)

    print("Exact hits:")
    if exact_hits:
        for hit in exact_hits:
            print(f"- {format_hit(hit)}")
    else:
        print("- none")

    print("")
    print("Related hits:")
    if related_hits:
        for hit in related_hits:
            print(f"- {format_hit(hit)}")
    else:
        print("- none")


if __name__ == "__main__":
    main()
