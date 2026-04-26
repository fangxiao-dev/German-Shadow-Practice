---
name: shadow-practice
description: "Shared core contract for the local German shadow-practice workflow. This skill is a file-backed scaffold, not an app, and defines the capture, commit, review, and report rules used by the thin wrapper skills."
---

# shadow-practice

Use this skill for the local German shadow-practice workflow. It is a file-backed agent scaffold, not an app. Keep it operational and narrow: capture, commit, review, report.
It serves as the shared core contract for the thin wrapper skills `shadow-capture`, `shadow-commit`, `shadow-review`, and `shadow-report`.

## Purpose

Turn pasted shadow transcripts into durable learning assets, then review them in a controlled local loop. The agent must prefer local file state over chat memory once a command has been written to disk.

## Command contract

### `capture`

Use when the user points to a local transcript file and wants the material staged for review.

Reads:
- A local transcript file, typically under `E:\Personal\学德语\raw-transcripts\`
- Optional existing local state for context only:
  - `E:\Personal\学德语\shadow_assets\assets.yaml`
  - `E:\Personal\学德语\shadow_reviews\review_state.yaml`

Writes:
- `E:\Personal\学德语\shadow_sessions\*.md`
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md` only if a draft review note is useful

Behavior:
- Parse the transcript and must_keep list from a local source file that uses the `---`-separated input.
- Classify each must_keep item as `word`, `phrase`, or `pattern`.
- Propose recommendation items only when they are clearly worthwhile and fill an obvious gap in the user's list.
- Keep recommendation volume conservative:
  - aim to provide at least 1 strong recommendation when the transcript clearly contains one
  - do not recommend weak, repetitive, or merely local sentence fragments just to hit a quota
  - there is no hard maximum, but the practical default is to keep only the strongest useful recommendations
- Normalize user-marked items into durable target forms when the intended form is obvious:
  - convert inflected verb forms to the lemma when the item is meant as a standalone word
  - correct obvious typos in the staged target form
  - keep the user's original bullet text visible in the session note
- Add a compact `english` gloss for each staged item; keep it to one short transcript-specific meaning.
- Add a `transcript_sentence` field for each staged item using the matching source sentence from the current transcript.
- Keep worthwhile recommendations visible in the session note so the user can prune them during review.
- Use the same staged item fields in both `Must Keep Candidates` and `Recommendations`.
- Use `collocation` or `collocations` only for subordinate wording that strengthens recall of the main target without becoming a separate target.
- Do not recommend:
  - speed/intensity modifiers or other disposable local variations that are not stable learning targets
  - near-duplicates of an already staged target unless the duplicate signal itself matters for later commit behavior
  - discourse scaffolds or paired connectors extracted from a sentence when the user's staged items already capture the main transferable content
- Preserve user shorthand such as `adj.` when it is intentionally used as a compact study label.
- Do not write a `note` field in staged items.
- Write a session file under `E:\Personal\学德语\shadow_sessions\` using the stable session naming rule.
- Store the source transcript path in the session file instead of copying the full raw transcript body.
- Do not write to the permanent asset store yet.
- Treat the session file as the editable review document for the next step.
- When a staged target matches an existing durable asset, keep it visible in the session note instead of silently suppressing it.
- Mark repeated durable hits clearly in the session note so the later `commit` step can treat them as resets of an existing asset rather than as brand-new assets.

Edge cases:
- If no `---` section is present in the source file, treat the whole file as the transcript and assume an empty must_keep list.
- If the bullet list is empty, keep the session file and skip candidate extraction.
- If many recommendation candidates are possible, include only the strongest ones; recommendation count is driven by usefulness, not by quota.
- If a candidate type is ambiguous, default to `phrase`.
- If the content is abstract usage advice, defer it to a later drill phase instead of creating a v1 asset type.
- If a user-marked item is clearly a malformed form, stage the corrected target form explicitly.
- If a useful memory hook exists but should not become a separate target, attach it as `collocation` instead of emitting a second staged item.
- Skip recommendation items that duplicate a target already staged in the current session, or a narrower variant already covered by a broader reusable chunk.
- Do not upgrade sentence-level framing such as `zum einen ..., zum anderen ...` into a recommendation when the user already marked the substantive payload from the same sentence.
- Do not skip user-marked staged items merely because they duplicate an existing durable asset; duplicate user-marking is itself a learning signal.

### `commit`

Use when the user says the session is reviewed and the remaining items should become durable assets.

Reads:
- `E:\Personal\学德语\shadow_sessions\*.md`
- `E:\Personal\学德语\shadow_assets\assets.yaml`
- `E:\Personal\学德语\shadow_reviews\review_state.yaml`

Writes:
- `E:\Personal\学德语\shadow_assets\assets.yaml`
- `E:\Personal\学德语\shadow_reviews\review_state.yaml`
- `E:\Personal\学德语\shadow_reviews\review_log.md` when a short commit note is needed

Behavior:
- Prefer the local helper script for commit execution:
  - `python E:\Personal\学德语\scripts\shadow_commit.py`
  - add `--session <path>` when the user identifies a specific reviewed session
  - only fall back to manual YAML edits after investigating why the helper script is unsuitable
- Read the session file identified by the user if an explicit session path is provided.
- Otherwise read the latest `YYYY-MM-DD-HHMM.md` session file in `E:\Personal\学德语\shadow_sessions\` by timestamp.
- Include every item still present in the reviewed session file, including any recommended items the user chose to keep.
- Treat removed items in the session document as intentionally rejected.
- Do not require a second approval pass for recommendation items that remain in the edited session.
- For a truly new target, append a new durable record to `E:\Personal\学德语\shadow_assets\assets.yaml` and `E:\Personal\学德语\shadow_reviews\review_state.yaml`.
- For a target that already exists in the durable store, do not create a duplicate durable record.
- Treat a repeated durable hit as a reset signal:
  - reset the existing asset's learning status back to `new`
  - keep `review_count` as the historical count of completed reviews; do not zero it out
  - increment a separate durable reset counter so the system can distinguish first-time additions from later resets
  - keep the existing durable asset id rather than minting a new one
- Persist `english` and `transcript_sentence` into durable assets.
- Do not persist temporary rationale text such as `note` or `why_keep` into durable assets.
- Keep the durable store aligned with the reviewed session document, not with speculative suggestions.
- The commit result must preserve the distinction between:
  - first-time durable additions
  - existing durable assets that were re-hit and reset by a later capture
- If the helper script fails, isolate the failing boundary before changing approach:
  - durable YAML write
  - dashboard data rebuild
  - local dashboard server start
  - browser open
- For sandbox-related write, listener, or browser failures, rerun the same helper-script path with escalation before replacing it with manual per-file commands.

### `review`

Use when the user wants an active review session over local assets.

Reads:
- `E:\Personal\学德语\shadow_assets\assets.yaml`
- `E:\Personal\学德语\shadow_reviews\review_state.yaml`
- `E:\Personal\学德语\shadow_reviews\review_log.md` when past review context matters

Writes:
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md`

