# Design: Shadow Asset Index

> **Status:** Draft
> **Last updated:** 2026-05-07
> **Related plan:** _To be determined._

---

## Project Background

This project supports German shadowing practice through a local, file-backed workflow. Raw transcripts are captured into staged session notes, reviewed by the user, and then committed into a durable asset store for later review.

The durable store currently lives in `shadow_assets/assets.yaml`, which is intentionally human-readable and easy to inspect. As the number of assets grows, capture-time duplicate detection and related-item lookup become harder for the agent to do reliably inside a bounded context window.

---

## Module Background & Goals

The asset index is a generated lookup layer for the durable shadow-practice library. It exists to make capture, commit, review, and dashboard workflows faster and more reliable without replacing the YAML store as the source of truth.

The immediate problem is retrieval, not storage. `assets.yaml` should remain the canonical record because it is readable, diffable, and already integrated into the existing commit and review flow. The index should be disposable and rebuildable from that canonical file.

### Goals

- Keep `shadow_assets/assets.yaml` as the durable source of truth.
- Provide fast exact lookup for duplicate targets during capture and commit.
- Provide lightweight related-item lookup for near matches, collocations, and token overlap.
- Reduce the need for agents to read the entire durable store during capture.
- Make the indexing logic shared by capture, commit, review, and dashboard code instead of duplicating normalization rules.
- Keep the first version local, simple, and fully rebuildable.

### Non-Goals

- Replace `assets.yaml` with a database as the canonical asset store.
- Split durable assets into many date-based YAML files as a retrieval strategy.
- Introduce embedding search or external vector databases in the first version.
- Build a full linguistic lemmatizer or morphology engine.
- Change the asset schema, review status semantics, or reset behavior as part of indexing.

---

## Solution Overview

| Feature / Capability | Technology / Approach | Rationale |
|---|---|---|
| Canonical durable storage | Continue writing `shadow_assets/assets.yaml` | Preserves current readable, diffable, file-backed workflow. |
| Generated lookup cache | Add `shadow_assets/asset_index.json` | JSON is simple, portable, easy to rebuild, and sufficient for the current library size. |
| Shared normalization | Move normalization and lookup helpers into `scripts/shadow_index.py` | Keeps capture and commit duplicate detection consistent. |
| Exact duplicate detection | Index normalized `content`, `title`, and useful `collocation` values | Handles most reset-candidate detection without scanning the full YAML file. |
| Related-item lookup | Build a token or n-gram inverted index over titles, content, and collocations | Gives capture enough context to mention related but different assets in dry-run notes. |
| Rebuild safety | Add a rebuild script that derives the full index from `assets.yaml` | The index is never manually edited and can be regenerated after any durable-store change. |
| Future query growth | Keep an upgrade path to SQLite FTS if JSON becomes too limited | Avoids premature database complexity while leaving a clear path for larger libraries. |

The first version should be a generated JSON index, not a database. It should make common lookup cases cheap: "does this target already exist?", "does a collocation already point to an asset?", and "are there related items worth mentioning but not resetting?"

---

## Constraints

- The workflow must remain local-first and work without external services.
- The generated index must be reconstructable from `assets.yaml` alone.
- Manual edits should happen only in source files, not in the generated index.
- The index must not become a second source of truth for review state, status, priority, or reset count.
- Capture should preserve duplicate user-marked items as learning signals; the index only helps identify them.
- Lookup should prefer deterministic matching over opaque ranking.
- The design must work inside Windows PowerShell and respect the repository's search constraints.

---

## Index Model

The JSON index should optimize for deterministic lookups and compact related context.

Recommended top-level shape:

```json
{
  "generated_at": "2026-05-07T10:50:00+02:00",
  "source": "shadow_assets/assets.yaml",
  "exact": {},
  "tokens": {},
  "items": {}
}
```

### `exact`

Maps normalized durable forms to one or more asset ids.

Sources:

- `content`
- `title`
- `collocation`, when present

The value may start as a single id, but the data model should tolerate multiple ids because the current durable store may contain historical duplicates or deliberately similar records.

### `tokens`

Maps normalized tokens or short n-grams to asset ids.

This powers related-item lookup such as finding assets that share `Nachteil`, `vorbereitet`, or `an Bord`, without treating them as exact reset candidates.

### `items`

Stores compact display metadata by id:

- `id`
- `type`
- `title`
- `content`
- `english`
- `collocation`
- `status`
- `priority`
- `reset_count`

This lets capture and review commands show useful context without reopening and scanning the full YAML for every match.

---

## Lookup Semantics

Lookup should distinguish exact reset candidates from related context.

Exact matches:

- Normalize the incoming target.
- Compare against normalized `content`, `title`, and core collocation forms.
- Return a durable hit only when the reusable target is materially the same asset.

Related matches:

- Tokenize the incoming target.
- Query token and n-gram overlap.
- Exclude exact matches.
- Return a small number of high-signal related assets.
- Use related matches only in dry-run notes, not as reset candidates.

This distinction matters because duplicate user-marking is a learning signal, while merely related expressions should not reset an existing asset.

---

## Workflow Boundaries

### Capture

Capture should use the index to identify durable hits before writing a session file. When a staged target matches an existing asset, the session note should keep the item visible and mark it with `durable_hit: <asset_id> -> reset candidate`.

