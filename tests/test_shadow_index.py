from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import shadow_index


def write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sample_assets() -> list[dict]:
    return [
        {
            "id": "a-2026-04-13-001",
            "type": "phrase",
            "title": "in der breiten Masse",
            "content": "in der breiten Masse",
            "english": "among the broad public",
            "collocation": "in der breiten Masse ankommen",
            "status": "solid",
            "priority": "high",
            "reset_count": 2,
        },
        {
            "id": "a-2026-04-14-002",
            "type": "pattern",
            "title": "auf etw. vorbereitet sein",
            "content": "auf etw. vorbereitet sein",
            "english": "be prepared for something",
            "collocation": "",
            "status": "new",
            "priority": "normal",
            "reset_count": 0,
        },
    ]


def test_build_asset_index_contains_required_sections_and_metadata() -> None:
    index = shadow_index.build_asset_index(sample_assets(), generated_at="2026-05-07T10:50:00+02:00")

    assert index["generated_at"] == "2026-05-07T10:50:00+02:00"
    assert index["source"] == "shadow_assets/assets.yaml"
    assert set(index) == {"generated_at", "source", "exact", "tokens", "items"}
    assert index["items"]["a-2026-04-13-001"] == {
        "id": "a-2026-04-13-001",
        "type": "phrase",
        "title": "in der breiten Masse",
        "content": "in der breiten Masse",
        "english": "among the broad public",
        "collocation": "in der breiten Masse ankommen",
        "status": "solid",
        "priority": "high",
        "reset_count": 2,
    }


def test_exact_index_includes_content_title_and_collocation() -> None:
    index = shadow_index.build_asset_index(sample_assets(), generated_at="2026-05-07T10:50:00+02:00")

    assert index["exact"]["in der breiten masse"] == ["a-2026-04-13-001"]
    assert index["exact"]["in der breiten masse ankommen"] == ["a-2026-04-13-001"]
    assert index["exact"]["auf etw vorbereitet sein"] == ["a-2026-04-14-002"]


def test_normalize_for_match_handles_case_spacing_punctuation_and_german_characters() -> None:
    assert shadow_index.normalize_for_match("  AUF   etw. vorbereitet sein!  ") == "auf etw vorbereitet sein"
    assert shadow_index.normalize_for_match("Drohnen-Gefahren, äußerst groß") == "drohnen gefahren äußerst groß"


def test_lookup_exact_supports_multiple_ids_in_stable_order() -> None:
    assets = sample_assets() + [
        {
            "id": "a-2026-04-15-003",
            "type": "phrase",
            "title": "in der breiten Masse",
            "content": "in der breiten Masse",
            "english": "in the mass market",
            "collocation": "",
            "status": "new",
            "priority": "normal",
            "reset_count": 0,
        }
    ]
    index = shadow_index.build_asset_index(assets, generated_at="2026-05-07T10:50:00+02:00")

    hits = shadow_index.lookup_exact(index, "In der breiten Masse")

    assert [hit["id"] for hit in hits] == ["a-2026-04-13-001", "a-2026-04-15-003"]


def test_lookup_related_excludes_exact_hits_and_ranks_by_overlap() -> None:
    index = shadow_index.build_asset_index(sample_assets(), generated_at="2026-05-07T10:50:00+02:00")

    hits = shadow_index.lookup_related(index, "Deutschland ist auf Drohnen-Gefahren vorbereitet", limit=3)

    assert [hit["id"] for hit in hits] == ["a-2026-04-14-002"]


def test_load_or_rebuild_asset_index_recovers_missing_or_corrupt_index(tmp_path: Path) -> None:
    write_yaml(
        tmp_path / "shadow_assets" / "assets.yaml",
        "- id: a-2026-04-13-001\n"
        "  type: word\n"
        "  title: umsetzen\n"
        "  content: umsetzen\n",
    )
    index_path = tmp_path / "shadow_assets" / "asset_index.json"

    missing_index = shadow_index.load_or_rebuild_asset_index(tmp_path)
    assert missing_index["exact"]["umsetzen"] == ["a-2026-04-13-001"]
    assert index_path.exists()

    index_path.write_text("{not valid json", encoding="utf-8")
    rebuilt_index = shadow_index.load_or_rebuild_asset_index(tmp_path)
    assert rebuilt_index["exact"]["umsetzen"] == ["a-2026-04-13-001"]
    json.loads(index_path.read_text(encoding="utf-8"))


def test_load_or_rebuild_asset_index_raises_for_invalid_yaml(tmp_path: Path) -> None:
    write_yaml(tmp_path / "shadow_assets" / "assets.yaml", "not: a list\n")

    with pytest.raises(ValueError, match="Expected a YAML list"):
        shadow_index.load_or_rebuild_asset_index(tmp_path)
