---
name: shadow-report
description: "Thin wrapper entry point for summarizing a saved shadow review draft and applying batch updates after confirmation."
---

# shadow-report

Use this skill as the `$shadow-report` entry point for the local German shadow-practice workflow.
It is a thin wrapper around the shared `shadow-practice` conventions.

## Purpose

Summarize a saved review draft and apply batch updates after user confirmation.

## Trigger

Use when the user says a review is finished and wants the report/update phase.

## Delegation

Follow the report rules in `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`.

## Read / Write Boundary

Reads:
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md`
- `E:\Personal\学德语\shadow_assets\assets.yaml`
- `E:\Personal\学德语\shadow_reviews\review_state.yaml`

Writes:
- `E:\Personal\学德语\shadow_reviews\review_log.md`
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md` for the report draft and proposed updates
- `E:\Personal\学德语\shadow_reviews\review_state.yaml` only after the user confirms the proposed bulk updates
