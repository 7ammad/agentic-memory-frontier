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

## LEDGER-20260528-009 - Global AMS MCP availability verified in Codex runtime

- Date: 2026-05-28
- Type: verification
- Status: resolved
- Source: TODO first unchecked item and live Codex MCP tool call.
- Summary: The active Codex runtime can reach the global `ams-memory` MCP server. The first `cem_retrieve_action_brief` call with an offset-aware `current_time` exposed a timezone comparison bug, and the follow-up call without `current_time` succeeded with the expected AMS action brief.
- Files:
  - `TODO.md`
  - `packages/cem-core/src/cem_core/mcp_tools.py`
- Verification: Live MCP `cem_retrieve_action_brief` returned cards `card_ea301b6b32a24987ace36f9ea1ef7c81` and `card_030551464aa44ae995af1e358ef99f86` after retry.
- Follow-up: Track the timezone comparison bug separately; it is not part of the Correction Capture Controller slice.

## LEDGER-20260528-010 - Correction Capture Controller added to AMS

- Date: 2026-05-28
- Type: plan-update
- Status: active
- Source: Vol handoff identified that AMS lacked live user-correction capture and should own it instead of Vol.
- Summary: Added `CorrectionCaptureController` as a first-class AMS module. It detects live correction language, classifies mistake categories, records affected files/actions, routes to directive/CEM/project ledger/stale-memory/human-gate targets, writes correction ledgers, blocks continuation through a resume gate, and surfaces correction-loop health in Monitor-0.
- Files:
  - `packages/cem-core/src/cem_core/correction_capture.py`
  - `packages/cem-core/src/cem_core/cli.py`
  - `packages/cem-core/src/cem_core/operations.py`
  - `packages/cem-core/src/cem_core/local_memory.py`
  - `tests/test_ams_cli.py`
  - `docs/2026-05-28-ams-v1.3-correction-capture-controller-plan.md`
  - `README.md`
  - `TODO.md`
  - `CHANGELOG.md`
- Verification: `python -m pytest tests/test_ams_cli.py` passed with 20 tests, including plan-first correction capture, repeated drift routing, action-brief retrieval, resume gate behavior, and event status update after resume. Full verification also passed: `python -m pytest`, `python -m compileall -q packages scripts tests`, `python scripts/run_synthetic_eval.py`, `python scripts/ams.py monitor --deep`, `scripts/session-start-gate.ps1`, `git diff --check`, and a high-confidence secret-pattern scan.
- Follow-up: Wire the controller into live agent runtime hooks beyond the CLI surface and fix the MCP timezone comparison bug found during action-brief retrieval.

## LEDGER-CORRECTION-20260528-39d81600 - premature implementation

- Date: 2026-05-28
- Type: mistake
- Status: active
- Source: Correction Capture Controller `correction_6f62bebc4e8c4a26b32b06d139d81600`
- Summary: Agent started implementation or scaffolding before the requested plan/approval gate was satisfied.
- Files:
  - `C:\Dev\Builds\Vibing Operating Layer\package.json`
  - `C:\Dev\Builds\Vibing Operating Layer\tsconfig.json`
  - `C:\Dev\Builds\Vibing Operating Layer\src\types.ts`
  - `C:\Dev\Builds\Vibing Operating Layer\src\fsx.ts`
  - `C:\Dev\Builds\Vibing Operating Layer\src\guards.ts`
  - `C:\Dev\Builds\Vibing Operating Layer\src\config.ts`
- Affected actions:
  - created implementation scaffold before full Vol plan approval
- Verification: Correction event recorded and resume gate opened.
- Follow-up: Resume only after explicit approval.

## LEDGER-CORRECTION-20260528-06f6a2d2 - repeated drift