Behavior:
- Support review scopes:
  - `incremental`: prioritize new items plus a small number of weak items.
  - `focus`: prioritize weak items and items with high priority.
  - `full`: prioritize a broad pass over the user-specified range; if no range is specified, use all currently eligible durable assets.
- Select items from durable state, not from chat memory.
- Write the review result as a draft record under `E:\Personal\学德语\shadow_reviews\review_drafts\` and do not directly mutate final review state.
- Keep the review output draft-only until the user asks for the report step.

### `report`

Use when the user says the review is finished and wants a summary and update proposal.

Reads:
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md`
- `E:\Personal\学德语\shadow_assets\assets.yaml`
- `E:\Personal\学德语\shadow_reviews\review_state.yaml`

Writes:
- `E:\Personal\学德语\shadow_reviews\review_log.md`
- `E:\Personal\学德语\shadow_reviews\review_drafts\*.md` for the report draft and proposed updates
- `E:\Personal\学德语\shadow_reviews\review_state.yaml` only after the user confirms the proposed bulk updates

Behavior:
- Reread the saved review draft.
- Summarize suggested solid items.
- Summarize suggested weak or revisit items.
- Summarize observed mistakes.
- Include proposed bulk updates in the report draft, but do not apply them yet.
- Wait for grouped user feedback before writing the final bulk state updates to durable review state and review log.
- Treat that confirmation as the update phase within `report`; do not introduce a separate supported `apply` command.
- Apply updates in batch after confirmation, not item-by-item chat confirmation.

## Input format

The capture input uses a transcript file with a transcript-plus-separator form:

```text
<raw transcript text stored in raw-transcripts/...>

---
- mandatory item 1
- mandatory item 2
- mandatory item 3
```

Rules:
- The raw transcript file is the source of truth and should live outside `shadow_sessions`.
- The transcript content comes first inside that source file.
- A single line with `---` separates transcript from candidate notes.
- Bullet items after `---` are staged candidates.
- The bullet items are not typed by the user.
- The agent must infer whether each bullet is a `word`, `phrase`, or `pattern`.
- If a bullet is ambiguous, keep the item but classify it conservatively.
- After capture, the session file is the review surface the user can prune before commit.

## Operational rules

- Keep the scaffold local-first.
- Prefer Markdown for session notes, drafts, and reports.
- Prefer YAML for durable asset state and review state.
- Do not expand this skill into a full study app.
- Do not invent extra commands unless the workflow needs them.
- Keep `review_count` semantically narrow: it counts completed review events, not capture-time resets.
- Track repeated capture-driven resets separately from review history.
- During capture, separate three things clearly:
  - the raw user-marked item
  - the normalized target form to be committed
  - the compact English gloss for the meaning used in this transcript
  - the transcript sentence for the meaning used in this transcript
  - any optional collocation attached to that target

## Durable state semantics

- Durable assets and review state should preserve two different histories:
  - review history: how many formal reviews the item has gone through
  - reset history: how many times an existing durable item was re-hit by later captures and therefore reset
- Use `review_count` only for the first history.
- Use a separate field such as `reset_count` for the second history.
- Duplicate user-marking is not noise; it is evidence that the item is still unstable enough to re-enter active learning.

## Session naming

- Use one session file per capture.
- File names must follow `YYYY-MM-DD-HHMM.md`.
- Store the file in `E:\Personal\学德语\shadow_sessions\`.
- Use the README in `shadow_sessions` for file-purpose conventions.
- Session files should reference the transcript source path rather than duplicate the raw transcript body.

## Examples

See `E:\Personal\学德语\.agents\skills\shadow-practice\examples.md` for realistic command examples.
