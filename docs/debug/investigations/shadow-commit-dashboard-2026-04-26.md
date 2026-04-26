---
status: active
doc_type: investigation
source_of_truth: current code + shadow skills
last_verified_at: 2026-04-26
---

# Shadow Commit Dashboard Follow-Up

## Context

During `shadow-commit` for `shadow_sessions/2026-04-26-1004.md`, the durable asset commit succeeded, but the workflow did not initially use the existing helper script and dashboard follow-up needed multiple attempts.

## Root Causes

- `shadow-commit` skill documentation did not name `scripts/shadow_commit.py` as the preferred execution path, so the agent followed the generic YAML contract manually.
- Dashboard data rebuild failed inside the sandbox with `PermissionError` for `dashboard/data/dashboard-data.json`, even though the file and directory ACLs allowed modification.
- A background `python -m http.server` process launched inside the sandbox exited silently; launching the same server path outside the sandbox made `http://127.0.0.1:4173/` reachable.

## Correct Next-Time Path

1. For commit, run the helper script first:

   ```powershell
   python E:\Personal\学德语\scripts\shadow_commit.py
   ```

2. If a session path is explicit, pass it:

   ```powershell
   python E:\Personal\学德语\scripts\shadow_commit.py --session E:\Personal\学德语\shadow_sessions\YYYY-MM-DD-HHMM.md
   ```

3. If the command fails, identify the failing boundary before changing approach:
   - durable YAML write
   - dashboard data rebuild
   - dashboard server start
   - browser open

4. For sandbox write/listener/browser failures, rerun the same helper-script path with escalation before replacing it with manual YAML edits or piecemeal dashboard commands.

## Guardrail

Do not rerun `shadow_commit.py` against an already committed session unless idempotency has been added. Current behavior treats existing targets as repeated hits, resets them, and appends another commit log entry.
