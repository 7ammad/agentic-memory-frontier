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

## LEDGER-20260529-016 - CEM-1 Phase 2 grounded consolidation + verified lifecycle landed and verified

- Date: 2026-05-29
- Type: verification
- Status: resolved
- Source: Standing user directive to finish the full CEM-1 build (no MVP, no trimming) end-to-end with no ghost coding / no fake-green; Phase 2 per the round-2 phase sequencing (consolidation §4.4 + verification §4.2 land together, before the read-path advances in Phase 3).
- Summary: Completed the two halves of Phase 2 as five atomic bricks.
  - **Consolidation (§4.4).** Card-level **temporal supersession**: a newer contradicting atom (e.g. an `UPDATE:` invalidation event) now marks the stale card `promotion_status="superseded"` with `deactivated_at`/`deactivated_reason`/`superseded_by_card_ids`, and `_card_in_scope` excludes superseded/deprecated/deactivated cards so retrieval no longer serves them. Cross-scope **contradiction links**: two cards asserting the same claim key with different values in *different* operational scopes (different `domain_scope`) bypass the same-scope contradiction quarantine, both promote, and are bidirectionally cross-linked via `contradicts_card_ids` (real input for the Phase 3 §4.1 contradiction penalty); unrelated cards (different keys) stay unlinked.
  - **Verified lifecycle (§4.2).** `schedule_probe` + `run_probe` execute a held-out replay probe whose measured lift is the memory arm's success (target card surfaced AND recommends the decisive action) minus a 0.0 no-memory control; only `apply_verification_result` promotes a card to `verified`, and only when lift ≥ threshold. A card whose decisive action the probe does not recommend stays `candidate` with `measured_lift` None. `inject_negative_control` plants a retrievable bad card (recommending the wrong action); `run_probe` deprecates it and removes it from retrieval. `negative_control_suppression_rate()` is a real gate with a leak canary that forces a control to `verified` and asserts the rate falls below 1.0.
  - **Real caller (build contract §5).** `run_vertical_loop` now probes each seeded candidate to `verified` and injects+suppresses a negative control, reporting `verified_card_count` and `negative_control_suppression_rate`; `card_count` tallies active cards so the deactivated control does not inflate it. `scripts/run_cem_vertical_loop.py` exercises it as a real consumer. Scorer stays `lexical_overlap_v0` (action-value scorer is Phase 3).
- Files:
  - `packages/cem-core/src/cem_core/kernel.py`
  - `packages/cem-core/src/cem_core/models.py`
  - `packages/cem-eval/src/cem_eval/vertical_loop.py`
  - `tests/test_consolidation.py`
  - `tests/test_verification.py`
  - `tests/test_vertical_loop.py`
  - `TODO.md`, `CHANGELOG.md`
- Verification: `python -m pytest` -> 107 passed (12 new tests, every gate paired with a failure canary). `python scripts/run_synthetic_eval.py` clean (false-memory resistance 1.0, contradiction precision/recall 1.0, false-quarantine rate 0.0); `python scripts/run_cem_vertical_loop.py` -> `verified_card_count` 2, `negative_control_suppression_rate` 1.0. Independent verifier subagent refuted all four Phase 2 claims as SUPPORTED: proved two canaries bite (break -> fail -> revert -> pass) on the grounding guard and the suppression-rate gate, grep-confirmed `apply_verification_result` (kernel.py:302) is the only card `verified` assignment and `scorer_version` stays `lexical_overlap_v0`, and confirmed the real caller chain (`run_vertical_loop` -> `schedule_probe`/`run_probe`; script -> loop). Tree left clean (`git status --short` empty). Commits: `8379ef4` (supersession), `3becd56` (contradiction links), `bea64b1` (probe runner), `1347593` (negative-control suppression), `9d1eb80` (vertical-loop wiring).
- Follow-up: Phase 3 - action-value retrieval (advance `scorer_version` past `lexical_overlap_v0`, rank briefs by measured/expected action value, record influence events), then Phases 4-5.

