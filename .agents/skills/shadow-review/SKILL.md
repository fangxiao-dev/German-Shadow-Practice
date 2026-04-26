---
name: shadow-review
description: "Thin wrapper entry point for running a draft-only shadow asset review session."
---

# shadow-review

Use this skill as the `$shadow-review` entry point for the local German shadow-practice workflow.
It is a thin wrapper around the shared `shadow-practice` conventions.

## Purpose

Run an active review session over durable assets and write the result as a draft.

## Trigger

Use when the user wants a review session such as incremental, focus, or full.

## Delegation

Follow the review rules in `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`.

## Read / Write Boundary

Reads:
- `E:\Personal\学德语\shadow_assets\assets.yaml`
- `E:\Personal\学德语\shadow_reviews\review_state.yaml`
- `E:\Personal\学德语\shadow_reviews\review_log.md` when past review context matters

Writes:
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md`
