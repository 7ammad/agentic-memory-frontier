# Changelog

Canonical repo-level timeline for Agentic Memory System changes.

Use this file for high-signal changes only: shipped behavior, plan changes, verification results, newly discovered gaps, mistakes, and status changes. Put deeper reasoning and follow-up detail in `docs/PROJECT-LEDGER.md`.

## 2026-05-29

### Added

- Locked the **CEM-1 Full Kernel Build** contract (Phase 0). New evidence primitives `VerificationProbe`, `VerificationResult`, `ActionBriefRecord`, `ActionInfluenceEvent`, plus `ConfidenceInterval` and the `ExpectedActionDeltaSource` enum.
- Extended `ExperienceCard` with lifecycle fields (`promotion_status`, `measured_lift`, `measured_lift_ci`, `verification_result_ids`, deactivation/supersession) and `ActionBrief` with influence/scoring fields.
- Added SQLite + in-memory persistence for verification probes, verification results, action-brief records, and action-influence events in both store backends.
- Added `apply_verification_result()` to the kernel — the only path that can set a card `promotion_status="verified"`.
- Added `packages/cem-eval/src/cem_eval/eval_protocol.py`: the locked Marginal Memory Advantage metric (paired delta + 95% CI), the 10-baseline ladder (`human_runbook` flagged ceiling), the >=5pp lexical-overlap margin, and a leakage guard.
- Added `tests/test_no_fake_green_guard.py`: a static AST guard that fails new literal-bool health checks (the two `operations.py` offenders pinned as tracked debt).
- Added `docs/2026-05-28-cem-1-phase-0-contract-lock-plan.md` (Phase 0 implementation plan).
- Completed **Phase 1 (full vertical skeleton)**: a real end-to-end `trace -> atom -> validate -> candidate card -> action brief -> influence event` loop on persisted SQLite objects, no stubs. `retrieve_action_brief` now persists an `ActionBriefRecord` and emits a sourced `expected_action_delta` (`observational_unverified` when cards are selected, otherwise `none`); `close_influence` writes an observational `ActionInfluenceEvent` that never promotes a card or sets `measured_lift`.
- Added `packages/cem-eval/src/cem_eval/vertical_loop.py` (`run_vertical_loop` + `VerticalLoopReport`) and `scripts/run_cem_vertical_loop.py` as a real CLI consumer. Report counts come from real store queries; the runner enforces the leakage guard. First loop: MMA 1.0, n=2, CI [1.0, 1.0] (toy skeleton smoke, not the Phase 4 exam). Scorer stays `lexical_overlap_v0` (the action-value scorer is Phase 3).
- Added `docs/2026-05-29-cem-1-phase-1-vertical-skeleton-plan.md` (Phase 1 implementation plan).

### Changed

- Fixed the asserted-promotion bug: `promote()` now creates/updates a **candidate** card only and no longer flips the atom or card to `verified`. Verification is a separate, evidence-gated step via `apply_verification_result()`. `audit()` now reports a card's real `promotion_status` instead of a hardcoded `"verified"`.

### Verification

- **Phase 0:** `python -m pytest` -> 82 passed (21 new Phase 0 tests, including failure canaries for the promotion bug, the audit status, the MMA success bar, the leakage guard, and the no-fake-green guard).
- **Phase 1:** `python -m pytest` -> 91 passed (9 new Phase 1 tests, including failure canaries for untagged action-delta, `close_influence` never verifying a card, and the vertical-loop leakage guard). An independent verifier subagent confirmed real-green, all three canaries bite (break -> fail -> revert -> pass), no ghost code (every new symbol has a real caller), and no Phase 2/3 scope leak (MMA computed not hardcoded; `scorer_version` uniformly `lexical_overlap_v0`).
- `python -m compileall -q packages scripts tests`, `python scripts/run_cem_vertical_loop.py`, `python scripts/run_synthetic_eval.py`, `scripts/session-start-gate.ps1`, and `git diff --check` all clean.

## 2026-05-28

### Added

- Added `CHANGELOG.md` as the canonical human-readable change timeline.
- Added `docs/PROJECT-LEDGER.md` as the deeper engineering ledger for decisions, gaps, mistakes, and verification state.
- Added scoped dashboard/monitor status so AMS/CEM records are separated from global Codex behavior records.
- Added explicit current-phase and next-step output to `python scripts/ams.py dashboard` and monitor records.
- Added `python scripts/ams.py startup-brief` as the first Memory Use Controller command with allow/block status, monitor linkage, evidence ids, scoped retrieval, and bounded output.
- Wired `scripts/session-start-gate.ps1` through `startup-brief` so startup execution now blocks when required AMS memory is missing.
- Added `python scripts/ams.py correction ...` as the first Correction Capture Controller surface with live correction classification, affected file/action recording, directive/CEM/ledger routing, resume gate, and event ledgers.
- Added `docs/2026-05-28-ams-v1.3-correction-capture-controller-plan.md` to make live correction capture part of AMS architecture instead of Vol.

### Changed

- Promoted the AMS operating target from "memory exists and can be queried" to "agents must use bounded, auditable retrieval before acting."
- Clarified that startup memory behavior must be action-brief-first and bounded. AMS must not load the full memory corpus into every session.
- Monitor-0 now checks minimum AMS-scoped directives and learned AMS cards instead of trusting total record counts.
- Monitor-0 now checks correction-controller wiring, active resume gates, correction event visibility, and correction directive surfacing.
- Correction resume now updates the stored event status, so `correction list` does not report a cleared event as still blocked.
- The next active phase is now explicit in repo output: `AMS v1.3 Correction Capture Controller`.

### Gap Identified

- Agent behavior was not fully governed by AMS. The system had memory primitives (`brief`, directives, Monitor-0, provenance), but no universal runtime controller forcing agents to retrieve and attach a bounded memory brief before work.
- The first session-start gate was a useful stopgap, but it checked directive presence rather than enforcing the full bounded startup-brief contract.
- AMS still lacked the live correction loop: it validated memories after traces, but did not intercept mistakes while the agent was actively drifting.

### Mistake Logged

- AMS was initially treated too much like a project-local artifact instead of global agent infrastructure.
- Memory loading happened reactively in-session instead of being enforced as a pre-execution control.
- Codex started Vol implementation before the full plan was approved. AMS now treats that class of correction as a first-class capture event.

### Verified

- `python -m pytest` passed.
- `python -m compileall -q packages scripts tests` passed.
- `python scripts/run_synthetic_eval.py` passed with CEM-0 false-memory resistance, contradiction precision/recall, and action-brief pollution still clean.
- `python scripts/ams.py monitor --deep` passed with correction-controller checks.
- `scripts/session-start-gate.ps1` passed after the controller update.

### Next

- Continue the live control layer:
  - wire Correction Capture Controller into live agent runtime hooks beyond the CLI surface;
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