- Date: 2026-05-28
- Type: mistake
- Status: active
- Source: Correction Capture Controller `correction_2c520b5ce2174ab2baae123706f6a2d2`
- Summary: Agent repeated behavior that had already been corrected or rejected.
- Files:
  - `packages/cem-core/src/cem_core/correction_capture.py`
  - `docs/2026-05-28-ams-v1.3-correction-capture-controller-plan.md`
  - `TODO.md`
  - `CHANGELOG.md`
  - `docs/PROJECT-LEDGER.md`
- Affected actions:
  - treated a manual correction recorder as an implementation-verified controller
  - responded with foundation/skeleton scope instead of full live behavioral control system
- Verification: Correction event recorded and resume gate opened.
- Follow-up: Resume only after explicit approval.

## LEDGER-20260528-011 - CEM-1 Full Kernel Build contract locked (Phase 0)

- Date: 2026-05-29
- Type: plan-update
- Status: active
- Source: User asked for the full Causal Experience Memory program from the original research (not a narrow proof slice, not a broad platform), under a hard no-ghost-coding / no-dropping constraint; refined by GPT Pro revised (round-2) feedback into the "CEM-1 Full Kernel Build" and Approach C (eval-first). Phase 0 = contract lock per `docs/2026-05-28-causal-experience-memory-full-program-design.md` sections 5, 6, 8, 10.
- Summary: Locked the build contract before any scorer tuning. (1) Added evidence primitives `VerificationProbe`, `VerificationResult`, `ActionBriefRecord`, `ActionInfluenceEvent`, plus `ConfidenceInterval` and the `ExpectedActionDeltaSource` enum. (2) Extended `ExperienceCard` (lifecycle: `promotion_status`, `measured_lift`, `measured_lift_ci`, `verification_result_ids`, deactivation/supersession) and `ActionBrief` (influence/scoring fields). (3) Added SQLite + in-memory persistence for probes, results, action-brief records, and influence events in both backends. (4) Fixed the asserted-promotion bug: `promote()` now only creates/updates a candidate card and never flips atom or card to `verified`; the new evidence-gated `apply_verification_result()` is the only path that can set `promotion_status="verified"`; `audit()` now reports a card's real status instead of a hardcoded `"verified"`. (5) Added `cem_eval/eval_protocol.py`: locked Marginal Memory Advantage metric (paired delta + 95% CI), the 10-baseline ladder (`human_runbook` flagged ceiling, not a must-beat), the >=5pp lexical-overlap margin, and the leakage guard. (6) Added a static AST no-fake-green guard that fails any new literal-bool health check, with the two `operations.py` offenders pinned as tracked debt.
- Files:
  - `packages/cem-core/src/cem_core/models.py`
  - `packages/cem-core/src/cem_core/storage.py`
  - `packages/cem-core/src/cem_core/kernel.py`
  - `packages/cem-eval/src/cem_eval/eval_protocol.py`
  - `tests/test_lifecycle_rules.py`
  - `tests/test_eval_protocol.py`
  - `tests/test_no_fake_green_guard.py`
  - `docs/2026-05-28-cem-1-phase-0-contract-lock-plan.md`
  - `CHANGELOG.md`
- Verification: `python -m pytest` -> 82 passed (21 new Phase 0 tests, including failure canaries for the promotion bug, the audit status, the MMA success bar, the leakage guard, and the no-fake-green guard). `python -m compileall -q packages scripts tests`, `python scripts/run_synthetic_eval.py`, `scripts/session-start-gate.ps1` (SESSION_GATE_PASS), and `git diff --check` all clean.
- Follow-up: Execute Phase 1 (full vertical skeleton: trace -> atom -> card -> action brief -> influence event with real persisted state at every hop, no stubs), then Phases 2-5 (grounded consolidation + verification; action-value retrieval; MMA + baseline ladder exam; hardening).

## LEDGER-20260529-012 - CEM-1 Phase 1 full vertical skeleton landed and verified

