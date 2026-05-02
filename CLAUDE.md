# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running Things

```bash
# Run tests
python -m pytest tests/test_shadow_commit.py -q

# Commit a staged session
python scripts/shadow_commit.py --session shadow_sessions/<file>.md

# Rebuild dashboard JSON only
python scripts/build_shadow_dashboard.py

# Launch dashboard in browser (Windows)
pwsh -ExecutionPolicy Bypass -File scripts/start_shadow_dashboard.ps1
# Dashboard at http://localhost:4173
```

## Design Constraints

- **Stage-first, never skip review.** Capture writes a session file; user edits it before commit. Do not write directly to `assets.yaml`.
- **Helper scripts own YAML edits.** Use `shadow_commit.py` rather than editing `assets.yaml` or `review_state.yaml` by hand.
- **Review drafts are provisional.** Files under `shadow_reviews/review_drafts/` must not be applied to durable state until the user confirms via the report step.
- **Dashboard is read-only.** `dashboard/data/dashboard-data.json` is generated; never edit it directly.
- **Duplicates are reset signals.** A repeated capture hit increments `reset_count` and reverts status to `"new"` — never silently suppress.
- **Conservative recommendations.** Err toward fewer items in `## Recommendations`; the must-keep list takes priority.

## Skills

The workflow is driven by four skills in `.agents/skills/`. Always invoke a skill rather than editing files ad-hoc.

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `shadow-capture` | new transcript | Parses transcript + must-keep bullets → stages `shadow_sessions/*.md` |
| `shadow-commit` | after session review | Promotes staged items to `assets.yaml` / `review_state.yaml` via helper script |
| `shadow-review` | review loop | Drafts a review session from durable assets; writes to `review_drafts/` only |
| `shadow-report` | after review | Summarizes draft, then batch-applies updates after user confirmation |

The shared contract (classification rules, edge cases, field definitions) lives in [`.agents/skills/shadow-practice/SKILL.md`](.agents/skills/shadow-practice/SKILL.md).

## Overview

Four-command workflow (capture → commit → review → report) backed entirely by Markdown and YAML files. See [README.md](README.md) for the full data flow, state model, and file formats.
