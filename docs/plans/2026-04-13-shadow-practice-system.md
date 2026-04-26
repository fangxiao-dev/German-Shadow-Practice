# Shadow Practice System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local, skill-driven workflow that captures transcript files into structured assets, tracks review state, and supports review/report loops without depending on chat context.

**Architecture:** The implementation creates a file-backed knowledge layout plus a `shadow-practice` skill that defines the capture, commit, review, and report workflows. The system stores provisional session data separately from durable assets and review state so the permanent library remains user-confirmed and review decisions are reproducible from local files.

**Tech Stack:** Markdown files for session/report records, YAML files for durable asset and review state, local directories, Codex/Claude-style skill prompt files, optional lightweight helper scripts if the prompt-only workflow becomes too fragile.

---

### Task 1: Create the runtime folder structure

**Files:**
- Create: `E:\Personal\学德语\shadow_sessions\.gitkeep`
- Create: `E:\Personal\学德语\shadow_assets\assets.yaml`
- Create: `E:\Personal\学德语\shadow_reviews\review_state.yaml`
- Create: `E:\Personal\学德语\shadow_reviews\review_log.md`
- Create: `E:\Personal\学德语\shadow_reviews\review_drafts\.gitkeep`

**Step 1: Create the directories and placeholder files**

Create the folder tree and initial empty markdown files with short headers describing each file's role.

**Step 2: Verify the structure exists**

Run: `Get-ChildItem -Recurse 'E:\Personal\学德语\shadow_*'`
Expected: the four top-level directories/files appear in the correct locations.

**Step 3: Add minimal file headers**

Write short file headers so later agent turns can infer each file's purpose without guessing.

**Step 4: Verify the files are readable**

Run: `Get-Content 'E:\Personal\学德语\shadow_assets\assets.yaml'`
Expected: header text renders and file is not empty.

**Step 5: Commit**

```bash
git add shadow_sessions shadow_assets shadow_reviews
git commit -m "chore: initialize shadow practice runtime files"
```

### Task 2: Create the shadow-practice skill scaffold

**Files:**
- Create: `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`
- Create: `E:\Personal\学德语\.agents\skills\shadow-practice\examples.md`

**Step 1: Write the skill contract**

Document the supported commands:

- `capture`
- `commit`
- `review`
- `report`

State clearly which files each command may read and write.

**Step 2: Define the input format**

Document the transcript-file-plus-separator format:

```text
<transcript content from raw-transcripts/...>

---
- must keep item
- must keep item
```

Explain that transcript source files live under `raw-transcripts/`, that bullet items are mandatory candidates, and that the agent must infer `word`, `phrase`, or `pattern`.

**Step 3: Add command examples**

Write concrete examples for all four commands using local file paths and realistic German learning content.

**Step 4: Verify the skill file is readable**

Run: `Get-Content 'E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md'`
Expected: the command contract and file-boundary rules are present.

**Step 5: Commit**

```bash
git add .agents/skills/shadow-practice
git commit -m "feat: add shadow practice skill scaffold"
```

### Task 3: Define the asset and review schemas

**Files:**
- Modify: `E:\Personal\学德语\shadow_assets\assets.yaml`
- Modify: `E:\Personal\学德语\shadow_reviews\review_state.yaml`
- Modify: `E:\Personal\学德语\shadow_reviews\review_log.md`

**Step 1: Write the asset schema**

Add a markdown section documenting required fields:

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

**Step 2: Write the status rules**

Document that `status` is mutually exclusive and limited to:

- `new`
- `learning`
- `weak`
- `solid`

**Step 3: Write the review draft/log conventions**

Define what a draft review file must contain and how final report outcomes should be copied into `review_log.md`.

**Step 4: Verify the conventions are explicit**

Run: `Get-Content 'E:\Personal\学德语\shadow_reviews\review_state.yaml'`
Expected: a future agent can infer how to update state without inventing a format.

**Step 5: Commit**

```bash
git add shadow_assets/assets.yaml shadow_reviews/review_state.yaml shadow_reviews/review_log.md
git commit -m "docs: define shadow asset and review schemas"
```

### Task 4: Specify the capture and commit behavior

**Files:**
- Modify: `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`
- Create: `E:\Personal\学德语\shadow_sessions\README.md`

**Step 1: Write capture behavior**

State that `capture` must:

