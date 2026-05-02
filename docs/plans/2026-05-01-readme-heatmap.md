# README Heatmap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate a Claude-orange GitHub-style contribution heatmap SVG from `assets.yaml` and keep it current via GitHub Actions when assets change and once per day as the rolling window advances.

**Architecture:** A single Python script (`scripts/build_readme_chart.py`) reads `shadow_assets/assets.yaml`, computes per-day word counts, and writes a hand-built SVG to `assets/chart.svg`. A GitHub Actions workflow runs the script when `assets.yaml` changes and once per day, then commits the SVG back if changed. The README embeds the SVG with a plain `![]()` tag.

**Tech Stack:** Python 3.10+, PyYAML (already a project dependency), GitHub Actions, plain SVG XML (no SVG libraries).

---

### Task 1: Pure data functions + tests

**Files:**
- Create: `scripts/build_readme_chart.py`
- Create: `tests/test_build_readme_chart.py`

**Step 1: Write the failing tests**

Create `tests/test_build_readme_chart.py`:

```python
import math
from datetime import date, timedelta
from scripts.build_readme_chart import (
    load_daily_counts,
    compute_stats,
    get_color_level,
    build_week_grid,
)

# ── load_daily_counts ──────────────────────────────────────────────────────────

def test_load_daily_counts_aggregates_by_date(tmp_path):
    yaml_file = tmp_path / "assets.yaml"
    yaml_file.write_text(
        "- {created_at: '2026-04-13'}\n"
        "- {created_at: '2026-04-13'}\n"
        "- {created_at: '2026-04-14'}\n"
    )
    counts = load_daily_counts(str(yaml_file))
    assert counts == {date(2026, 4, 13): 2, date(2026, 4, 14): 1}

def test_load_daily_counts_empty_file(tmp_path):
    yaml_file = tmp_path / "assets.yaml"
    yaml_file.write_text("[]")
    assert load_daily_counts(str(yaml_file)) == {}

# ── compute_stats ──────────────────────────────────────────────────────────────

def test_compute_stats_basic():
    counts = {date(2026, 4, 13): 33, date(2026, 4, 14): 11}
    study_days, total_words, avg = compute_stats(counts)
    assert study_days == 2
    assert total_words == 44
    assert avg == 22.0

def test_compute_stats_rounds_avg():
    counts = {date(2026, 4, 13): 10, date(2026, 4, 14): 11, date(2026, 4, 15): 12}
    _, total, avg = compute_stats(counts)
    assert total == 33
    assert avg == 11.0

def test_compute_stats_empty():
    study_days, total_words, avg = compute_stats({})
    assert study_days == 0
    assert total_words == 0
    assert avg == 0.0

# ── get_color_level ────────────────────────────────────────────────────────────

def test_get_color_level_zero_returns_zero():
    assert get_color_level(0, 33) == 0

def test_get_color_level_max_returns_four():
    assert get_color_level(33, 33) == 4

def test_get_color_level_bands():
    # max=100: bands are 1-25→1, 26-50→2, 51-75→3, 76-100→4
    assert get_color_level(1, 100) == 1
    assert get_color_level(25, 100) == 1
    assert get_color_level(26, 100) == 2
    assert get_color_level(50, 100) == 2
    assert get_color_level(51, 100) == 3
    assert get_color_level(75, 100) == 3
    assert get_color_level(76, 100) == 4

def test_get_color_level_max_zero_returns_zero():
    assert get_color_level(0, 0) == 0

# ── build_week_grid ────────────────────────────────────────────────────────────

def test_build_week_grid_returns_12_weeks():
    today = date(2026, 5, 1)  # Friday
    grid = build_week_grid({}, today)
    assert len(grid) == 12

def test_build_week_grid_each_week_has_7_days():
    today = date(2026, 5, 1)
    grid = build_week_grid({}, today)
    for week in grid:
        assert len(week) == 7

def test_build_week_grid_last_cell_is_today_or_later():
    today = date(2026, 5, 1)  # Friday = index 4 (Mon=0)
    grid = build_week_grid({}, today)
    last_week = grid[-1]
    # today is Friday; last_week[4] should be today
    assert last_week[4][0] == today

def test_build_week_grid_future_days_are_not_activity_cells():
    today = date(2026, 5, 1)  # Friday = index 4 (Mon=0)
    grid = build_week_grid({}, today)
    last_week = grid[-1]
    assert last_week[5][1] is None
    assert last_week[6][1] is None

def test_build_week_grid_assigns_levels():
    today = date(2026, 5, 1)
    counts = {date(2026, 4, 29): 16, date(2026, 4, 30): 16}
    grid = build_week_grid(counts, today)
    # Find the week containing Apr 29 (Tuesday = index 1)
    apr29_week = next(w for w in grid if w[1][0] == date(2026, 4, 29))
    assert apr29_week[1][1] == 4  # max=16, level=4
    assert apr29_week[2][1] == 4  # Apr 30, also 16

def test_build_week_grid_uses_window_max_not_historical_max():
    today = date(2026, 5, 1)
    counts = {
        date(2025, 12, 1): 1000,  # outside the visible 12-week window
        date(2026, 4, 29): 16,
    }
    grid = build_week_grid(counts, today)
    apr29_week = next(w for w in grid if w[1][0] == date(2026, 4, 29))
    assert apr29_week[1][1] == 4
```

**Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_build_readme_chart.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `build_readme_chart` doesn't exist yet.

**Step 3: Implement the data functions**

Create `scripts/build_readme_chart.py` with just the four functions (no SVG yet):

```python
import math
import yaml
from collections import defaultdict
from datetime import date, timedelta


def load_daily_counts(yaml_path: str) -> dict[date, int]:
    with open(yaml_path, encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []
    counts: dict[date, int] = defaultdict(int)
    for entry in entries:
        raw = entry.get("created_at")
        if raw:
            d = date.fromisoformat(str(raw))
            counts[d] += 1
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
    # Grid covers 12 week columns ending with today's current week.
    # Columns left→right = oldest→newest. Rows top→bottom = Mon→Sun.
    current_week_monday = today - timedelta(days=today.weekday())
    grid_start = current_week_monday - timedelta(weeks=11)
    rendered_dates = [
        grid_start + timedelta(days=offset)
        for offset in range(12 * 7)
        if grid_start + timedelta(days=offset) <= today
    ]
    max_count = max((daily_counts.get(d, 0) for d in rendered_dates), default=0)

    grid = []
    for week_idx in range(12):
        week_monday = grid_start + timedelta(weeks=week_idx)
        week = []
        for day_offset in range(7):  # Mon=0 … Sun=6
            d = week_monday + timedelta(days=day_offset)
            if d > today:
                level = None
            else:
                count = daily_counts.get(d, 0)
                level = get_color_level(count, max_count)
            week.append((d, level))
        grid.append(week)
    return grid
```

**Step 4: Run tests — all should pass**

```bash
python -m pytest tests/test_build_readme_chart.py -v
```

Expected: all 15 tests PASS.

**Step 5: Commit**

```bash
git add scripts/build_readme_chart.py tests/test_build_readme_chart.py
git commit -m "feat: add heatmap data functions with tests"
```

---

### Task 2: SVG rendering + smoke test

**Files:**
- Modify: `scripts/build_readme_chart.py` — add `build_svg()` and `main()`
- Modify: `tests/test_build_readme_chart.py` — add SVG smoke tests

**Step 1: Write SVG smoke tests**

Append to `tests/test_build_readme_chart.py`:

```python
from scripts.build_readme_chart import build_svg

def _make_grid():
    today = date(2026, 5, 1)
    counts = {
        date(2026, 4, 13): 33,
        date(2026, 4, 14): 11,
        date(2026, 4, 21): 26,
        date(2026, 4, 26): 5,
        date(2026, 4, 29): 16,
        date(2026, 4, 30): 16,
        date(2026, 5, 1):  20,
    }
    return counts, build_week_grid(counts, today)

def test_build_svg_is_valid_xml():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")

def test_build_svg_contains_stat_values():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    assert ">7<" in svg        # study_days
    assert ">127<" in svg      # total_words
    assert ">18.1<" in svg     # avg

def test_build_svg_contains_only_rendered_day_cells():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    # 11 full weeks plus Mon-Fri in the current week; future days are skipped.
    assert svg.count('class="day"') == 82

def test_build_svg_contains_orange_cells():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    # At least one active cell should use the orange palette
    assert "#f0883e" in svg or "#d36820" in svg
```

**Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_build_readme_chart.py::test_build_svg_is_valid_xml -v
```

Expected: `ImportError` — `build_svg` not defined yet.

**Step 3: Implement `build_svg()` and `main()`**

Append to `scripts/build_readme_chart.py`:

```python
# ── SVG constants ──────────────────────────────────────────────────────────────