- Date: 2026-05-29
- Type: verification
- Status: resolved
- Source: Standing user directive to build the full CEM program end-to-end with no ghost coding / no fake-green; Phase 1 per `docs/2026-05-29-cem-1-phase-1-vertical-skeleton-plan.md` (round-2 phase sequencing).
- Summary: Built the first real end-to-end loop on persisted objects, no stubs. (1) `retrieve_action_brief` now enriches the brief with `influence_id`, `scorer_version`, a per-card `score_breakdown_by_card`, and a sourced `expected_action_delta` (`observational_unverified` when cards are selected, `none`/`None` when not) and persists an `ActionBriefRecord` on every call. (2) Added `close_influence(brief_id, ...)` writing an observational `ActionInfluenceEvent` (defaults `counterfactual_method="observational_no_counterfactual"`); it never promotes a card or sets `measured_lift` (observational/causal firewall held). (3) Added `cem_eval/vertical_loop.py` (`run_vertical_loop` + `VerticalLoopReport`) driving ingest -> propose -> validate -> promote -> retrieve -> close on two seeded skills, computing MMA via the locked protocol with the leakage guard wired (`inject_leakage` negative control). (4) Added `scripts/run_cem_vertical_loop.py` as a real CLI consumer. Report counts are real store queries, not loop counters. First loop: MMA 1.0, n=2, CI [1.0, 1.0] - the toy skeleton smoke, explicitly NOT the Phase 4 baseline-ladder exam. Scorer deliberately kept `lexical_overlap_v0` (action-value scorer is Phase 3).
- Files:
  - `packages/cem-core/src/cem_core/kernel.py`
  - `packages/cem-eval/src/cem_eval/vertical_loop.py`
  - `packages/cem-eval/src/cem_eval/__init__.py`
  - `scripts/run_cem_vertical_loop.py`
  - `tests/test_action_brief_record.py`
  - `tests/test_close_influence.py`
  - `tests/test_vertical_loop.py`
  - `tests/test_run_cem_vertical_loop_script.py`
  - `docs/2026-05-29-cem-1-phase-1-vertical-skeleton-plan.md`
- Verification: `python -m pytest` -> 91 passed (9 new Phase 1 tests). Three failure canaries hand-verified break -> fail -> revert -> pass: untagged action-delta (`test_brief_never_presents_untagged_delta`), `close_influence` never verifies a card (`test_close_influence_never_verifies_a_card`), and vertical-loop leakage-bites (`test_vertical_loop_leakage_guard_bites`, self-proving via `pytest.raises`). Independent verifier subagent returned PHASE 1 VERIFIED across 6 checks: real-green (91/91, exit 0), script runs end-to-end (`brief_record_count=2`, `influence_event_count=2`, `card_count=2`), MMA computed not hardcoded (sensitivity check `[0.5,1.0]` vs `[0.0,0.0]` -> 0.75), canaries substantive, every new symbol has a real caller (no ghost code), and no Phase 2/3 scope leak (`scorer_version` uniformly `lexical_overlap_v0`; `probe_verified`/`heldout_eval` appear only as enum literals and a canary assertion). `python -m compileall`, `python scripts/run_synthetic_eval.py`, `scripts/session-start-gate.ps1`, and `git diff --check` all clean.
- Follow-up: Execute Phase 2 (grounded consolidation + the evidence-gated verification loop: probes -> results -> verified promotion), then Phases 3-5.

## LEDGER-20260529-014 - Fixed offset-naive current_time crash in action-brief retrieval

