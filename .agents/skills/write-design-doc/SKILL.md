---
name: write-design-doc
description: "Use this skill after a brainstorming or planning session when the user wants to capture a Design document — NOT an implementation plan. Triggers include: 'write a design doc', 'capture the design', 'create a design document', 'help me write up the design'. This skill produces a long-lived, maintainable design artifact focused on WHY and WHAT (goals, feature-to-tech mapping, constraints, decisions), not HOW (implementation steps, tasks, timelines). The output goes to docs/designs/, not docs/plans/."
---

# Write Design Doc

## Purpose

A Design document captures the **intent and rationale** behind a feature or module. It is meant to be maintained over time — updated as decisions evolve, not replaced. It is distinct from an Implementation Plan, which is ephemeral and task-oriented.

**Design doc answers:** What is this? Why are we building it? What are the key technical choices and why? What is out of scope?

**Implementation plan answers:** What tasks need to be done, in what order, by when?

---

## Output Location

Always write design docs to:

```
docs/designs/<topic-slug>.md
```

Use a stable, descriptive slug based on the feature or module name (e.g., `sync-engine.md`, `auth-flow.md`, `data-export.md`). Do **not** include dates in the filename — this file will be updated in place over time.

---

## Document Structure

Generate the file with these sections, described in ./template.md:

---

## Behavior Instructions

1. **Infer from context.** If the user has just finished a brainstorm or there is an existing plan document in context, extract the relevant material — do not ask them to repeat themselves.

2. **Populate every section.** If information is missing for a section, write a short placeholder comment in italics (e.g., `_To be determined._`) rather than omitting the section. This keeps the document structurally complete for future editing.

3. **Solution Overview is a mapping, not a task list.** The table maps user-facing capabilities to the technical choices that enable them. If the user described features during brainstorming, use those as the Feature column. If they described technical choices, use those as the Approach column. Reconstruct the mapping from context.

4. **Decision Log starts with at least one entry.** Pull the most significant architectural or approach decision from the brainstorm and log it. The date should be today's date.

5. **Status defaults to `Draft`.** Only set to `Active` if the user explicitly says the design is finalized.

6. **Link to the plan if one exists.** If Writing Plans was already called and generated a file under `docs/plans/`, reference it in the header block.

7. **Do not duplicate the plan.** Tasks, timelines, and step-by-step instructions belong in the plan. If that content appears during brainstorming, acknowledge it but do not put it in the design doc.