CELL   = 11   # px, square cell
GAP    =  3   # px between cells
WEEKS  = 12
DAYS   =  7

# Colours
BG         = "#0d1117"
CARD_BG    = "#161b22"
BORDER     = "#30363d"
TEXT_PRI   = "#e6edf3"
TEXT_SEC   = "#6e7681"
ORANGE_HI  = "#f0883e"
LEVELS = ["#21262d", "#4a1f08", "#7d3a10", "#d36820", "#f0883e"]

# Layout
PAD        = 16
DAY_LABEL_W = 28
CARD_H     = 52
CARD_GAP   = 10
GRID_TOP   = PAD + CARD_H + 24   # below stat row
MONTH_ROW_H = 14
GRID_Y     = GRID_TOP + MONTH_ROW_H + 4

GRID_W = WEEKS * (CELL + GAP) - GAP          # 12*14-3 = 165
TOTAL_W = 720
GRID_H  = DAYS * (CELL + GAP) - GAP          # 7*14-3 = 95
LEGEND_H = 18
TOTAL_H = GRID_Y + GRID_H + LEGEND_H + PAD  # ~199

GRID_X = TOTAL_W - PAD - GRID_W  # right-align the newest week in the wide canvas
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

    # ── Root ──
    e(f'<svg xmlns="http://www.w3.org/2000/svg" width="{TOTAL_W}" height="{TOTAL_H}" '
      f'viewBox="0 0 {TOTAL_W} {TOTAL_H}">')
    e(f'  <rect width="{TOTAL_W}" height="{TOTAL_H}" rx="8" fill="{CARD_BG}"/>')

    # ── Stat cards ──
    card_w = (TOTAL_W - 2 * PAD - 2 * CARD_GAP) // 3
    cards = [
        (str(study_days), "study days", "total",       ORANGE_HI),
        (str(total_words), "words",     "committed",   TEXT_PRI),
        (str(avg),         "avg",       "per session", TEXT_PRI),
    ]
    for i, (val, label1, label2, val_color) in enumerate(cards):
        cx = PAD + i * (card_w + CARD_GAP)
        cy = PAD
        e(f'  <rect x="{cx}" y="{cy}" width="{card_w}" height="{CARD_H}" '
          f'rx="5" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>')
        # large value
        e(f'  <text x="{cx + 12}" y="{cy + 32}" '
          f'font-family="\'Segoe UI\',system-ui,sans-serif" font-size="20" '
          f'font-weight="600" fill="{val_color}">{val}</text>')
        # top label
        e(f'  <text x="{cx + 12}" y="{cy + 43}" '
          f'font-family="\'Segoe UI\',system-ui,sans-serif" font-size="9" '
          f'fill="{TEXT_PRI}">{label1}</text>')
        # bottom label
        e(f'  <text x="{cx + 12}" y="{cy + 50}" '
          f'font-family="\'Segoe UI\',system-ui,sans-serif" font-size="8" '
          f'fill="{TEXT_SEC}">{label2}</text>')

    # ── Month labels ──
    last_month = None
    for wi, week in enumerate(week_grid):
        first_day = week[0][0]   # Monday of this week
        if first_day.month != last_month:
            last_month = first_day.month
            mx = _x(wi)
            month_name = first_day.strftime("%b")
            e(f'  <text x="{mx}" y="{GRID_TOP + 10}" '
              f'font-family="\'Segoe UI\',system-ui,sans-serif" font-size="9" '
              f'fill="{TEXT_SEC}">{month_name}</text>')

    # ── Day axis labels ──
    label_days = {0: "Mon", 2: "Wed", 4: "Fri"}
    for di, label in label_days.items():
        ly = _y(di) + CELL - 1
        e(f'  <text x="{DAY_LABEL_X}" y="{ly}" '
          f'font-family="\'Segoe UI\',system-ui,sans-serif" font-size="8" '
          f'fill="{TEXT_SEC}" text-anchor="start">{label}</text>')

    # ── Heatmap cells ──
    for wi, week in enumerate(week_grid):
        for di, (d, level) in enumerate(week):
            if level is None:
                continue
            color = LEVELS[level]
            cx = _x(wi)
            cy = _y(di)
            e(f'  <rect class="day" x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" '
              f'rx="2" fill="{color}"/>')

    # ── Legend ──
    legend_y = GRID_Y + GRID_H + 10
    lx = TOTAL_W - PAD - len(LEVELS) * (CELL + 3) - 30
    e(f'  <text x="{lx}" y="{legend_y + CELL - 1}" '
      f'font-family="\'Segoe UI\',system-ui,sans-serif" font-size="8" '
      f'fill="{TEXT_SEC}">Less</text>')
    for i, color in enumerate(LEVELS):
        rx = lx + 28 + i * (CELL + 3)
        e(f'  <rect x="{rx}" y="{legend_y}" width="{CELL}" height="{CELL}" '
          f'rx="2" fill="{color}"/>')
    more_x = lx + 28 + len(LEVELS) * (CELL + 3) + 2
    e(f'  <text x="{more_x}" y="{legend_y + CELL - 1}" '
      f'font-family="\'Segoe UI\',system-ui,sans-serif" font-size="8" '
      f'fill="{TEXT_SEC}">More</text>')

    e("</svg>")
    return "\n".join(lines)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    import os
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    yaml_path = repo_root / "shadow_assets" / "assets.yaml"
    out_path  = repo_root / "assets" / "chart.svg"

    daily_counts = load_daily_counts(str(yaml_path))
    stats        = compute_stats(daily_counts)
    grid         = build_week_grid(daily_counts, date.today())
    svg          = build_svg(stats, grid)

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {out_path}  ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
```

**Step 4: Run all tests**

```bash
python -m pytest tests/test_build_readme_chart.py -v
```

Expected: all 19 tests PASS.

**Step 5: Manually verify the SVG renders**

```bash
python scripts/build_readme_chart.py
```

Open `assets/chart.svg` in a browser and confirm it looks like the mockup: dark background, three stat cards, orange heatmap cells, legend row.

**Step 6: Commit**

```bash
git add scripts/build_readme_chart.py tests/test_build_readme_chart.py assets/chart.svg
git commit -m "feat: generate README heatmap SVG"
```

---

### Task 3: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/update-chart.yml`

