---
name: shadow-capture
description: "Thin wrapper entry point for stage-first shadow transcript capture."
---

# shadow-capture

Use this skill as the `$shadow-capture` entry point for the local German shadow-practice workflow.
It is also the capture executor when `$shadow-practice capture` delegates here.
It is a thin wrapper around the shared `shadow-practice` conventions.

## Purpose

Stage a transcript file into a session note that the user can prune before commit, while keeping duplicate durable hits visible as reset-worthy learning signals.

## Trigger

Use when the user wants to capture a local transcript file and stage items for review, or when `shadow-practice` dispatches a resolved transcript path to capture.

## Delegation

Follow the capture rules in `<project-root>\.agents\skills\shadow-practice\SKILL.md`.
In particular, do not suppress duplicate user-marked items just because they already exist in the durable asset store.
For session layout details, follow `<project-root>\.agents\skills\shadow-capture\references\session-format.md`.
Do not define latest-transcript selection here; `$shadow-practice capture` owns that default. This skill owns how to turn the resolved transcript into a staged session file.

## Read / Write Boundary

Reads:
- `<project-root>\raw-transcripts\*.md`
- `<project-root>\shadow_assets\assets.yaml` for context only
- `<project-root>\shadow_reviews\review_state.yaml` for context only

Writes:
- `<project-root>\shadow_sessions\*.md`
- `<project-root>\shadow_reviews\review_drafts\*.md` only if a draft note is useful
