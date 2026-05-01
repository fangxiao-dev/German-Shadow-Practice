# README Heatmap Design

**Date:** 2026-05-01  
**Status:** Approved

## What We're Building

A self-updating SVG chart embedded in README.md for public GitHub display. It shows German shadow-practice activity at a glance: how many days studied, how many words committed, and when sessions happened relative to today.

## Visual Design

Style: GitHub dark theme (`#0d1117` background), Segoe UI / system-ui font, Claude orange heatmap palette.

**Stat row** — three compact cards side by side:
- Study days (total unique days in `assets.yaml`, highlighted orange)
- Words committed (total asset count, white)
- Avg words per session (total ÷ study days, white)

**Heatmap grid** — GitHub contribution-graph format:
- 12 weeks of columns, newest week at the right, today's week partial
- 7 rows (Mon–Sun), left axis labels on Mon/Wed/Fri
- Month labels above the column group where a month begins
- Each cell: 11×11 px, 3 px gap, 2 px border-radius
- Empty cells: `#21262d`; active cells in 4 intensity steps keyed to word count quartiles across the window:
  - Level 1 (low): `#4a1f08`
  - Level 2: `#7d3a10`
  - Level 3: `#d36820`
  - Level 4 (high): `#f0883e`
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

**Color thresholds:** computed dynamically from the non-zero values in the 12-week window (quartiles), so intensity is always relative to the current period, not a hardcoded scale.

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
4. Determine 12-week window: `today - 83 days` through `today`, aligned to Monday starts
5. Map each date in window to an intensity level (0–4) using quartiles of non-zero counts
6. Render SVG as a string — hand-built XML, no external SVG library needed
7. Write to `assets/chart.svg`

SVG dimensions: width = `(12 weeks × 14px) + left_margin + right_padding` ≈ 720px wide, height ≈ 180px. Exact values computed during implementation to fit content cleanly.

The script is safe to re-run at any time: it always overwrites `assets/chart.svg` deterministically from the same YAML input.

## GitHub Actions Workflow

Trigger: `push` to `main`.

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
