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

Follow the report rules in `<project-root>\.agents\skills\shadow-practice\SKILL.md`.

## Read / Write Boundary

Reads:
- `<project-root>\shadow_reviews\review_drafts\*.md`
- `<project-root>\shadow_assets\assets.yaml`
- `<project-root>\shadow_reviews\review_state.yaml`

Writes:
- `<project-root>\shadow_reviews\review_log.md`
- `<project-root>\shadow_reviews\review_drafts\*.md` for the report draft and proposed updates
- `<project-root>\shadow_reviews\review_state.yaml` only after the user confirms the proposed bulk updates
