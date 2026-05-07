from __future__ import annotations

from pathlib import Path
import argparse

try:
    from scripts.shadow_index import DEFAULT_ROOT, write_asset_index
except ModuleNotFoundError:
    from shadow_index import DEFAULT_ROOT, write_asset_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the generated shadow asset lookup index.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    index = write_asset_index(args.root)
    print(
        "Rebuilt shadow asset index "
        f"(assets={len(index['items'])}, exact_keys={len(index['exact'])}, token_keys={len(index['tokens'])})"
    )


if __name__ == "__main__":
    main()
