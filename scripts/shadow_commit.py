from __future__ import annotations

from datetime import datetime
from urllib.parse import quote
from pathlib import Path
import argparse
import json
import re
import socket
import subprocess
import sys
import webbrowser
import yaml


DEFAULT_ROOT = Path(r"E:\Personal\学德语")
DEFAULT_DASHBOARD_PORT = 4173
SESSION_SECTIONS = {
    "Must Keep Candidates",
    "Recommendations",
}


def load_yaml_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or []
    if not isinstance(data, list):
        raise ValueError(f"Expected a YAML list in {path}")
    return data


def dump_yaml_list(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def normalize_for_match(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\wäöüÄÖÜß]+", " ", value.casefold())).strip()


def parse_session_file(path: Path) -> tuple[str, list[dict[str, str]]]:
    text = path.read_text(encoding="utf-8")
    source_match = re.search(r"- source: `([^`]+)`", text)
    transcript_source = source_match.group(1) if source_match else ""

    items: list[dict[str, str]] = []
    current_section = None
    current_item: dict[str, str] | None = None

    def flush_current_item() -> None:
        nonlocal current_item
        if current_item and current_item.get("target"):
            items.append(current_item)
        current_item = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            flush_current_item()
            current_section = line[3:].strip()
            continue

        if current_section not in SESSION_SECTIONS:
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
    return transcript_source, items


def choose_session_path(root: Path, explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        return explicit_path

    sessions = sorted(
        (path for path in (root / "shadow_sessions").glob("*.md") if path.name != "README.md"),
        key=lambda path: path.name,
    )
    if not sessions:
        raise FileNotFoundError("No shadow session files found")
    return sessions[-1]


def next_asset_id(assets: list[dict], created_at: str) -> str:
    max_serial = 0
    for asset in assets:
        match = re.match(r"a-\d{4}-\d{2}-\d{2}-(\d+)$", str(asset.get("id", "")))
        if match:
            max_serial = max(max_serial, int(match.group(1)))
    return f"a-{created_at}-{max_serial + 1:03d}"


def relative_session_path(root: Path, session_path: Path) -> str:
    return session_path.relative_to(root).as_posix()


def ensure_reset_count(record: dict) -> None:
    if "reset_count" not in record or record["reset_count"] is None:
        record["reset_count"] = 0


def sync_state_from_asset(asset: dict, state_record: dict | None = None) -> dict:
    record = dict(state_record or {})
    record["id"] = asset["id"]
    record["status"] = asset["status"]
    record["priority"] = asset["priority"]
    record["review_count"] = asset["review_count"]
    record["reset_count"] = asset["reset_count"]
    record["last_reviewed_at"] = asset["last_reviewed_at"]
    record["mistake_note"] = asset["mistake_note"]
    return record


def append_commit_log(log_path: Path, session_ref: str, committed_at: str, added_count: int, reset_count: int) -> None:
    lines = [
        "",
        f"## {committed_at[:10]} commit",
        "",
        f"Committed the reviewed items from `{session_ref}` into the durable asset store.",
        "",
    ]
    if added_count:
        lines.append(f"- Added {added_count} new assets with `status: new`")
    if reset_count:
        lines.append(f"- Reset {reset_count} existing assets to `new` after repeated capture hits")
    if not added_count and not reset_count:
        lines.append("- No durable changes were required")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def is_dashboard_port_in_use(port: int = DEFAULT_DASHBOARD_PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def run_dashboard_launcher(root: Path, no_open: bool) -> None:
    launcher_path = root / "scripts" / "start_shadow_dashboard.ps1"
    command = [
        "pwsh",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(launcher_path),
    ]
    if no_open:
        command.append("-NoOpen")
    subprocess.run(command, check=True, cwd=root)


def open_dashboard_url(url: str) -> None:
    webbrowser.open(url)


def read_dashboard_version(root: Path) -> str:
    data_path = root / "dashboard" / "data" / "dashboard-data.json"
    if not data_path.exists():
        return datetime.now().strftime("%Y%m%d%H%M%S")
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    generated_at = payload.get("generated_at") or datetime.now().strftime("%Y%m%d%H%M%S")
    return str(generated_at)


def build_dashboard_url(root: Path, port: int = DEFAULT_DASHBOARD_PORT) -> str:
    version = quote(read_dashboard_version(root), safe="")
    return f"http://localhost:{port}/?v={version}"


def post_commit_dashboard_followup(root: Path, no_open: bool = False) -> None:
    if is_dashboard_port_in_use():
        if not no_open:
            open_dashboard_url(build_dashboard_url(root))
        return
    run_dashboard_launcher(root, no_open=no_open)


def commit_session(
    root: Path = DEFAULT_ROOT,
    session_path: Path | None = None,
    committed_at: str | None = None,
    launch_dashboard: bool = False,
    no_open: bool = False,
) -> dict[str, int | str]:
    root = Path(root)
    session_path = choose_session_path(root, Path(session_path) if session_path is not None else None)
    committed_at = committed_at or datetime.now().strftime("%Y-%m-%d %H:%M")
    created_at = session_path.stem[:10]

    assets_path = root / "shadow_assets" / "assets.yaml"
    state_path = root / "shadow_reviews" / "review_state.yaml"
    log_path = root / "shadow_reviews" / "review_log.md"

    assets = load_yaml_list(assets_path)
    state = load_yaml_list(state_path)
    state_by_id = {item["id"]: item for item in state}

    for asset in assets:
        ensure_reset_count(asset)
    for item in state:
        ensure_reset_count(item)

    _, session_items = parse_session_file(session_path)
    assets_by_target = {normalize_for_match(asset["content"]): asset for asset in assets}

    added_count = 0
    reset_count = 0
    session_ref = relative_session_path(root, session_path)

    for session_item in session_items:
        target = session_item["target"]
        normalized_target = normalize_for_match(target)
        existing_asset = assets_by_target.get(normalized_target)

        if existing_asset is not None:
            existing_asset["title"] = target
            existing_asset["content"] = target
            existing_asset["type"] = session_item.get("type", existing_asset["type"])
            existing_asset["english"] = session_item.get("english", existing_asset.get("english", ""))
            existing_asset["transcript_sentence"] = session_item.get(
                "transcript_sentence",
                existing_asset.get("transcript_sentence", ""),
            )
            if session_item.get("collocation"):
                existing_asset["collocation"] = session_item["collocation"]
            existing_asset["source_session"] = session_ref
            existing_asset["status"] = "new"
            ensure_reset_count(existing_asset)
            existing_asset["reset_count"] += 1

            existing_state = state_by_id.get(existing_asset["id"])
            synced_state = sync_state_from_asset(existing_asset, existing_state)
            state_by_id[existing_asset["id"]] = synced_state
            reset_count += 1
            continue

        new_asset = {
            "id": next_asset_id(assets, created_at),
            "type": session_item["type"],
            "title": target,
            "content": target,
            "english": session_item.get("english", ""),
            "transcript_sentence": session_item.get("transcript_sentence", ""),
            "collocation": session_item.get("collocation", ""),
            "source_session": session_ref,
            "created_at": created_at,
            "status": "new",
            "priority": "normal",
            "review_count": 0,
            "reset_count": 0,
            "last_reviewed_at": None,
            "mistake_note": None,
        }
        assets.append(new_asset)
        assets_by_target[normalized_target] = new_asset
        state_by_id[new_asset["id"]] = sync_state_from_asset(new_asset)
        added_count += 1

    dump_yaml_list(assets_path, assets)
    ordered_state = [state_by_id[asset["id"]] for asset in assets]
    dump_yaml_list(state_path, ordered_state)
    append_commit_log(log_path, session_ref, committed_at, added_count, reset_count)

    if launch_dashboard:
        post_commit_dashboard_followup(root, no_open=no_open)

    return {
        "session": session_ref,
        "added_count": added_count,
        "reset_count": reset_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Commit a reviewed shadow session into durable assets.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--session", type=Path, default=None)
    parser.add_argument("--committed-at", default=None)
    parser.add_argument("--no-dashboard", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    result = commit_session(
        root=args.root,
        session_path=args.session,
        committed_at=args.committed_at,
        launch_dashboard=not args.no_dashboard,
        no_open=args.no_open,
    )
    print(
        f"Committed {result['session']} "
        f"(added={result['added_count']}, reset={result['reset_count']})"
    )


if __name__ == "__main__":
    main()