## LEDGER-20260529-017 - PR#4 Phase 2 Greptile review round driven to fixes (3/5 -> re-review)

- Date: 2026-05-29
- Type: verification
- Status: resolved
- Source: Greptile review of PR#4 (`feat/cem1-phase2-consolidation-verification`) returned Confidence 3/5 with three findings. Per the codified review-loop hardgate (every slice rides the Greptile PR loop to 5/5), the findings were fixed test-first before re-review.
- Summary: Three atomic TDD fixes, each with a failure canary proven to bite.
  - **Issue 1 - silent atom loss (correctness).** `_matching_card` scanned all cards without filtering inactive ones, so a re-observed lesson whose title matched a superseded/deprecated card was merged into that dead card; because `_card_in_scope` drops inactive cards, the re-observed atom became permanently unretrievable. Added a status guard mirroring `_link_contradicting_cards`. RED canary `test_reobserved_lesson_does_not_merge_into_inactive_card` confirmed the merge-into-dead-card bug (same `card_id`) before the fix. Commit `4ed433b`.
  - **Issue 2 - dishonest suppression metric (metric integrity).** `negative_control_suppression_rate()` counted any card with `promotion_status != "verified"` as suppressed, so a freshly planted negative control whose probe had not run -- still `candidate` and live in retrieval -- was reported as suppressed (false 1.0 hiding a live hazard). Rejected Greptile's literal suggestion (filter denominator to run probes) because it would vacuously return 1.0 with zero run probes AND break the existing leak canary (which simulates the leak via `apply_verification_result`, leaving `probe.status` unset). Instead the numerator now counts only actually-inactive cards via a shared `_card_is_inactive` predicate (also adopted by `_matching_card`). RED canary `test_suppression_rate_excludes_unrun_negative_control` asserted `1.0 == 0.0` before the fix; the leak canary was rewritten to baseline 1.0 from a genuinely suppressed control. Commit `ba9efff`.
  - **Issue 3 - redundant scan on the hot path (perf).** `_supersede_stale_cards` ran a full `list_atoms()` scan on every promote, though `superseded_by` is only ever populated by an `invalidation_event` atom (validator `_supersede_conflicts`, the sole writer -- grep-confirmed across the codebase). Added an early-exit for non-invalidation atoms. Behavior-preserving (no new test; both branches already covered by the existing supersession test and the Issue-1 re-observation canary). Commit `d8a5bec`.
- Files:
  - `packages/cem-core/src/cem_core/kernel.py`
  - `tests/test_consolidation.py`
  - `tests/test_verification.py`
  - `CHANGELOG.md`
