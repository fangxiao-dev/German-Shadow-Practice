from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import json
import re
import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml_list(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or []
    if not isinstance(data, list):
        raise ValueError(f"Expected a YAML list in {path}")
    return data


def normalize_for_match(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\wäöüÄÖÜß]+", " ", value.casefold())).strip()


def tokenize_for_match(value: str) -> list[str]:
    return [token for token in normalize_for_match(value).split(" ") if token]


def load_transcript_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    transcript_only = text.split("\n---", 1)[0]
    return [line.strip() for line in transcript_only.splitlines() if line.strip()]


def find_example_sentence(lines: list[str], raw: str, target: str) -> str:
    candidates = [value for value in [raw, target] if value]
    normalized_lines = [(line, normalize_for_match(line)) for line in lines]

    for candidate in candidates:
        normalized_candidate = normalize_for_match(candidate)
        if not normalized_candidate:
            continue
        for original_line, normalized_line in normalized_lines:
            if normalized_candidate in normalized_line:
                return original_line

    best_line = ""
    best_score = 0.0
    for candidate in candidates:
        candidate_tokens = tokenize_for_match(candidate)
        if not candidate_tokens:
            continue
        candidate_token_set = set(candidate_tokens)
        for original_line, _ in normalized_lines:
            line_tokens = set(tokenize_for_match(original_line))
            if not line_tokens:
                continue
            overlap = len(candidate_token_set & line_tokens)
            score = overlap / len(candidate_token_set)
            if score > best_score:
                best_score = score
                best_line = original_line

    if best_score >= 0.6:
        return best_line

    return ""


def parse_session_file(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    source_match = re.search(r"- source: `([^`]+)`", text)
    transcript_source = source_match.group(1) if source_match else ""

    sections: dict[str, dict] = {}
    current_section = None
    current_item: dict[str, str] | None = None

    def flush_current_item() -> None:
        nonlocal current_item
        if current_item and current_item.get("target"):
            sections[current_item["target"]] = current_item
        current_item = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            flush_current_item()
            current_section = line[3:].strip()
            continue

        if current_section not in {
            "Must Keep Candidates",
            "Recommendations",
        }:
            continue

        raw_match = re.match(r"- raw: `(.+)`", line)
        if raw_match:
            flush_current_item()
            current_item = {
                "raw": raw_match.group(1),
                "source_transcript": transcript_source,
                "section": current_section,
            }
            continue

        if current_item is None:
            continue

        target_match = re.match(r"\s+target: `(.+)`", line)
        if target_match:
            current_item["target"] = target_match.group(1)
            continue

        type_match = re.match(r"\s+type: `(.+)`", line)
        if type_match:
            current_item["type"] = type_match.group(1)
            continue

        collocation_match = re.match(r"\s+collocation[s]?: `(.+)`", line)
        if collocation_match:
            current_item["collocation"] = collocation_match.group(1)
            continue

        english_match = re.match(r"\s+english: `(.+)`", line)
        if english_match:
            current_item["english"] = english_match.group(1)
            continue

        transcript_sentence_match = re.match(r"\s+transcript_sentence: `(.+)`", line)
        if transcript_sentence_match:
            current_item["transcript_sentence"] = transcript_sentence_match.group(1)

    flush_current_item()

    return sections


def build_session_lookup(sessions_dir: Path) -> dict[str, dict[str, dict]]:
    lookup: dict[str, dict[str, dict]] = {}
    for path in sessions_dir.glob("*.md"):
        if path.name == "README.md":
            continue
        lookup[path.as_posix().replace("/", "\\")] = parse_session_file(path)
    return lookup


def iso_week_label(date_str: str) -> str:
    dt = datetime.fromisoformat(date_str[:10])
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def session_sort_key(session_ref: str) -> str:
    name = Path(session_ref).name
    stem = Path(name).stem
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{4}", stem):
        return stem
    return ""


def build_dashboard_data(root: Path = ROOT) -> dict:
    root = Path(root)
    assets_path = root / "shadow_assets" / "assets.yaml"
    state_path = root / "shadow_reviews" / "review_state.yaml"
    sessions_dir = root / "shadow_sessions"

    assets = load_yaml_list(assets_path)
    state = load_yaml_list(state_path)
    state_by_id = {item["id"]: item for item in state}
    session_lookup = build_session_lookup(sessions_dir)
    transcript_cache: dict[str, list[str]] = {}

    enriched_items: list[dict] = []
    for asset in assets:
        item = dict(asset)
        current_state = state_by_id.get(asset["id"], {})
        item["status"] = current_state.get("status", asset.get("status"))
        item["priority"] = current_state.get("priority", asset.get("priority"))
        item["review_count"] = current_state.get("review_count", asset.get("review_count"))
        item["reset_count"] = current_state.get("reset_count", asset.get("reset_count", 0))
        item["last_reviewed_at"] = current_state.get("last_reviewed_at", asset.get("last_reviewed_at"))
        item["mistake_note"] = current_state.get("mistake_note", asset.get("mistake_note"))
        item["week"] = iso_week_label(asset["created_at"])
        session_items = session_lookup.get(str(root / asset["source_session"]), {})
        session_info = session_items.get(asset["content"], {})
        item["raw"] = session_info.get("raw", asset.get("raw", ""))
        item["source_transcript"] = session_info.get("source_transcript", "")
        item["english"] = asset.get("english", session_info.get("english", ""))
        item["collocation"] = asset.get("collocation", session_info.get("collocation", ""))
        if asset.get("transcript_sentence"):
            item["example_sentence"] = asset["transcript_sentence"]
            enriched_items.append(item)
            continue

        if session_info.get("transcript_sentence"):
            item["example_sentence"] = session_info["transcript_sentence"]
            enriched_items.append(item)
            continue

        transcript_path = item["source_transcript"]
        if transcript_path:
            transcript_file = Path(transcript_path)
            if not transcript_file.is_absolute():
                transcript_file = root / transcript_file
            transcript_lines = transcript_cache.setdefault(
                transcript_path,
                load_transcript_lines(transcript_file),
            )
            item["example_sentence"] = find_example_sentence(
                transcript_lines,
                item["raw"],
                item["content"],
            )
        else:
            item["example_sentence"] = ""
        enriched_items.append(item)

    enriched_items.sort(key=lambda x: (x["created_at"], x["id"]), reverse=True)

    weekly: dict[str, list[dict]] = defaultdict(list)
    for item in enriched_items:
        weekly[item["week"]].append(item)

    weekly_groups = [
        {
            "week": week,
            "count": len(items),
            "items": items,
        }
        for week, items in sorted(weekly.items(), reverse=True)
    ]

    summary = {
        "total_items": len(enriched_items),
        "status_counts": dict(Counter(item["status"] for item in enriched_items)),
        "type_counts": dict(Counter(item["type"] for item in enriched_items)),
        "latest_created_at": enriched_items[0]["created_at"] if enriched_items else None,
    }

    latest_session_key = max((session_sort_key(item["source_session"]) for item in enriched_items), default="")
    if latest_session_key:
        recent_items = [
            item
            for item in enriched_items
            if session_sort_key(item["source_session"]) == latest_session_key
        ]
        recent_items.sort(key=lambda x: (x["created_at"], x["id"]), reverse=True)
    else:
        recent_items = enriched_items[:12]

    recent_summary = {
        "total_items": len(recent_items),
        "status_counts": dict(Counter(item["status"] for item in recent_items)),
        "type_counts": dict(Counter(item["type"] for item in recent_items)),
        "latest_session": recent_items[0]["source_session"] if recent_items else None,
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "recent_summary": recent_summary,
        "all_items": enriched_items,
        "recent_items": recent_items,
        "weekly_groups": weekly_groups,
    }


def main() -> None:
    output_path = ROOT / "dashboard" / "data" / "dashboard-data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_data()
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
