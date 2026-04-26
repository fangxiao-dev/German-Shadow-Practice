# Design: Shadow Practice System

> **Status:** Draft
> **Last updated:** 2026-04-13
> **Related plan:** `docs/plans/2026-04-13-shadow-practice-system.md`

---

## Project Background

This project supports German shadowing practice based on local transcript files. The user practices by listening, attempting to repeat, checking the transcript, and then overlearning useful expressions until they can be produced without the text. The system is not an app; it is a local, file-backed agent workflow that reduces post-practice friction and turns one-off inputs into reviewable language assets.

---

## Module Background & Goals

The immediate problem is not transcript access but asset formation. The user already knows many of the words, phrases, and expression patterns worth keeping, but manual extraction is slow, which means useful input often never becomes part of a reusable review loop. The module therefore focuses first on low-friction capture, then on tracked review, while leaving scenario-based speaking drills as a later extension.

### Goals

- Turn a pasted shadow transcript into structured candidate assets with minimal manual formatting.
- Separate provisional capture from long-term asset storage so the permanent library stays clean.
- Track enough review state to support incremental, focus, and full review scopes without building a heavy spaced-repetition system.
- Keep all intermediate and final records on local disk so later agent turns can reread state instead of relying on chat context.

### Non-Goals

- Build a standalone app, GUI, or mobile workflow.
- Accept audio input or score shadow performance from speech.
- Fully automate all asset selection without user confirmation.
- Implement a sophisticated SRS scheduler in the first version.
- Treat abstract usage advice as a first-class asset type in v1.

---

## Solution Overview

| Feature / Capability | Technology / Approach | Rationale |
|---|---|---|
| Low-friction transcript input | Local transcript files plus a `---` separator and bullet list of must-keep items | Keeps the source of truth in one place and lets the user force-include important items without tagging type. |
| Clean capture workflow | `capture` writes a session file first, not the long-term asset library | Prevents unconfirmed agent suggestions from polluting the persistent asset base. |
| Controlled promotion into the library | `commit` writes only user-confirmed items into the asset store and review state | Makes the asset library deliberate and easier to maintain over time. |
| Flexible asset representation | A generic `asset` model with `word`, `phrase`, and `pattern` as v1 types | Matches the user's real learning objects better than a vocabulary-card model. |
| Review scope control | File-backed review state with `incremental`, `focus`, and `full` modes | Supports realistic study sessions without forcing date math every time. |
| Context-safe review evaluation | `review` writes drafts first; `report` rereads local draft files to summarize and then batch-applies status updates | Avoids dependence on long chat context and keeps later decisions reproducible. |
| Future speaking expansion | Reserve `drill` as a separate capability fed by existing `phrase` and `pattern` assets | Keeps v1 narrow while preserving a clean path to scenario-based output practice. |

The system is intentionally file-centric. The user interacts through agent commands, while the durable system state lives in markdown files that the agent can reread on demand.

---

## Constraints

- Input is text only; the workflow must assume pasted transcripts, not audio.
- The workspace is local, so the system should prefer simple file operations over external services.
- The user must be able to mark must-keep items in a very lightweight format.
- Review outcomes cannot require per-item confirmation during the exercise itself.
- Long-lived state must be reconstructable from files rather than chat memory.
- The first version must prioritize reduced friction over completeness.

---

## Data Model

The core object is an `asset`, not a vocabulary card. This allows the system to store single words when the user explicitly chooses them, but still treat phrase chunks and reusable answer patterns as first-class learning objects.

### Asset Types

- `word`: usually user-marked individual lexical items.
- `phrase`: short expressions, chunks, collocations, or fixed/semi-fixed language.
- `pattern`: reusable expression frames or response structures that can transfer into speaking.

Abstract usage guidance is not a standalone v1 asset type. If it matters, it should either be attached as a short explanation to a concrete asset or deferred to a later drill capability.

### Core Fields

- `id`
- `type`
- `title`
- `content`
- `collocation`
- `why_keep`
- `source_session`
- `created_at`
- `status`
- `priority`
- `review_count`
- `last_reviewed_at`
- `mistake_note`

### Status Model

`status` is a mutually exclusive current-state field:

- `new`
- `learning`
- `weak`
- `solid`

Priority is separate from status so an item can remain `learning` while also being marked `high` priority.

---

## Workflow Boundaries

### Capture

The user pastes:

1. local transcript file
2. `---`
3. bullet points of must-keep items

The agent:

- parses the transcript and user list
- classifies must-keep items into asset types
- proposes a small number of recommendation items that fill obvious gaps
- writes a session record that references the source transcript path
- does not modify the long-term asset library yet

