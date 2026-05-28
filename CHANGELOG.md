# Changelog

Canonical repo-level timeline for Agentic Memory System changes.

Use this file for high-signal changes only: shipped behavior, plan changes, verification results, newly discovered gaps, mistakes, and status changes. Put deeper reasoning and follow-up detail in `docs/PROJECT-LEDGER.md`.

## 2026-05-28

### Added

- Added `CHANGELOG.md` as the canonical human-readable change timeline.
- Added `docs/PROJECT-LEDGER.md` as the deeper engineering ledger for decisions, gaps, mistakes, and verification state.
- Added scoped dashboard/monitor status so AMS/CEM records are separated from global Codex behavior records.
- Added explicit current-phase and next-step output to `python scripts/ams.py dashboard` and monitor records.
- Added `python scripts/ams.py startup-brief` as the first Memory Use Controller command with allow/block status, monitor linkage, evidence ids, scoped retrieval, and bounded output.
- Wired `scripts/session-start-gate.ps1` through `startup-brief` so startup execution now blocks when required AMS memory is missing.

### Changed

- Promoted the AMS operating target from "memory exists and can be queried" to "agents must use bounded, auditable retrieval before acting."
- Clarified that startup memory behavior must be action-brief-first and bounded. AMS must not load the full memory corpus into every session.
- Monitor-0 now checks minimum AMS-scoped directives and learned AMS cards instead of trusting total record counts.
- The next active phase is now explicit in repo output: `AMS v1.2 Memory Use Controller`.

### Gap Identified

- Agent behavior was not fully governed by AMS. The system had memory primitives (`brief`, directives, Monitor-0, provenance), but no universal runtime controller forcing agents to retrieve and attach a bounded memory brief before work.
- The first session-start gate was a useful stopgap, but it checked directive presence rather than enforcing the full bounded startup-brief contract.

### Mistake Logged

- AMS was initially treated too much like a project-local artifact instead of global agent infrastructure.
- Memory loading happened reactively in-session instead of being enforced as a pre-execution control.

### Next

- Continue the Memory Use Controller:
  - verify global `ams-memory` MCP availability after Codex restart;
  - add latency budget enforcement;
  - attach `brief_id`, `monitor_id`, and evidence ids to broader governed agent work;
  - extend controller coverage beyond session-start gating.

## 2026-05-27

### Added

- Implemented AMS v1 usable local memory workflow around CEM-0:
  - `init`;
  - `session`;
  - `remember`;
  - `pin`;
  - `bootstrap-codex`;
  - `brief`;
  - `list`;
  - `audit`;
  - `eval`.
- Implemented AMS v1.1 migration and Monitor-0 operator workflow:
  - curated migration records;
  - monitor records;
  - dashboard summary.
- Added global AMS environment roots:
  - `AMS_ROOT=C:\Users\7amma\.codex\memory\cem`;
  - `CEM_ROOT=C:\Users\7amma\.codex\memory\cem`.
- Added global Codex MCP registration for `ams-memory` in `C:\Users\7amma\.codex\config.toml`.
- Added `scripts/session-start-gate.ps1` as a first enforcement gate for AMS directive availability.

### Verified

- `python scripts/ams.py monitor --deep` passed.
- `python scripts/ams.py dashboard` returned a live global AMS root.
- Cross-project CLI smoke from `C:\Dev\Builds\Playground-and-testing` reached the same AMS root and returned AMS directives.
- `scripts/session-start-gate.ps1` passed with 13 loaded directives.

### Gap Identified

- Codex runtime restart is required before new global MCP registration is active in every session.
- CLI cross-project proof exists, but full in-agent MCP proof after restart remains the true readiness check.

## 2026-05-26

### Completed

- A: Deep technical review of SuperClaude memory MCP - DONE and VERIFIED.
- B: SuperClaude memory v0.3 upgrade spec - DONE and VERIFIED.
- C: Codex memory system design - DONE and VERIFIED.
- D: ACS protocol design - DONE and VERIFIED.

### Verified

- C design reached READY after 3 Codex verification passes.
- D design reached READY after 4 Codex verification passes.

### Locked Rules

- Do not continue from PATCH-FIRST as if it is ready.
- Run strict verification between major sub-projects.
- Do not read or write `C:\Dev\Builds\Waki` from this workspace.