No tests for this task (workflow YAML is not unit-testable locally). Verify by pushing to GitHub and watching the Actions tab.

**Step 1: Create the workflow**

Create `.github/workflows/update-chart.yml`:

```yaml
name: Update README chart

on:
  push:
    branches: [main]
    paths:
      - 'shadow_assets/assets.yaml'
  schedule:
    - cron: '15 3 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: true

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install pyyaml

      - run: python scripts/build_readme_chart.py

      - name: Commit updated chart
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add assets/chart.svg
          if git diff --cached --quiet; then
            echo "No chart changes"
            exit 0
          fi
          git commit -m "chore: update README chart [skip ci]"
          git push
```

Key details:
- The `push.paths` filter runs the workflow when `assets.yaml` changes; the daily schedule keeps the chart aligned with today even when no new assets are committed.
- The chart update commit only changes `assets/chart.svg`, so it does not match the `push.paths` filter and does not loop.
- `[skip ci]` in the commit message is a GitHub convention that prevents the push from re-triggering the workflow (double-check your GitHub plan supports it; it works on all tiers).
- The explicit `git diff --cached --quiet` guard exits before `git push` when the SVG is unchanged.

**Step 2: Commit**

```bash
git add .github/workflows/update-chart.yml
git commit -m "ci: add GitHub Actions workflow to auto-update README chart"
```

---

### Task 4: Wire up README

**Files:**
- Modify: `README.md`

**Step 1: Add the chart embed**

Open `README.md`. After the opening paragraph (before `## Project Intent`), insert:

```markdown
![German study activity](assets/chart.svg)
```

**Step 2: Verify locally**

```bash
python scripts/build_readme_chart.py
```

Open `assets/chart.svg` in browser — confirm it looks correct.

**Step 3: Commit and push**

```bash
git add README.md assets/chart.svg
git commit -m "docs: embed heatmap chart in README"
git push
```

After the push, go to the GitHub Actions tab and confirm the `update-chart` workflow is present. This README-only push should be skipped by the `paths:` filter; that is correct because the chart was already generated locally.

To trigger a real end-to-end test: make any edit to `shadow_assets/assets.yaml` (or run a shadow-commit), then push. The workflow should run, regenerate the SVG, and commit it automatically.

---

### Done

The heatmap is live. Every future `shadow-commit` that modifies `assets.yaml` will trigger GitHub Actions, and the daily scheduled run will advance the rolling window even when no assets changed. In both cases, the workflow regenerates `assets/chart.svg` and commits it only when the file changes.
