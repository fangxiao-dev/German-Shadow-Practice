---
name: shadow-capture
description: "Thin wrapper entry point for stage-first shadow transcript capture."
---

# shadow-capture

Use this skill as the `$shadow-capture` entry point for the local German shadow-practice workflow.
It is a thin wrapper around the shared `shadow-practice` conventions.

## Purpose

Stage a transcript file into a session note that the user can prune before commit, while keeping duplicate durable hits visible as reset-worthy learning signals.

## Trigger

Use when the user wants to capture a local transcript file and stage items for review.

## Delegation

Follow the capture rules in `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`.
In particular, do not suppress duplicate user-marked items just because they already exist in the durable asset store.

## Read / Write Boundary

Reads:
- `E:\Personal\学德语\raw-transcripts\*.md`
- `E:\Personal\学德语\shadow_assets\assets.yaml` for context only
- `E:\Personal\学德语\shadow_reviews\review_state.yaml` for context only

Writes:
- `E:\Personal\学德语\shadow_sessions\*.md`
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md` only if a draft note is useful
