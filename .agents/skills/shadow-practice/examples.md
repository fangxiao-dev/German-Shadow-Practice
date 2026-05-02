# shadow-practice examples

## Unified dispatcher

Input:

```text
$shadow-practice capture
```

Expected behavior:
- Choose the latest `<project-root>\raw-transcripts\*.md` by filesystem last-write time.
- Delegate the resolved transcript path to `shadow-capture`.
- Stage the session under `<project-root>\shadow_sessions\`.

Input:

```text
$shadow-practice commit
```

Expected behavior:
- Choose the latest `YYYY-MM-DD-HHMM.md` session under `<project-root>\shadow_sessions\`.
- Delegate the resolved session path to `shadow-commit`.

Input:

```text
$shadow-practice review
```

Expected behavior:
- Default to `incremental`.
- Delegate the resolved scope to `shadow-review`.

Input:

```text
$shadow-practice report
```

Expected behavior:
- Choose the latest review draft under `<project-root>\shadow_reviews\review_drafts\`.
- Delegate the resolved draft path to `shadow-report`.

## `capture`

Source file: `<project-root>\raw-transcripts\2026-04-13-0930.md`

Content:

```text
Heute geht es um die Frage, wie man im Alltag mit Unsicherheit umgeht. Ich habe versucht, ruhig zu bleiben, obwohl ich nicht sofort eine Lösung hatte.

---
- mit Unsicherheit umgehen
- obwohl ich nicht sofort eine Lösung hatte
- ruhig bleiben
```

Expected behavior:
- Read the transcript and preserve it in a local session note such as `<project-root>\shadow_sessions\2026-04-13-0930.md`.
- Record the source transcript path in the session note instead of copying the full raw transcript body.
- Treat all bullets as mandatory candidates.
- Infer types:
  - `mit Unsicherheit umgehen` -> `phrase`
  - `obwohl ich nicht sofort eine Lösung hatte` -> `pattern`
  - `ruhig bleiben` -> `phrase`
- Optionally suggest nearby omissions under `Recommendations`, but keep the staged item fields identical to `Must Keep Candidates`.
- Do not write confirmed assets yet.

Normalization example:
- raw: `benennt`
- normalized target: `benennen`
- english: `name or label`
- transcript_sentence: `Die Studie benennt drei zentrale Probleme.`

Source file: `<project-root>\raw-transcripts\2026-04-13-0945.md`

Content:

```text
Ich hatte heute ein langes Gespräch mit einer Kollegin, und es ging vor allem darum, ruhig zu bleiben, offen zu sprechen und eine Lösung Schritt für Schritt zu finden.

---
- ruhig zu bleiben
- offen zu sprechen
- eine Lösung Schritt für Schritt zu finden
```

Expected behavior:
- Treat this as a phrase-heavy capture.
- Classify the bullets as phrases unless one is clearly a pattern.
- Keep the recommendations small and focused.
- Do not promote sentence-level discourse framing into `Recommendations` when the marked items already capture the reusable content.

Source file: `<project-root>\raw-transcripts\2026-04-13-1000.md`

Content:

```text
Was ich damit sagen will, ist nicht, dass alles sofort perfekt sein muss, sondern dass man den ersten Schritt überhaupt macht.

---
- Was ich damit sagen will, ist
- nicht, dass alles sofort perfekt sein muss
- den ersten Schritt überhaupt macht
```

Expected behavior:
- Treat this as a clear pattern capture.
- Classify the first bullet as `pattern`.
- Preserve the other bullets as pattern or phrase only if they are direct structural helpers for the same pattern.
- Do not invent a new asset type for abstract usage advice.

Normalization and shorthand examples:
- raw: `aus meiner Sich`
- normalized target: `aus meiner Sicht`
- english: `in my view`
- transcript_sentence: `Aus meiner Sicht ist das zu riskant.`
- raw: `adj. anwendbar`
- normalized target: `adj. anwendbar`
- english: `applicable`
- transcript_sentence: `Die Regel ist hier nicht direkt anwendbar.`
- optional collocation on a staged item:
  - target: `Lagebild`
  - collocation: `Lagebilder erstellen`
  - english: `create situational pictures`
  - transcript_sentence: `Und auch da wieder eine Erstellung von Lagebildern ist sehr hilfreich.`
  - keep collocations attached to the main item instead of promoting them into a parallel target

## `commit`

Input:

```text
commit the confirmed items from <project-root>\shadow_sessions\2026-04-13-0930.md
```

Expected behavior:
- Read the staged session file.
- Promote only the confirmed items into `<project-root>\shadow_assets\assets.yaml`.
- Persist the staged `english` gloss into durable assets.
- Persist the staged `transcript_sentence` into durable assets.
- Initialize or update the corresponding review state in `<project-root>\shadow_reviews\review_state.yaml`.
- Append a short note to `<project-root>\shadow_reviews\review_log.md` only if needed for traceability.

Example confirmed items:
- `mit Unsicherheit umgehen` as `phrase`
- `obwohl ich nicht sofort eine Lösung hatte` as `pattern`
- `ruhig bleiben` as `phrase`

## `review`

Input:

```text
review incremental from <project-root>\shadow_assets\assets.yaml and <project-root>\shadow_reviews\review_state.yaml
```

Expected behavior:
- Read durable assets and current review state.
- Select a small incremental set: new items plus a few weak items.
- Write the session output to a draft such as `<project-root>\shadow_reviews\review_drafts\2026-04-13-incremental.md`.
- Keep the review draft local and do not finalize state yet.

German practice example:
- Prompt: `Wie würdest du sagen, dass du trotz Stress ruhig geblieben bist?`
- Target asset: `ruhig bleiben`
- Target pattern: `obwohl ich ...`

## `report`

Input:

```text
report after review draft <project-root>\shadow_reviews\review_drafts\2026-04-13-incremental.md
```

Expected behavior:
- Read the latest review draft.
- Summarize what looked solid, what needs another pass, and any repeated mistake pattern.
- Propose batch updates to `<project-root>\shadow_reviews\review_state.yaml`.
- Write the concise summary to `<project-root>\shadow_reviews\review_log.md`.

Example report content:
- Solid: `ruhig bleiben`
- Revisit: `obwohl ich nicht sofort eine Lösung hatte`
- Note: the pattern is understood, but spontaneous recall is still slow