Related but different items should be mentioned briefly in `Dry Run Notes` when they help the user understand overlap with the existing library.

### Commit

Commit should use the same normalization and exact lookup semantics as capture. If the reviewed session still contains a durable-hit target, commit should reset the existing asset rather than minting a duplicate.

After a successful durable commit, the index should be refreshed from `assets.yaml`.

### Review

Review does not need the index for correctness, because review state is keyed by durable asset id. It may use the compact `items` metadata later to support faster filtering or review selection.

### Dashboard

Dashboard generation may continue reading `assets.yaml` directly for full data. If dashboard queries become slow, it can later reuse `asset_index.json` for summary lookups while treating YAML as authoritative.

---

## Failure Handling

The system should treat a missing or stale index as recoverable.

- If `asset_index.json` is missing, rebuild it from `assets.yaml`.
- If JSON parsing fails, discard and rebuild the generated index.
- If rebuild fails because `assets.yaml` is invalid, stop and report the YAML problem rather than falling back to partial results.
- If lookup finds multiple exact ids for one normalized key, report the ambiguity and choose the oldest existing asset only when commit behavior needs a deterministic target.

---

## Evolution Path

The JSON index should be the first implementation. It is enough for hundreds or low thousands of assets and keeps the system easy to inspect.

SQLite with FTS should be considered only when one of these becomes true:

- exact and related lookup over JSON is measurably slow;
- review or dashboard needs richer filtered queries;
- the asset library grows beyond what is comfortable to load as one YAML list;
- ranking related assets becomes more important than deterministic matching.

Embeddings should remain out of scope until the workflow needs semantic discovery rather than duplicate and related-target detection.

---

## Future Extensions

These extensions are intentionally outside the first version, but the index design should leave room for them.

### SQLite Full-Text Index

If JSON lookup becomes too limited, the generated index can move to SQLite with FTS5. This would support faster filtered searches by `type`, `status`, `priority`, `reset_count`, source session, and full-text terms across `title`, `content`, `english`, `collocation`, and `transcript_sentence`.

SQLite should still be generated from `assets.yaml`; it should not become the canonical store unless a later design explicitly changes the persistence model.

### Linguistic Normalization Layer

A later version can add a small German-specific normalization layer for high-value cases:

- inflected verb forms to infinitives, such as `vorkommt` -> `vorkommen`;
- separable verb recognition, such as `richtet ... auf` -> `auf etw. richten`;
- article and case noise reduction for noun phrases;
- optional synonym or near-synonym aliases curated by the user.

This should start as a conservative local rule table, not a broad automatic grammar engine.

### Asset Aliases

Assets may eventually need explicit aliases for forms that should resolve to the same durable target but should not overwrite the canonical `content`.

Example:

```yaml
aliases:
  - kommt vor
  - ist vorgekommen
```

Aliases would let capture detect repeated learning targets without changing the preferred study form.

### Duplicate Hygiene Reports

The index can support periodic reports that identify likely duplicate or overlapping durable assets. These reports should be advisory only: they can suggest merge candidates, but actual merging should remain a separate confirmed maintenance step.

Useful report categories:

- exact normalized duplicates;
- title/content duplicates with different asset ids;
- collocations that duplicate another asset's main content;
- highly overlapping phrases that may need consolidation;
- frequently reset items that may need higher priority or a different study form.

### Review Prioritization Signals

Index metadata can later help review selection without changing the review-state model. For example, review could prioritize:

- assets with high `reset_count`;
- clusters of related weak items;
- recently captured items that overlap with older weak assets;
- patterns that appear across multiple transcript topics.

This should remain a selection aid. The authoritative review state should still live in `shadow_reviews/review_state.yaml`.

### Semantic Discovery

Embeddings or semantic search may become useful when the goal changes from duplicate detection to discovery, such as finding all assets related to "security risk", "policy response", or "technical capability" even when wording differs.

This should be a later optional layer because semantic search is harder to audit and less deterministic than exact or token-based lookup. It should never decide reset candidates by itself.

### Dashboard Search UI

The dashboard can eventually expose the same lookup layer as a small local search interface. This would let the user search the durable library by German text, English gloss, type, status, source session, and reset count.

The dashboard should read from generated index data for speed but link back to the canonical asset id and source session for inspection.

---

## Decision Log

### [2026-05-07] Keep YAML canonical and add a generated JSON index

**Decision:** Keep `shadow_assets/assets.yaml` as the source of truth and add `shadow_assets/asset_index.json` as a generated lookup cache.

**Alternatives considered:** Split the YAML store into many files, replace YAML with SQLite, or add embedding/vector search.

**Reason:** The current problem is lookup efficiency and agent context pressure, not durable storage correctness. A generated JSON index solves the immediate retrieval problem while preserving the existing local, readable, diffable workflow.

### [2026-05-07] Share lookup semantics between capture and commit

**Decision:** Move normalization and durable-hit lookup into a shared helper module used by both capture and commit paths.

**Alternatives considered:** Keep ad hoc lookup logic inside each command, or let the agent manually search the durable store during capture.

**Reason:** Capture and commit must agree on what counts as the same durable target. Shared code reduces drift and prevents a session from marking one item as new while commit later treats it as a reset, or the reverse.