- parse the transcript from a local raw-transcript file and the `must_keep` list
- classify must-keep items into asset types
- propose a small number of recommendation items that fill obvious omissions
- write a session file that references the source transcript path instead of copying the full transcript
- avoid writing the permanent asset store
- keep `Must Keep Candidates` and `Recommendations` as separate sections with the same item fields
- use `collocation` or `collocations` only for subordinate memory hooks attached to a target, not as separate assets
- do not promote sentence-level discourse framing into `Recommendations` when the user's marked items already capture the substantive payload

**Step 2: Write commit behavior**

State that `commit` must:

- read the most recent relevant session file
- include all confirmed must-keep items
- include only user-approved recommendation items
- append durable records to the asset store and review state

**Step 3: Add a session file naming rule**

Document a stable naming pattern such as `YYYY-MM-DD-HHMM.md`.

**Step 4: Verify capture/commit boundary clarity**

Run: `Select-String -Path 'E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md' -Pattern 'capture|commit'`
Expected: both commands mention what they can and cannot write.

**Step 5: Commit**

```bash
git add .agents/skills/shadow-practice/SKILL.md shadow_sessions/README.md
git commit -m "docs: define capture and commit workflow boundaries"
```

### Task 5: Specify the review and report behavior

**Files:**
- Modify: `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`
- Create: `E:\Personal\学德语\shadow_reviews\README.md`

**Step 1: Write review scope rules**

Document the three supported scopes:

- `incremental`
- `focus`
- `full`

State what each scope should prioritize.

**Step 2: Write draft-first review behavior**

State that `review` must write a draft record under `shadow_reviews/review_drafts/` and must not directly mutate final review state.

**Step 3: Write report confirmation/update behavior**

State that `report` must:

- reread the saved draft
- summarize suggested `solid` items
- summarize suggested `weak/revisit` items
- summarize observed mistakes
- wait for grouped user feedback before updating final state and review log
- treat the confirmation/update phase as part of `report`, not as a separate `apply` command

**Step 4: Verify the report flow**

Run: `Get-Content 'E:\Personal\学德语\shadow_reviews\README.md'`
Expected: the draft/report confirmation-update lifecycle is explicit and unambiguous.

**Step 5: Commit**

```bash
git add .agents/skills/shadow-practice/SKILL.md shadow_reviews/README.md
git commit -m "docs: define review and report lifecycle"
```

### Task 6: Add examples and edge-case rules

**Files:**
- Modify: `E:\Personal\学德语\.agents\skills\shadow-practice\examples.md`
- Modify: `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`

**Step 1: Add example capture sessions**

Include at least two examples:

- one dominated by phrases
- one with a clear pattern candidate

**Step 2: Add edge-case guidance**

Document behavior for:

- no `---` section present
- empty bullet list
- too many recommendation candidates
- ambiguous type classification

**Step 3: Add fallback rules**

State that ambiguous items default to `phrase`, and that abstract usage advice should become a note or be deferred to a later drill phase instead of becoming a v1 asset type.

**Step 4: Verify examples are actionable**

Run: `Get-Content 'E:\Personal\学德语\.agents\skills\shadow-practice\examples.md'`
Expected: a future agent can imitate the examples without guessing missing steps.

**Step 5: Commit**

```bash
git add .agents/skills/shadow-practice/SKILL.md .agents/skills/shadow-practice/examples.md
git commit -m "docs: add examples and edge-case rules for shadow practice"
```

### Task 7: Validate the documentation from a cold start

**Files:**
- Review only: `E:\Personal\学德语\docs\designs\shadow-practice-system.md`
- Review only: `E:\Personal\学德语\docs\plans\2026-04-13-shadow-practice-system.md`
- Review only: `E:\Personal\学德语\.agents\skills\shadow-practice\SKILL.md`
- Review only: `E:\Personal\学德语\shadow_assets\assets.yaml`
- Review only: `E:\Personal\学德语\shadow_reviews\review_state.yaml`

**Step 1: Read the system from scratch**

Read the design, plan, skill file, and state headers as if there is no chat context.

**Step 2: Check for lifecycle confusion**

Verify there is no overlap between:

- design rationale
- implementation tasks
- runtime state files

**Step 3: Check for missing file-boundary rules**

Verify that every command says what it may write and what it must not write.

**Step 4: Capture any ambiguity in follow-up notes**

If anything is still underspecified, update the relevant doc before implementation begins.

**Step 5: Commit**

```bash
git add docs/designs/shadow-practice-system.md docs/plans/2026-04-13-shadow-practice-system.md .agents/skills/shadow-practice shadow_assets shadow_reviews
git commit -m "docs: finalize shadow practice system planning"
```