- Date: 2026-05-29
- Type: verification
- Status: resolved
- Source: First real code commit run through the new Greptile review-loop workflow. Closes the standing Open Follow-Up (MCP `current_time` offset-naive/offset-aware comparison), originally observed live in LEDGER-20260528-009.
- Summary: A client (MCP/CLI) supplying `current_time` as a timezone-less ISO string had it parsed offset-naive by Pydantic, while card `valid_from`/`valid_until` are offset-aware (`utc_now`). `_card_in_scope` then raised `TypeError: can't compare offset-naive and offset-aware datetimes` inside `retrieve_action_brief`. Fix: a `TaskContext.current_time` field validator coerces naive input to UTC. After Greptile's PR #2 review (4/5) flagged the symmetric gap, the same coercion was added to `ExperienceCard.valid_from`/`valid_until`, so naive card validity bounds (legacy storage / external writes) can't crash from the card side either. The UTC-aware invariant is now enforced at the model boundary on both sides.
- Files:
  - `packages/cem-core/src/cem_core/models.py`
  - `tests/test_naive_current_time.py`
  - `CHANGELOG.md`
- Verification: Two regression tests first reproduced the exact `TypeError` at `kernel.py:202` (client `current_time` and naive card bounds), then passed after the fix; `python -m pytest` -> 93 passed (2 new), full suite green (EXIT 0).
- Follow-up: None for this bug; resume CEM Phase 2.

## LEDGER-20260529-015 - Adversarial-audit remediation (fake-green gates, weak tests, ghost exports)

- Date: 2026-05-29
- Type: verification
- Status: resolved
- Source: Multi-agent adversarial audit (5 hunters + 3 verifiers) of the whole repo against its own quality bars. User then directed "fix everything" for the remaining findings (overriding the audit's read-only constraint).
- Summary: Closed the remaining findings after the tz fix (014).
  - **Fake-green gates (HIGH).** `run_monitor`'s `correction_controller_wired` and `recent_corrections_recorded` passed a hardcoded `True`, so they could never go RED while feeding the `startup_brief` blocking gate. Replaced `correction_controller_wired` with a real falsifiable predicate (`_correction_controller_wired`: controller's resume-gate record lives under the active memory root and `summary.root == root`); a controller bound to a different root now goes RED. Removed the tautological `recent_corrections_recorded` check entirely and folded its count into the wired check's informational detail (zero corrections on a fresh install is normal and must not block). Emptied the fake-green allowlist.
  - **Existence-only / weak tests (LOW).** Pinned vertical-loop counts to exact measured values (n/trace/atom/card = 2; mma = 1.0) instead of `>= 1`; required `math.isfinite` on synthetic-eval p95 latency instead of the tautological `>= 0.0`; replaced the fragile try/except in the tampered-envelope test with `pytest.raises(ValueError, match=...)`.
  - **Ghost exports (LOW).** Removed `trace_body_hash` and `verify_shared_trace_envelope` from the `cem_core` public surface (zero external callers — internal use plus barrel only). Kept them defined for internal use. Decided to KEEP `build_shared_trace_envelope` exported (borderline #4): it is the public envelope constructor paired with `import_shared_trace` and is consumed by the test suite, so it is not a ghost.
- Files:
  - `packages/cem-core/src/cem_core/operations.py`
  - `packages/cem-core/src/cem_core/__init__.py`
  - `tests/test_correction_controller_gate.py` (new failure canary)
  - `tests/test_no_fake_green_guard.py`
  - `tests/test_vertical_loop.py`
  - `tests/test_synthetic_eval.py`
  - `tests/test_multi_agent.py`
  - `CHANGELOG.md`
- Verification: TDD canary-first for the gate (RED `assert 'pass' == 'fail'` before the fix, GREEN after); the existing CLI monitor test still passes, proving the honest gate is GREEN on a healthy seeded root. `python -m pytest` -> 95 passed (2 new), full suite green (EXIT 0). Work done on branch `fix/audit-remaining-findings` off `ab7bd86` to avoid colliding with the concurrent `fix/naive-current-time` session.
- Follow-up: None for these findings; the live-runtime correction-capture wiring (below) remains the one open implementation item.

## Open Follow-Ups

- Add latency budget enforcement to the startup controller.
- Record `brief_id`, `monitor_id`, and evidence ids for every governed agent run, not only session-start gate output.
- Wire Correction Capture Controller into live agent runtime hooks beyond the CLI surface.
