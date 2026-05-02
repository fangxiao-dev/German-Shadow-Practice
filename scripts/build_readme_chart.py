from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta

import yaml


def load_daily_counts(yaml_path: str) -> dict[date, int]:
    with open(yaml_path, encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []

    counts: dict[date, int] = defaultdict(int)
    for entry in entries:
        raw = entry.get("created_at")
        if raw:
            counts[date.fromisoformat(str(raw))] += 1
    return dict(counts)


def compute_stats(daily_counts: dict[date, int]) -> tuple[int, int, float]:
    study_days = len(daily_counts)
    total_words = sum(daily_counts.values())
    avg = round(total_words / study_days, 1) if study_days else 0.0
    return study_days, total_words, avg


def get_color_level(count: int, max_count: int) -> int:
    if count == 0 or max_count == 0:
        return 0
    return min(4, math.ceil(count / max_count * 4))


def build_week_grid(
    daily_counts: dict[date, int], today: date
) -> list[list[tuple[date, int | None]]]:
    # Columns left-to-right = oldest-to-newest. Rows top-to-bottom = Mon-Sun.
    current_week_monday = today - timedelta(days=today.weekday())
    grid_start = current_week_monday - timedelta(weeks=11)
    rendered_dates = [
        grid_start + timedelta(days=offset)
        for offset in range(12 * 7)
        if grid_start + timedelta(days=offset) <= today
    ]
    max_count = max((daily_counts.get(d, 0) for d in rendered_dates), default=0)

    grid: list[list[tuple[date, int | None]]] = []
    for week_idx in range(12):
        week_monday = grid_start + timedelta(weeks=week_idx)
        week: list[tuple[date, int | None]] = []
        for day_offset in range(7):
            d = week_monday + timedelta(days=day_offset)
            if d > today:
                level = None
            else:
                level = get_color_level(daily_counts.get(d, 0), max_count)
            week.append((d, level))
        grid.append(week)
    return grid


CELL = 13
GAP = 4
WEEKS = 12
DAYS = 7

BG = "#0d1117"
CARD_BG = "#161b22"
BORDER = "#30363d"
TEXT_PRI = "#e6edf3"
TEXT_SEC = "#6e7681"
TEXT_MUTED = "#484f58"
ORANGE_HI = "#f0883e"
LEVELS = ["#21262d", "#4a1f08", "#7d3a10", "#d36820", "#f0883e"]
FONT = "Segoe UI Variable,Segoe UI,system-ui,sans-serif"

PAD = 18
DAY_LABEL_W = 28
CARD_GAP = 6
CARD_W = 120
CARD_H = 42
GRID_W = WEEKS * (CELL + GAP) - GAP
GRID_H = DAYS * (CELL + GAP) - GAP
TOTAL_W = 440
TOTAL_H = 250
GRID_X = PAD + DAY_LABEL_W
GRID_Y = 116
MONTH_Y = 101
DAY_LABEL_X = GRID_X - DAY_LABEL_W


def _x(week_idx: int) -> int:
    return GRID_X + week_idx * (CELL + GAP)


def _y(day_idx: int) -> int:
    return GRID_Y + day_idx * (CELL + GAP)


def build_svg(
    stats: tuple[int, int, float],
    week_grid: list[list[tuple[date, int | None]]],
) -> str:
    study_days, total_words, avg = stats
    lines: list[str] = []

    def e(s: str) -> None:
        lines.append(s)

    e(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{TOTAL_W}" '
        f'height="{TOTAL_H}" viewBox="0 0 {TOTAL_W} {TOTAL_H}">'
    )
    e(f'  <rect width="{TOTAL_W}" height="{TOTAL_H}" rx="8" fill="{CARD_BG}"/>')
    e(
        f'  <text x="{PAD}" y="34" font-family="{FONT}" '
        f'font-size="18" font-weight="650" fill="{TEXT_PRI}">German study</text>'
    )
    e(
        f'  <text x="{PAD}" y="51" font-family="{FONT}" '
        f'font-size="10" fill="{TEXT_SEC}">12-week shadow practice</text>'
    )

    stat_rows = [
        ("Study days", str(study_days)),
        ("Words", str(total_words)),
        ("Avg/session", str(avg)),
    ]
    for idx, (label, value) in enumerate(stat_rows):
        x = PAD + idx * (CARD_W + CARD_GAP)
        y = 66
        e(
            f'  <rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" '
            f'rx="6" fill="#21262d" opacity="0.9"/>'
        )
        e(
            f'  <text x="{x + 9}" y="{y + 16}" font-family="{FONT}" '
            f'font-size="10" fill="{TEXT_SEC}">{label}</text>'
        )
        e(
            f'  <text x="{x + 9}" y="{y + 34}" font-family="{FONT}" '
            f'font-size="16" font-weight="700" fill="{TEXT_PRI}">{value}</text>'
        )

    last_month = None
    for week_idx, week in enumerate(week_grid):
        first_day = week[0][0]
        if first_day.month != last_month:
            last_month = first_day.month
            e(
                f'  <text x="{_x(week_idx)}" y="{MONTH_Y}" '
                f'font-family="{FONT}" font-size="10" '
                f'fill="{TEXT_SEC}">{first_day.strftime("%b")}</text>'
            )

    for day_idx, label in {0: "Mon", 2: "Wed", 4: "Fri"}.items():
        e(
            f'  <text x="{DAY_LABEL_X}" y="{_y(day_idx) + CELL - 1}" '
            f'font-family="{FONT}" font-size="9" '
            f'fill="{TEXT_SEC}" text-anchor="start">{label}</text>'
        )

    for week_idx, week in enumerate(week_grid):
        for day_idx, (_d, level) in enumerate(week):
            if level is None:
                continue
            e(
                f'  <rect class="day" x="{_x(week_idx)}" y="{_y(day_idx)}" '
                f'width="{CELL}" height="{CELL}" rx="2" fill="{LEVELS[level]}"/>'
            )

    legend_y = GRID_Y + GRID_H + 14
    legend_right = GRID_X + GRID_W
    more_w = 26
    cell_group_w = len(LEVELS) * (CELL + 3) - 3
    cells_x = legend_right - more_w - 6 - cell_group_w
    less_x = cells_x - 30
    e(
        f'  <text x="{less_x}" y="{legend_y + CELL - 1}" '
        f'font-family="{FONT}" font-size="9" '
        f'fill="{TEXT_SEC}">Less</text>'
    )
    for i, color in enumerate(LEVELS):
        e(
            f'  <rect x="{cells_x + i * (CELL + 3)}" y="{legend_y}" '
            f'width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    e(
        f'  <text x="{legend_right}" y="{legend_y + CELL - 1}" '
        f'font-family="{FONT}" font-size="9" '
        f'fill="{TEXT_SEC}" text-anchor="end">More</text>'
    )

    e("</svg>")
    return "\n".join(lines)


def main() -> None:
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    yaml_path = repo_root / "shadow_assets" / "assets.yaml"
    out_path = repo_root / "assets" / "chart.svg"

    daily_counts = load_daily_counts(str(yaml_path))
    stats = compute_stats(daily_counts)
    grid = build_week_grid(daily_counts, date.today())
    svg = build_svg(stats, grid)

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {out_path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
