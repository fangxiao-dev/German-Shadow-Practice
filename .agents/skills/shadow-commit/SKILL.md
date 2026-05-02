---
name: shadow-commit
description: "Thin wrapper entry point for promoting staged shadow assets into durable storage."
---

# shadow-commit

Use this skill as the `$shadow-commit` entry point for the local German shadow-practice workflow.
It is a thin wrapper around the shared `shadow-practice` conventions.

## Purpose

Promote the reviewed session file into durable assets, then open the local dashboard by default for immediate browsing.

## Trigger

Use when the user says the session has been reviewed and the remaining items can be committed to long-term storage.

## Delegation

Follow the commit rules in `<project-root>\.agents\skills\shadow-practice\SKILL.md`.

## Preferred Execution Path

Use the local helper script first instead of manually editing YAML:

```powershell
python <project-root>\scripts\shadow_commit.py
```

Rules:
- If the user provides an explicit session file, pass it with `--session`.
- Prefer an absolute `--session` path, or ensure the helper script resolves a relative session path against `<project-root>` before computing the stored `source_session` reference.
- If no session is provided, let the script choose the latest `YYYY-MM-DD-HHMM.md` session.
- Let the script update `shadow_assets\assets.yaml`, `shadow_reviews\review_state.yaml`, `shadow_reviews\review_log.md`, rebuild dashboard data, and launch/open the dashboard by default.
- Use `--no-dashboard` only when the user explicitly asks to skip dashboard follow-up.
- Use `--no-open` only when the user wants dashboard refresh without opening a browser.
- Before considering manual YAML edits, inspect why the script failed and prefer fixing the script or environment issue.

## Failure Handling

If the helper script or dashboard follow-up fails:
- Read the full error first and identify the failing boundary: commit write, dashboard data rebuild, server start, or browser open.
- Do not switch to manual edits until the script path is proven unsuitable for the current task.
- For sandbox-related `PermissionError`, network listener failures, or GUI/browser opening failures, retry the same script command with escalation instead of hand-running individual replacement steps.
- If dashboard launch fails after durable commit succeeds, keep the durable commit result and debug only the dashboard boundary.

## Read / Write Boundary

Reads:
- `<project-root>\shadow_sessions\*.md`
- `<project-root>\shadow_assets\assets.yaml`
- `<project-root>\shadow_reviews\review_state.yaml`

Writes:
- `<project-root>\shadow_assets\assets.yaml`
- `<project-root>\shadow_reviews\review_state.yaml`
- `<project-root>\shadow_reviews\review_log.md` when a short commit note is needed
