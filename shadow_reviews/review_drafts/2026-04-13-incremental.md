# Incremental Review Draft

- source_assets: `E:\Personal\学德语\shadow_assets\assets.yaml`
- source_state: `E:\Personal\学德语\shadow_reviews\review_state.yaml`
- session_date: `2026-04-13`
- scope: `incremental`
- status: `draft`

## Selection Rationale

- Prioritize new items because there are no weak items yet.
- Keep the set compact for a first review pass.
- Mix `word`, `phrase`, and `pattern` items so recall is not too narrow.

## Review Set

1. `Henne-Ei-Problem` (`phrase`)
   cue: How would you describe a situation where both sides depend on each other to start?
   target: `Henne-Ei-Problem`

2. `nachweisen` (`word`)
   cue: Which verb would you use for "prove/show with evidence" in a formal context?
   target: `nachweisen`

3. `Kontakt herstellen` (`phrase`)
   cue: How do you say "to establish contact"?
   target: `Kontakt herstellen`

4. `Wie geht ihr damit um?` (`pattern`)
   cue: Ask a company or team how they deal with a difficult issue.
   target: `Wie geht ihr damit um?`

5. `wir machen kein Geheimnis draus` (`phrase`)
   cue: Say openly that you are not hiding something.
   target: `wir machen kein Geheimnis draus`

6. `aus meiner Sicht` (`pattern`)
   cue: Start a sentence with "from my point of view".
   target: `aus meiner Sicht`

7. `in den Fokus rücken` (`phrase`)
   cue: Which phrase means "to bring something into focus / public attention"?
   target: `in den Fokus rücken`

8. `Es ist ganz klar, ...` (`pattern`)
   cue: Start a strong opinion sentence with a clear stance-taking frame.
   target: `Es ist ganz klar, ...`

## Simulated User Answers

1. `Henne-Ei-Problem`
   simulated_answer: `Das ist so ein Problem, wo man erst A braucht, um B zu machen, aber auch B braucht, um A zu bekommen.`
   assessment: meaning recalled; exact phrase not produced

2. `nachweisen`
   simulated_answer: `beweisen`
   assessment: near-synonym recalled; target verb not retrieved

3. `Kontakt herstellen`
   simulated_answer: `mit Kunden Kontakt herstellen`
   assessment: correct and usable

4. `Wie geht ihr damit um?`
   simulated_answer: `Wie geht ihr damit um?`
   assessment: exact frame retrieved

5. `wir machen kein Geheimnis draus`
   simulated_answer: `Wir verstecken das nicht.`
   assessment: meaning recalled; idiomatic target missed

6. `aus meiner Sicht`
   simulated_answer: `aus meiner Sicht ist das wichtig`
   assessment: exact frame retrieved

7. `in den Fokus rücken`
   simulated_answer: `mehr im Fokus sein`
   assessment: related expression recalled; target phrase partial

8. `Es ist ganz klar, ...`
   simulated_answer: `Es ist klar, dass ...`
   assessment: near-match; target frame simplified

## Suggested Report Inputs

- suggested_solid:
  - `Kontakt herstellen`
  - `Wie geht ihr damit um?`
  - `aus meiner Sicht`

- suggested_learning:
  - `Henne-Ei-Problem`
  - `nachweisen`
  - `wir machen kein Geheimnis draus`
  - `in den Fokus rücken`
  - `Es ist ganz klar, ...`

- suggested_weak:
  - none for the first incremental pass unless the user felt strong hesitation

- observed_patterns:
  - Meaning is often available before the exact target wording.
  - Idiomatic chunks are less stable than transparent question frames.
  - Near-synonyms appear quickly, so later review should push exact retrieval.
