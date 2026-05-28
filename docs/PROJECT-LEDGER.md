# Project Ledger

Canonical engineering ledger for Agentic Memory System.

This file records decisions, gaps, mistakes, plan updates, verification evidence, and follow-up actions. It is intentionally more detailed than `CHANGELOG.md`.

## How To Update

Add a new entry whenever one of these changes:

- architecture direction;
- plan scope;
- readiness status;
- verification result;
- discovered gap;
- mistake or operational failure;
- cross-agent/runtime behavior;
- acceptance criteria.

Entry format:

```text
## LEDGER-YYYYMMDD-NNN - Short title

- Date:
- Type: decision | gap | mistake | plan-update | verification | status
- Status: open | active | resolved | superseded
- Source:
- Summary:
- Files:
- Verification:
- Follow-up:
```

## LEDGER-20260528-001 - Canonical changelog and ledger added

- Date: 2026-05-28
- Type: plan-update
- Status: active
- Source: User asked whether the repo has a changelog to track changes, plan updates, gaps, and mistakes.
- Summary: Added `CHANGELOG.md` for concise repo timeline and `docs/PROJECT-LEDGER.md` for deeper engineering state.
- Files:
  - `CHANGELOG.md`
  - `docs/PROJECT-LEDGER.md`
  - `AGENTS.md`
- Verification: `rg` confirmed the changelog, ledger, AGENTS rule, and Memory Use Controller follow-ups are present.
- Follow-up: Keep both files updated before or alongside future plan changes.

## LEDGER-20260528-002 - AMS must govern agent behavior, not only store memory

- Date: 2026-05-28
- Type: decision
- Status: active
- Source: User challenged whether agents can ignore memory or overfill context, and asked which plan component addresses that.
- Summary: AMS target is now explicit: agents must use bounded, auditable memory retrieval before acting. Storage alone is insufficient.
- Files:
  - `README.md`
  - `docs/2026-05-27-ams-v1-usable-memory-plan.md`
  - `docs/2026-05-27-ams-v1.1-migration-monitor-plan.md`
  - `specs/2026-05-27-cem-0-memguard-kernel-spec.md`
- Verification: Source review confirmed `brief`, Monitor-0, directives, provenance, and validation exist as primitives.
- Follow-up: Implement a Memory Use Controller that wraps each agent session/task.

## LEDGER-20260528-003 - Full-memory startup load is rejected

- Date: 2026-05-28
- Type: decision
- Status: active
- Source: User questioned whether the memory gate would load every memory into every session.
- Summary: AMS startup behavior must not load the full corpus. Startup retrieval must be bounded to health, required directives, and top-k action brief. Further retrieval must be lazy, scoped, capped, and auditable.
- Files:
  - `packages/cem-core/src/cem_core/cli.py`
  - `packages/cem-core/src/cem_core/kernel.py`
  - `packages/cem-core/src/cem_core/local_memory.py`
- Verification: Existing `brief` command has `--max-cards` defaulting to 5; CEM retrieval selects top matching cards.
- Follow-up: Add explicit directive cap, token cap, and latency budget to startup brief.

## LEDGER-20260528-004 - Project-local AMS wiring was an operational miss

- Date: 2026-05-28
- Type: mistake
- Status: active
- Source: User pointed out that building a memory system and keeping it project-local defeats the point.
- Summary: AMS was initially validated as a local project tool before being treated as global runtime infrastructure. That created a real cross-project failure mode.
- Files:
  - `C:\Users\7amma\.codex\config.toml`
  - `scripts/session-start-gate.ps1`
- Verification: Cross-project CLI smoke from `C:\Dev\Builds\Playground-and-testing` reached global AMS root.
- Follow-up: After Codex restart, verify `ams-memory` MCP tools are available inside a separate project session.

## LEDGER-20260528-005 - Session-start memory gate is a stopgap

- Date: 2026-05-28
- Type: gap
- Status: resolved
- Source: User challenged the first direct fix as potentially too shallow and context-expensive.
- Summary: `scripts/session-start-gate.ps1` originally enforced directive availability only. It now calls `startup-brief`, retrieves a bounded startup brief, records brief/monitor/evidence ids, and blocks execution when required directives are missing. Broader governed-work attachment remains open under LEDGER-20260528-008.
- Files:
  - `scripts/session-start-gate.ps1`
  - `AGENTS.md`
- Verification: Gate passed through `startup-brief` and emitted brief, monitor, and evidence ids.
- Follow-up: Continue broader Memory Use Controller work under LEDGER-20260528-008.

## LEDGER-20260528-006 - No conservative alternate track when pace is locked

- Date: 2026-05-28
- Type: mistake
- Status: active
- Source: User flagged prior answer that offered a slower/safe track after explicitly rejecting conservative execution framing.
- Summary: For high-conviction AMS/system work, do not trim scope into cautious scaffolding or offer conservative padding unless the user asks for risk options. Keep verification gates, but execute the full system shape.
- Files:
  - `C:\Users\7amma\.codex\memory\cem\directives.json`
- Verification: AMS directive `directive_402fa6c213a04a22ae8aeaa41cd234e0` says not to trim high-conviction system builds into cautious Markdown skeletons.
- Follow-up: Encode this behavior in Memory Use Controller required-directive checks.

## LEDGER-20260528-007 - Monitor status must be scoped, not only alive

- Date: 2026-05-28
- Type: status
- Status: active
- Source: User asked whether overnight Monitor-0 runs are being recorded and where the project stands.
- Summary: Monitor/dashboard now report total records separately from AMS/CEM operational records and global Codex behavior directives. The dashboard also exposes the completed-through milestone, current phase, and next step.
- Files:
  - `packages/cem-core/src/cem_core/operations.py`
  - `packages/cem-core/src/cem_core/cli.py`
  - `tests/test_ams_cli.py`
  - `README.md`
  - `TODO.md`
- Verification: `python -m pytest`, `python -m compileall -q packages scripts tests`, `python scripts/run_synthetic_eval.py`, `python scripts/ams.py monitor --deep`, `git diff --check`, and credential-pattern scan passed.
- Follow-up: Continue Memory Use Controller work beyond session-start gating.

## LEDGER-20260528-008 - Startup brief becomes the first controller surface

- Date: 2026-05-28
- Type: plan-update
- Status: active
- Source: User asked when the next phase starts and wanted the status to be clear from the monitoring system.
- Summary: Added `startup-brief` as the first bounded Memory Use Controller surface. It runs a quick monitor, retrieves a scoped action brief, enforces required startup directives, caps directives/cards/evidence/actions, records the brief, and returns `allow` or `block`. The session-start gate now calls this command and blocks when the brief is not allowed.
- Files:
  - `packages/cem-core/src/cem_core/operations.py`
  - `packages/cem-core/src/cem_core/cli.py`
  - `tests/test_ams_cli.py`
  - `README.md`
  - `TODO.md`
- Verification: `python -m pytest` passed with startup-brief allow/block tests; `scripts/session-start-gate.ps1` passed and emitted brief, monitor, and evidence ids.
- Follow-up: Verify global `ams-memory` MCP availability after Codex runtime restart and attach brief ids to broader governed agent work.

## Open Follow-Ups

- Add latency budget enforcement to the startup controller.
- Record `brief_id`, `monitor_id`, and evidence ids for every governed agent run, not only session-start gate output.
- Verify global `ams-memory` MCP availability after Codex runtime restart.
