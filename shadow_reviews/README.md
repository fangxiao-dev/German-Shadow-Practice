# shadow_reviews

Purpose:
- Store review drafts, review state, and the durable review log for shadow practice.
- Keep draft review output separate from final state updates.

Lifecycle:
- `review` writes a draft record under `shadow_reviews\review_drafts\`.
- `report` rereads the saved draft, summarizes suggested solid items, weak or revisit items, and observed mistakes.
- The confirmation/update phase happens within `report` after grouped user feedback, and then updates `review_state.yaml` and appends a short outcome to `review_log.md`.

Rules:
- Drafts are temporary and may be replaced.
- Final review state stays in `review_state.yaml`.
- Final human-readable outcomes stay in `review_log.md`.
