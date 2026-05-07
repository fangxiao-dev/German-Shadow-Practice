from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import re
import yaml


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_RELATIVE_PATH = Path("shadow_assets") / "assets.yaml"
INDEX_RELATIVE_PATH = Path("shadow_assets") / "asset_index.json"
INDEX_SOURCE = ASSETS_RELATIVE_PATH.as_posix()
INDEX_FIELDS = ("content", "title", "collocation")
ITEM_FIELDS = (
    "id",
    "type",
    "title",
    "content",
    "english",
    "collocation",
    "status",
    "priority",
    "reset_count",
)
RELATED_STOPWORDS = {
    "aber",
    "als",
    "am",
    "an",
    "auf",
    "aus",
    "bei",
    "da",
    "das",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "es",
    "etw",
    "für",
    "im",
    "in",
    "ist",
    "mit",
    "nicht",
    "oder",
    "sein",
    "sich",
    "und",
    "von",
    "zu",
}


def load_yaml_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or []
    if not isinstance(data, list):
        raise ValueError(f"Expected a YAML list in {path}")
    return data


def normalize_for_match(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\wäöüÄÖÜß]+", " ", str(value).lower())).strip()


def tokenize_for_match(value: str) -> list[str]:
    return [token for token in normalize_for_match(value).split(" ") if token]


def terms_for_match(value: str) -> list[str]:
    tokens = [token for token in tokenize_for_match(value) if token not in RELATED_STOPWORDS]
    terms = list(tokens)
    terms.extend(f"{tokens[index]} {tokens[index + 1]}" for index in range(len(tokens) - 1))
    return terms


def compact_asset_item(asset: dict) -> dict:
    return {
        "id": str(asset.get("id", "")),
        "type": str(asset.get("type", "")),
        "title": str(asset.get("title", "")),
        "content": str(asset.get("content", "")),
        "english": str(asset.get("english", "")),
        "collocation": str(asset.get("collocation", "") or ""),
        "status": str(asset.get("status", "")),
        "priority": str(asset.get("priority", "")),
        "reset_count": asset.get("reset_count", 0) or 0,
    }


def _append_unique(mapping: dict[str, list[str]], key: str, asset_id: str) -> None:
    if not key or not asset_id:
        return
    values = mapping.setdefault(key, [])
    if asset_id not in values:
        values.append(asset_id)


def build_asset_index(assets: list[dict], generated_at: str | None = None) -> dict:
    exact: dict[str, list[str]] = {}
    tokens: dict[str, list[str]] = {}
    items: dict[str, dict] = {}

    for asset in assets:
        item = compact_asset_item(asset)
        asset_id = item["id"]
        if not asset_id:
            continue

        items[asset_id] = item

        for field_name in INDEX_FIELDS:
            value = item.get(field_name, "")
            normalized_value = normalize_for_match(value)
            _append_unique(exact, normalized_value, asset_id)
            for term in terms_for_match(value):
                _append_unique(tokens, term, asset_id)

    return {
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": INDEX_SOURCE,
        "exact": exact,
        "tokens": tokens,
        "items": items,
    }


def write_asset_index(root: Path = DEFAULT_ROOT, generated_at: str | None = None) -> dict:
    root = Path(root)
    assets = load_yaml_list(root / ASSETS_RELATIVE_PATH)
    index = build_asset_index(assets, generated_at=generated_at)
    index_path = root / INDEX_RELATIVE_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return index


def load_or_rebuild_asset_index(root: Path = DEFAULT_ROOT) -> dict:
    root = Path(root)
    index_path = root / INDEX_RELATIVE_PATH
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return write_asset_index(root)
        if isinstance(index, dict) and {"generated_at", "source", "exact", "tokens", "items"} <= set(index):
            return index
    return write_asset_index(root)


def lookup_exact(index: dict, target: str) -> list[dict]:
    normalized_target = normalize_for_match(target)
    asset_ids = index.get("exact", {}).get(normalized_target, [])
    items = index.get("items", {})
    return [dict(items[asset_id]) for asset_id in asset_ids if asset_id in items]


def lookup_related(index: dict, target: str, limit: int = 5) -> list[dict]:
    exact_ids = {item["id"] for item in lookup_exact(index, target)}
    query_terms = terms_for_match(target)
    if not query_terms:
        return []

    scores: Counter[str] = Counter()
    indexed_terms = index.get("tokens", {})
    for term in query_terms:
        for asset_id in indexed_terms.get(term, []):
            if asset_id not in exact_ids:
                scores[asset_id] += 1

    items = index.get("items", {})
    ordered_ids = list(items.keys())
    ranked_ids = sorted(
        (asset_id for asset_id in scores if asset_id in items),
        key=lambda asset_id: (-scores[asset_id], ordered_ids.index(asset_id)),
    )
    return [dict(items[asset_id]) for asset_id in ranked_ids[:limit]]
