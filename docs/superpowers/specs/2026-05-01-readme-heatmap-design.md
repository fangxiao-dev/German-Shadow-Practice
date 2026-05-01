# README Heatmap Design

**Date:** 2026-05-01  
**Status:** Approved

## What We're Building

A self-updating SVG chart embedded in README.md for public GitHub display. It shows German shadow-practice activity at a glance: how many days studied, how many words committed, and when sessions happened relative to today.

## Visual Design

Style: GitHub dark theme (`#0d1117` accents on `#161b22` card background), Segoe UI Variable / Segoe UI / system-ui font stack, Claude orange heatmap palette.

**Layout** — compact README card:
- Left rail: title, subtitle, and three stacked stats
- Right panel: centered 12-week heatmap, month labels, weekday labels, and legend
- A subtle vertical divider separates metrics from the activity grid

**Stats** — three compact rows:
- Study days (total unique days in `assets.yaml`, highlighted orange)
- Words committed (total asset count, white)
- Avg words per session (total ÷ study days, white)

**Heatmap grid** — GitHub contribution-graph format:
- 12 weeks of columns, newest week at the right, current week partial through today
- 7 rows (Mon–Sun), left axis labels on Mon/Wed/Fri
- Month labels above the column group where a month begins
- Each cell: 13×13 px, 4 px gap, 2 px border-radius
- Future dates in the current week are not rendered as empty activity cells; they are skipped or transparent so they are not confused with past no-study days.
- Empty cells: `#21262d`; active cells in 4 intensity steps keyed to word count quartiles across the window:
  - Level 1 (1–25% of window max): `#4a1f08`
  - Level 2 (26–50%): `#7d3a10`
  - Level 3 (51–75%): `#d36820`
  - Level 4 (76–100%): `#f0883e`
- Legend row, right-aligned, below the grid: "Less ░▒▓█ More"

**README embed:**
```markdown
![German study activity](assets/chart.svg)
```

## Data Source

`shadow_assets/assets.yaml` — one entry per committed word/phrase/pattern with a `created_at: 'YYYY-MM-DD'` field. The script aggregates count by date. No git log needed.

**Computed fields:**
- `study_days`: count of unique `created_at` dates
- `total_words`: len(all entries)
- `avg_per_session`: total_words / study_days, rounded to 1 decimal
- `daily_counts`: dict mapping date → count, for the rolling 12-week window

**Color thresholds:** computed from the max daily count in the 12-week window, divided into four equal bands. A day with count `c` gets level `ceil(c / max * 4)`, clamped to 1–4. If the window has no activity, all cells render as empty.

## Files

| Path | Role |
|------|------|
| `scripts/build_readme_chart.py` | Reads YAML, computes data, writes SVG |
| `assets/chart.svg` | Generated output, committed to repo |
| `.github/workflows/update-chart.yml` | GitHub Actions workflow |
| `README.md` | Embeds the SVG with a `![]()` tag |

## Script Behaviour (`build_readme_chart.py`)

1. Load `shadow_assets/assets.yaml` with PyYAML
2. Count entries per `created_at` date
3. Compute stat row values
4. Determine 12-week grid: start at the Monday 11 weeks before today's week; render only dates through `today`
5. Compute `max_count` from rendered dates in that 12-week window only, ignoring older historical counts and future dates
6. Map each rendered date in window to an intensity level (0–4): level = ceil(count / max_count * 4), or 0 if empty
7. Render SVG as a string — hand-built XML, no external SVG library needed
8. Create `assets/` directory if it does not exist, then write `assets/chart.svg`

SVG dimensions: about 560px wide by 220px high. The chart should read as a compact README card: metrics on the left, heatmap on the right, no large unused blank area.

The script is safe to re-run at any time: for the same YAML input and same `today` date, it always overwrites `assets/chart.svg` deterministically.

## GitHub Actions Workflow

Trigger: `push` to `main` when `shadow_assets/assets.yaml` changes, plus a daily scheduled run so the rolling window advances even on days with no new assets.

Steps:
1. `actions/checkout@v4` with `persist-credentials: true`
2. `actions/setup-python@v5` (Python 3.11)
3. `pip install pyyaml`
4. `python scripts/build_readme_chart.py`
5. Commit and push `assets/chart.svg` if it changed (use `git diff --quiet` guard to skip no-op pushes)

The workflow commits as `github-actions[bot]`. No secrets needed beyond the default `GITHUB_TOKEN`.

## Constraints

- No new Python dependencies beyond PyYAML (already used by existing scripts).
- SVG must render correctly in GitHub's Markdown renderer, which sandboxes SVGs (no JS, no external fonts — use `font-family` with system fallbacks only).
- The workflow must not push if the SVG is unchanged, to avoid infinite push loops.
- Do not edit `assets/chart.svg` by hand; treat it as a build artifact.
