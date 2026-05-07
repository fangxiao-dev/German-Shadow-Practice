# Shadow Capture Session Format

This file is the canonical capture template for `shadow-capture`.
Use it as the source of truth for staged session layout, item fields, and durable-hit reset markers.
Do not infer structure from older session files unless you are checking content.

## Session file template

```md
# Shadow Session

- source: `raw-transcripts\260502.md`
- captured_at: `2026-05-02 10:47`
- status: staged

## Raw Transcript
See source file: `raw-transcripts\260502.md`

---

## Must Keep Candidates

- No must_keep bullets were present in the source file.

## Recommendations

- raw: `...`
  target: `...`
  type: `word|phrase|pattern`
  english: `...`
  transcript_sentence: `...`
  collocation: `...`
  durable_hit: `a-...` -> reset candidate

## Dry Run Notes

- Notes about normalization, separator handling, related durable items, and durable hits.
```

## Rules

- Keep the raw transcript outside the session file body.
- Keep `source`, `captured_at`, and `status` at the top.
- Use the `Raw Transcript` section only as a pointer to the source file.
- Keep `Must Keep Candidates` and `Recommendations` in the same field order.
- Use the same item fields in both sections.
- Include `raw`, `target`, `type`, `english`, and `transcript_sentence` on every staged item.
- Use `collocation` only for subordinate wording that helps recall but should not become a separate target.
- Use `durable_hit` when the staged `target` has an exact hit in the generated durable index after normalizing away non-core wording.
- Non-core wording includes filler or discourse particles such as `eben`, `so`, `ja`, `doch`, `halt`, `mal`, `gerade`, `eigentlich`, and inflection or article noise when the same reusable target remains.
- Before marking a `durable_hit`, extract the main reusable target and compare that core through `scripts\shadow_lookup.py` or `scripts.shadow_index` against durable asset `content`, `title`, and non-empty `collocation`.
- Mention related but different constructions only in `Dry Run Notes`; do not mark them as reset candidates.
- If no must_keep bullets are present, keep the section and say so explicitly.
- If the source file has no `---` separator, treat the entire file as transcript text and note that in `Dry Run Notes`.
- Keep `Dry Run Notes` short and factual.