- Verification: `python -m pytest` -> 109 passed (1 net-new test; +2 from the Phase 2 baseline of 107). Each fix RED-first: Issue 1 watched `assert card_id != card_id` fail; Issue 2 watched `assert 1.0 == 0.0` fail; Issue 3's early-exit kept both the invalidation branch (`test_newer_atom_supersedes_stale_card_and_removes_it_from_retrieval`, whose `superseded_by_card_ids == [card_b]` assertion can only pass if the body ran) and the non-invalidation branch green. Grep confirmed validator.py:154 is the only writer of `superseded_by` and extractor.py:14 maps `UPDATE:` -> `invalidation_event`.
- Follow-up: Push branch, post the Issue-2 design-choice reply to Greptile, run the re-review loop to 5/5, then stop before merge (merge is the user's call). Phase 3 (action-value retrieval) stacks on this branch once PR#4 is 5/5.
- **Closeout (2026-05-29, re-review):** Greptile re-reviewed the latest commit `f4e7e8f` and returned **Confidence 5/5** (review #2; summary comment `06:28:05Z`). The three inline comments it re-posted (P1 `_matching_card`, P2 suppression rate, P2 `_supersede_stale_cards` scan) are **stale re-anchors of the round-1 findings** — verified against ground truth: the `_card_is_inactive` guard is live at `kernel.py:490`, the suppression numerator uses `_card_is_inactive` at `kernel.py:297` (not the `!= "verified"` the comment quotes), and the `invalidation_event` early-exit at `kernel.py:171-172` precedes the `list_atoms()` scan at `kernel.py:173`. PR#4 is **done at 5/5; stopped before merge** (merge is the user's call). Bounded Greptile loop NOT re-opened on a 5/5 surface.

## LEDGER-20260529-018 - CEM-1 Phase 3: action-value retrieval (transparent feature ranker)

- Date: 2026-05-29
- Type: feature
- Status: resolved (PR pending Greptile loop)
- Source: Standing user directive to finish the full CEM-1 build end-to-end (no MVP, no trimming) with TDD + the Greptile PR loop. Phase 3 is the next unchecked TODO item; spec `docs/2026-05-28-causal-experience-memory-full-program-design.md` §4.1 (lines 87-100) + §8 Phase 3 (line 225). Designed via a dynamic understand->design workflow (8 agents: 4 parallel readers mapping the spec/scorer/delta/tests, a 3-lens judge panel — auditability/eval-power/robustness — and a synthesis into one TDD blueprint); the blueprint's line/field claims were re-verified against the live tree before any code.
- Summary: Replaced the bare-int lexical scorer (`score_card -> int`, `SCORER_VERSION="lexical_overlap_v0"`) with the **transparent feature ranker `action_value_v1`** (design §4.1). Retrieval now ranks by estimated action value, not word overlap, and every ranking is auditable per card.
  - **Five auditable features**, each bounded to [0,1] before weighting: `precondition_match` (fraction of `card.check_first` preconditions whose >3-char tokens appear in the task context), `verified_lift_prior` (hard-gated), `recency_temporal` (exp decay, 30-day half-life, off `last_validated_at or valid_from`), `contradiction_penalty` (live in-scope conflicts / `CONTRA_SATURATION`, subtracted), `staleness_penalty` (proximity to `valid_until` within a 14-day window, subtracted). The legacy lexical count is preserved as a normalized similarity floor (`raw_lexical / candidate-set-max`) and carried raw under `lexical_overlap` for the Phase 4 >=5pp baseline diff.
  - **Verified-lift hard gate (§4.1).** `_verified_lift_prior` returns 0.0 unless `card.measured_lift is not None AND card.promotion_status == "verified"` (both required; `measured_lift` is set ONLY by `apply_verification_result` on a passed probe). Provably 0 for every card until a probe earns it — the prior is never invented from confidence/atom count/CI.
  - **Auditability invariant.** `score_card` returns `(total, breakdown)`; the persisted per-card `score_breakdown_by_card` carries each feature, each `weighted_*` term (penalties stored negative), and `total`, with `sum(weighted_*) == total` to float tolerance (locked by a test).
  - **Sourced delta (§4.2/§6).** `expected_action_delta` = the strongest verified selected card's RAW realized lift (`probe_verified`), else the confidence proxy (`observational_unverified`), else `None`/`none`. `heldout_eval` is never synthesized by the kernel (reserved for the Phase 4 MMA harness). Never hardcoded.
  - **Relevance-keyed selection (behavior change).** The old `score > 0` filter became "selected iff `precondition_match>0 OR lexical_overlap>0 OR verified_lift_prior>0`", so a contradiction/staleness penalty can never silently drop a relevant card, and a pure-recency card with no real relevance is excluded. Sort by `total` with a fully deterministic tie-break (`-total, -lift, -precondition, -lexical, card_id`). `retrieve_action_brief(task, *, max_cards)` signature unchanged; output bounded/lazy (breakdown built for selected cards only).
- Pre-registered weights (the SINGLE locked candidate for the spec §10 single-shot held-out rule — may only be tuned on the dev split, with held-out MMA evaluated once per locked set): `W_PRE=1.0, W_LEX=1.0, W_LIFT=4.0, W_REC=1.0, W_CON=2.0, W_STALE=1.5`; `HALF_LIFE_DAYS=30.0, STALE_WINDOW_DAYS=14.0, CONTRA_SATURATION=2.0`. These MUST be recorded here before any Phase 4 held-out run or the single-shot rule is violated.
- Files:
  - `packages/cem-core/src/cem_core/kernel.py` (constants, `_as_utc`, 5 feature helpers, `score_card` tuple return, `retrieve_action_brief` rewrite, 3-way delta, `SCORER_VERSION` bump)
  - `packages/cem-eval/src/cem_eval/vertical_loop.py` (independent `SCORER_VERSION` bumped in lockstep)
  - `tests/test_action_value_ranker.py` (new; 5 canaries)
  - `tests/test_vertical_loop.py`, `tests/test_action_brief_record.py` (version-string anchors)
  - `CHANGELOG.md`, `TODO.md`
- Verification: `python -m pytest` -> **114 passed** (5 new ranker tests; +5 from the 109 Phase-2-PR baseline). RED-first: the primary canary failed on the ordering assertion under `lexical_overlap_v0` (lexically-closer unverified card ranked first) before the ranker existed. **Two canaries proven to bite** (break -> fail -> revert -> pass): `W_LIFT=0.0` flips the lift-dominance canary (`AssertionError` at the ordering assert); disabling the `_as_utc` coercion reproduces `TypeError: can't subtract offset-naive and offset-aware datetimes` on a legacy naive `last_validated_at`. Smoke: `python scripts/run_synthetic_eval.py` clean; `python scripts/run_cem_vertical_loop.py` -> `mma 1.0`, `scorer_version action_value_v1`, `verified_card_count 2`, `negative_control_suppression_rate 1.0`. No lint gate in `pyproject.toml`.
- Pre-push review (adversarial multi-agent workflow, 5 dimensions -> verify; 11 findings -> 3 confirmed, all P2/P3, fixed test-first before push): (1) **P2 tautological invariant test** -- the breakdown test re-summed the stored `weighted_*` values (a == a, blind to a wrong weight), rewritten to assert each `weighted_* == weight x raw-feature`, enforce penalty/bonus signs, recompute `total` from raw features, and lock `W_LIFT` numerically; **proven to bite** (`W_LIFT=8.0` -> `4.0 == 2.0` AssertionError, where the old test passed). (2) **P3 lexical not reconstructable** -- the normalization divisor `max_raw_lexical` was not persisted, so `weighted_lexical` could not be re-derived from the stored raw `lexical_overlap`; added `lexical_overlap_norm` to the breakdown and corrected the `score_card` docstring. (3) **P3 staleness comment** -- the `days_to_expiry <= 0` branch is reachable at `valid_until == current_time` (since `_card_in_scope` uses strict `<`), contradicting its "defensive/unreachable" comment; comment corrected and a boundary characterization test added. Suite `115 passed`. Spec dimension cleared as faithful to §4.1; edge/regression dimension found no regression.
- Greptile review round (PR#5, base = PR#4's branch): first pass **4/5** with two P2 quality findings (retrieval path confirmed correct end-to-end), both fixed as a behavior-preserving refactor: (1) `_raw_lexical_overlap` was computed twice per card (once for the candidate-set max, once inside `score_card`) -> `retrieve_action_brief` now computes each card's raw overlap once into `raw_lexical_scores` and passes it into `score_card` via a new optional `raw_lexical` param (computed in-function only when `None`, for standalone callers). (2) `score_card`'s context defaults (`scope_ids=frozenset()`, `max_raw_lexical=0`) silently zeroed the contradiction penalty and lexical floor for any direct caller -> documented with a docstring note AND locked by a new `test_score_card_standalone_defaults_are_context_free` characterization test. Suite `116 passed`; vertical-loop smoke unchanged (`mma 1.0`, `action_value_v1`).
- Follow-up: Push the Phase-3 slice branch (`feat/cem1-phase3-action-value-retrieval`, stacked on PR#4) as its own small PR to staging; run the bounded Greptile loop to 5/5; stop before merge.
- **Closeout (2026-05-29):** PR **#5** opened (base = `feat/cem1-phase2-consolidation-verification`, stacked on PR#4). Greptile loop closed in **one turn**: first pass 4/5 (two P2 quality findings) -> fixed behavior-preservingly (`93d4ae9`) -> re-review **5/5** on `93d4ae9` (Greptile edited its summary in place; no new inline findings). **Phase 3 done at 5/5; stopped before merge** (merge is the user's call). Phase 4 stacks on this branch. Then Phase 4 (MMA + 10-baseline exam with the >=5pp lexical margin and leakage guard — the single-shot held-out run uses the weights pinned above), Phase 5 (hardening, incl. the two latent nits below), and the §12 correction-capture live-hooks track.

## LEDGER-20260529-019 - CEM-1 Phase 4: MMA + 10-baseline held-out exam (single-shot PASS)

- Date: 2026-05-29
- Type: feature / eval
- Status: resolved (PR pending Greptile loop)
- Source: Standing user directive to finish the full CEM-1 build; Phase 4 is the next unchecked TODO. Spec sections 7 (baseline ladder), 9 (kill criteria + single-shot rule), 10 (leakage), 11 (MMA reporting contract). Designed via a dynamic understand->design workflow; built lean (direct TDD, no pre-push review workflow, per user pacing decision).
- Summary: Ran the first real Marginal Memory Advantage exam.
  - **Gate (the one genuine eval_protocol gap):** `LEXICAL_MARGIN_PP=5.0` had no consumer. Added `lexical_margin_pp(cem, lexical)` (measured pp gap, reported even on a miss) and `beats_lexical_by_margin(cem, lexical, *, margin_pp=LEXICAL_MARGIN_PP)` (rounds to 6dp before `>=` so a true 5.0pp boundary survives float noise). Locked MMA/ladder/leakage definitions untouched.
  - **Dataset (`phase4_dataset.py`):** memory source = the synthetic-corruption fixture traces (valid lessons + planted poisoned/stale/contradiction/non-causal traps). 12 held-out tasks are fresh operator phrasings (no task statement appears verbatim in a source turn -- linted) targeting the decisive families, several with a lexically-attractive trap as a `forbidden_action`. Answer ids live in an `answer::` namespace disjoint from trace/turn ids, so `assert_no_leakage` is mechanical and fail-closed.
  - **Runner (`phase4_exam.py`):** all 10 `BASELINE_LADDER` rungs run honestly per held-out task; success = decisive action present AND no forbidden trap present; MMA + 95% CI per rung is paired against the REAL no_memory control (a genuine empty-recommend, not a literal). Two gates: `mma_passes(cem)` and `beats_lexical_by_margin(cem, lexical)`; `human_runbook` is computed as the ceiling and structurally excluded from both gates. Verdict is `PASS` or `FAIL_REPORTED_HONESTLY`. The CEM rung is the full kernel (validate -> promote -> earn verified lift via dev-split replay probes on the decisive lessons -> plant + suppress a negative control); the lexical_overlap rung ranks every extracted atom INCLUDING traps with no validation.
- **Single-shot held-out result (LEDGER-018 locked weights, scored once):** CEM **MMA 0.833** (95% CI [0.613, 1.054], n=12) vs lexical **0.083** -> **margin 75.0pp >= 5pp**; `mma_passes` True; **verdict PASS**. negative_control_suppression_rate 1.0. Honest baselines: no_memory 0.0, lexical_overlap/vector_rag/unverified_reflection 0.083, full_context 0.167, time_aware_rag/temporal_graph 0.250, summary 0.333; ceiling human_runbook 1.0. CEM dominates every honest rung and sits below the ceiling (10/12, not a suspicious perfect score). Margin honesty: it is earned by CEM suppressing the traps that word-overlap/vector/full-context retrieval surface, NOT by weight tuning (weights pinned + tested). CI is wide (n=12) and reported in full per the spec-11 no-bare-mean rule; the headline number is a toy-set demonstration, not a production claim.
- Files: `packages/cem-eval/src/cem_eval/eval_protocol.py`, `phase4_dataset.py` (new), `phase4_exam.py` (new), `scripts/run_phase4_exam.py` (new), `tests/test_eval_protocol.py`, `tests/test_phase4_exam.py` (new), `CHANGELOG.md`, `TODO.md`.
- Verification: `python -m pytest` -> **126 passed** (10 new). Margin-gate boundary canary locks 0/4.9/5.0/5.1pp; exam canaries lock leakage-aborts-first, 10-rungs+ceiling-excluded, real-zero no_memory denominator, total negative-control suppression, weight-drift detection, the no-verbatim-task lint, lexical-surfaces-trap-CEM-suppresses, and margin-gate-rejects-no-op. `python scripts/run_phase4_exam.py` -> exit 0.
- Follow-up: Push Phase-4 slice branch (`feat/cem1-phase4-mma-baseline-exam`, stacked on PR#5) as its own PR; bounded Greptile loop to 5/5; stop before merge. Then Phase 5 (hardening) and the section 12 correction-capture live-hooks track.
- **Closeout (2026-05-29):** PR **#6** opened (base = `feat/cem1-phase3-action-value-retrieval`, stacked on PR#5). Greptile loop closed in **one turn**: 4/5 -> fixes (`07bde3d`) -> **5/5** on `07bde3d`. **Phase 4 done at 5/5; stopped before merge.** Phase 5 stacks on this branch.
- Greptile review round (PR#6): first pass **4/5**, two test-coverage gaps (no wrong behavior; "safe to merge"), both fixed: (1) no assertion the CEM rung earns verified lift (if `_decisive_for_card_title` drifts, `W_LIFT=4.0` goes dark yet the exam still passes on trap suppression) -> verified empirically that **5 decisive cards earn `measured_lift=1.0`**, surfaced `cem_verified_card_count` on the report, and added `test_cem_rung_earns_verified_lift` (>=1). (2) the trap test only asserted the lexical side -> extended with the CEM-suppression side (at the pytest task the lexical rung's per-task success is 0.0 while CEM's is 1.0). Suite `127 passed`.

## Open Follow-Ups

- Add latency budget enforcement to the startup controller.
- Record `brief_id`, `monitor_id`, and evidence ids for every governed agent run, not only session-start gate output.
- Wire Correction Capture Controller into live agent runtime hooks beyond the CLI surface.
- **Phase 5 hardening — two latent defensive consistency nits surfaced by PR#4's 5/5 re-review (not bugs today, both unreachable):** (1) `_supersede_stale_cards` (`kernel.py:181`) skips only `promotion_status == "superseded"`, not all inactive states — a future `"deprecated"` card *with* evidence atoms could be overwritten to `"superseded"`; unreachable today because the only card-deprecation path (`_deprecate_negative_control`) leaves `evidence_atom_ids=[]`, so the `evidence & newly_superseded` gate drops it first. (2) `vertical_loop.py:129` `active_card_count` predicates on `deactivated_at is None` while line 130 `verified_card_count` predicates on `promotion_status == "verified"` — different axes; diverges only if a `"quarantined"` *card* is ever persisted with `deactivated_at=None`, and no code path sets `promotion_status="quarantined"` on a card today. Fix both by adopting the shared `_card_is_inactive` predicate.