The capture-stage session document has two sections with the same item shape:

- `Must Keep Candidates`: user-selected items that remain visible even when normalized
- `Recommendations`: agent-suggested omissions worth considering

Each staged item should use the same fields so the user can prune without switching mental models:

- `raw`
- `target`
- `type`
- `english`
- `transcript_sentence`
- optional `durable_hit`
- optional `collocation` or `collocations`

`collocation` is subordinate context attached to a main target, not a second target. It exists to preserve useful noun+verb or fixed-wording memory hooks such as `Lagebild` -> `Lagebilder erstellen` without creating a competing parallel asset.

Recommendations should fill genuinely missing learning targets, not restate sentence-level framing. Discourse organizers such as `zum einen ..., zum anderen ...` should not be lifted into a recommendation when the user's marked items already preserve the substantive content from that sentence.

### Commit

The agent promotes only confirmed items into:

- the asset library
- the review state store

This is the boundary between provisional work and durable knowledge.

### Review

The agent runs a review session against the current asset library using one of three scopes:

- `incremental`
- `focus`
- `full`

The review result is written first into a draft record, not directly into the final state.

### Report

When the user explicitly asks for a report after review, the agent rereads the saved draft and produces:

- suggested solid items
- suggested weak/revisit items
- observed patterns or notes

The user gives lightweight, grouped feedback, and the agent then batch-updates review state and review log files.

---

## File Layout

```text
docs/designs/shadow-practice-system.md
docs/plans/2026-04-13-shadow-practice-system.md
raw-transcripts/
shadow_sessions/
shadow_assets/assets.yaml
shadow_reviews/review_state.yaml
shadow_reviews/review_log.md
shadow_reviews/review_drafts/
.commands/
.agents/skills/shadow-practice/
```

The document and directory names are part of the design because they encode lifecycle:

- `docs/designs/` is long-lived and maintained in place
- `docs/plans/` is implementation-oriented and disposable after execution
- `shadow_*` directories hold the runtime knowledge base for the workflow
- `commands/` holds local command conventions that map fixed triggers like `/shadow-capture` to the matching workflow actions

---

## Storage Decision

The first implementation will use mixed storage:

- Markdown for session records, review drafts, and review reports.
- YAML for durable asset state and review state.

This split matches the data shape. Session and report files are narrative working records that should remain easy to read and edit. Asset and review state files are structured objects that the agent must update repeatedly and reliably.

---

## Open Questions

- How aggressively the agent should suggest recommendation items beyond user-specified must-keep items.
- How scenario-based drills should consume existing assets without turning into memorized scripts.

---

## Decision Log

### [2026-04-13] Separate design docs from implementation plans

**Decision:** Store long-lived design documentation in `docs/designs/` and implementation plans in `docs/plans/`.
**Alternatives considered:** Put both documents under `docs/plans/` following a generic brainstorming skill default.
**Reason:** Design and implementation plan have different lifecycles. The design must be maintained over time, while the plan is execution-oriented and may be deleted or archived after implementation.

### [2026-04-13] Use a file-backed agent workflow instead of building an app

**Decision:** Build the first version as a local skill-driven workflow with durable files.
**Alternatives considered:** Build a standalone app or add a heavier database-backed system first.
**Reason:** The main problem is friction after practice, not interface availability. File-backed agent commands solve the immediate problem with less overhead and preserve flexibility.

### [2026-04-13] Split provisional capture from durable storage

**Decision:** `capture` writes session records first; `commit` promotes confirmed items into the long-term asset library.
**Alternatives considered:** Let capture write directly into the permanent library.
**Reason:** The user wants to provide must-keep items and also calibrate agent suggestions over time. A provisional layer keeps the permanent library cleaner.

### [2026-04-13] Delay final review-state updates until after a report step

**Decision:** `review` writes drafts; `report` summarizes from files; user feedback then batch-updates final state.
**Alternatives considered:** Require per-item confirmation during review or auto-apply agent judgments immediately.
**Reason:** Per-item confirmation adds friction, while immediate auto-application risks drift and misclassification. The draft/report/apply flow balances speed and control.

### [2026-04-13] Use mixed Markdown and YAML storage

**Decision:** Store session-like records in Markdown and structured durable state in YAML.
**Alternatives considered:** Keep everything in Markdown, or move immediately to a database-backed design.
**Reason:** Markdown is better for human-readable working notes, while YAML is better for repeated agent updates to structured fields such as asset type, status, review counts, and timestamps.

---
