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
- Completed **Phase 2 (grounded consolidation + verification)**. Consolidation now runs the full §4.4 pipeline: card-level **temporal supersession** (a newer contradicting atom marks the stale card `superseded` with `deactivated_at`/`deactivated_reason`/`superseded_by_card_ids` and `_card_in_scope` drops it from retrieval) and cross-scope **contradiction links** (two cards with the same claim key but different values in different operational scopes are bidirectionally cross-linked via `contradicts_card_ids` and both stay active — feeding the Phase 3 contradiction penalty). The **verified lifecycle** (§4.2) is evidence-gated end-to-end: `schedule_probe`/`run_probe` measure held-out replay lift (memory arm minus a 0.0 no-memory control) and only `apply_verification_result` promotes to `verified` when lift ≥ threshold; `inject_negative_control` plants a retrievable bad card that `run_probe` deprecates and removes from retrieval, gated by `negative_control_suppression_rate()` (a leak canary forces a control to `verified` and asserts the rate drops below 1.0).
- Wired the Phase 2b machinery into a real caller: `run_vertical_loop` now probes each seeded candidate to `verified` and suppresses an injected negative control, reporting `verified_card_count` and `negative_control_suppression_rate`. `card_count` now tallies active cards so the deactivated control does not inflate it. Scorer stays `lexical_overlap_v0` (action-value scorer is Phase 3).
- Completed **Phase 4 (MMA + 10-baseline exam)**. Added the missing kill-criterion gate to the locked eval protocol (`beats_lexical_by_margin` / `lexical_margin_pp`; `LEXICAL_MARGIN_PP` had no consumer), the held-out dataset (`phase4_dataset.py`: 12 fresh operator-phrased tasks + the corruption-fixture memory source, with a namespace-disjoint leakage guard and a no-verbatim-task-statement lint), the exam runner (`phase4_exam.py`: all 10 `BASELINE_LADDER` rungs run honestly per held-out task, paired MMA + 95% CI per rung, the two gates `mma_passes(cem)` + `beats_lexical_by_margin(cem, lexical)`, weight snapshot, and a PASS/FAIL_REPORTED_HONESTLY verdict), and `scripts/run_phase4_exam.py`. **Single-shot held-out result at the LEDGER-018 locked weights: CEM MMA 0.833 (95% CI [0.613, 1.054], n=12) vs lexical 0.083 → margin 75.0pp; verdict PASS.** Negative-control suppression 1.0; CEM beats every honest baseline (best non-CEM = summary 0.333) and sits below the human_runbook ceiling (1.0). The margin is earned: the lexical/vector/full-context rungs surface the planted poisoned/stale/contradictory traps that CEM validates and consolidates away.
- Completed **§12 Correction Capture live runtime hooks** (the last open item from the project's original state — wiring the controller into a LIVE agent runtime beyond the manual CLI). New `cem_core/correction_hooks.py` pure decision core: `hook_on_user_prompt_submit(root, prompt_text, ...)` classifies a live prompt FIRST and short-circuits a benign prompt to ALLOW with zero side effects, else captures the correction and returns BLOCK; `hook_on_pre_tool_use_gate(root)` DENIES continuation while the resume gate is armed and FAILS CLOSED on a corrupt gate. A `HookDecision` (StrictModel) carries the decision + named exit codes (`HOOK_EXIT_ALLOW=0`/`BLOCK=10`/`GATE_BLOCKED=11`/`PARSE_ERROR=2`). Two CLI subcommands (`correction hook-prompt` reads an untyped stdin payload tolerating unknown runtime keys + a UTF-8 BOM; `correction hook-gate`) map the decision to the process exit code via a single `main()` branch, with a `_emit` hook branch keyed on a unique discriminator. Two PowerShell wrappers (`scripts/correction-hook-prompt.ps1`, `correction-hook-gate.ps1`) mirror `session-start-gate.ps1` (pipe stdin, stdout-only, branch on `$LASTEXITCODE`); the live runtime's payload→`prompt_text` field projection lives only in the wrapper and is tagged **[UNVERIFIED]** until a live runtime smoke. There is deliberately NO agent-callable resume surface — the gate clears only via the existing human-approved `correction resume`. A Monitor-0 bridge test proves the live hook and the manual CLI/session-start gate share ONE gate (single source of truth). **15 new tests; both gate canaries proven to bite; the PS wrappers smoke-verified end-to-end (benign→0, correction→10, gate→11) in an isolated root — which caught a real PowerShell UTF-8-BOM stdin bug that pure pytest missed.**
- Completed **Phase 5 (hardening)**. (1) **Shared `card_is_inactive(card)` predicate** promoted to module level in `kernel.py` (CEM staticmethod delegates to it; adopted by `_supersede_stale_cards` and the eval `vertical_loop` active-card count; exported from `cem_core`), so every consumer classifies card inactivity on one axis (status OR deactivation). (2) **Latency-budget readiness gate**: pre-registered `RETRIEVAL_LATENCY_BUDGET_MS=50.0` + `within_latency_budget(measured_ms, *, budget_ms)` (smaller-is-better `<=`, 6dp rounding) in `eval_protocol.py`; the Phase 4 exam now measures p95 CEM-rung retrieval latency (dedicated `_measure_cem_retrieval_latency` pass, reusing `_measure_ms`/`_p95`), reports `p95_retrieval_latency_ms`/`retrieval_latency_budget_ms`/`within_latency_budget`, and fails closed if the sample count ≠ task count. The MMA PASS/FAIL verdict is **unchanged** — latency is a readiness flag only. (3) **Failure-mode coverage** (`tests/test_fail_closed.py`): empty-store retrieval degrades to a graceful empty brief; missing card/atom ids raise `KeyError` (store + kernel); a probe with no target raises `ValueError`; `StrictModel` rejects malformed input. (4) **Composite production-readiness gate** (`cem_eval/production_readiness.py`): `production_readiness_report(report) -> ReadinessReport` with `ready` **derived** as `all(checks pass)` over the five locked criteria — `mma_passes`, `beats_lexical_by_margin`, `negative_control_suppression==1.0`, `within_latency_budget`, `no_fake_green_ast_clean`. The no-fake-green AST scanner was extracted to a shared `cem_eval/fake_green_guard.py` (single source of truth) and now also policies the gate module itself (self-referential hole closed). **Exam unchanged after wiring: CEM MMA 0.833 (95% CI [0.613, 1.054], n=12), margin 75.0pp, verdict PASS; measured p95 retrieval ≈ 11–13 ms (worst-of-12), within the 50 ms budget.**
- Completed **Phase 3 (action-value retrieval)**. Replaced the bare lexical-overlap scorer (`lexical_overlap_v0`) with the **transparent feature ranker `action_value_v1`** (design §4.1): an auditable additive weighted sum over five features — `precondition_match`, `verified_lift_prior`, `recency_temporal`, `contradiction_penalty`, `staleness_penalty` — plus the preserved normalized lexical floor. `verified_lift_prior` is **hard-gated to 0.0** until a passed probe sets both `card.measured_lift` and `promotion_status="verified"` (never invents a prior from confidence/atom count). `score_card` now returns `(total, breakdown)` and `retrieve_action_brief` persists a per-feature `score_breakdown_by_card` whose `weighted_*` terms sum exactly to each card's `total` (an assertable auditability invariant). `expected_action_delta` is now sourced from the strongest verified selected card's realized lift (`probe_verified`), the confidence proxy (`observational_unverified`), or `none` — never hardcoded; `heldout_eval` stays reserved for the Phase 4 MMA harness. Selection is now **relevance-keyed** (precondition OR lexical OR earned lift), so a penalty never silently drops a relevant card. `retrieve_action_brief(task, *, max_cards)` signature is unchanged.

### Changed

- Fixed the asserted-promotion bug: `promote()` now creates/updates a **candidate** card only and no longer flips the atom or card to `verified`. Verification is a separate, evidence-gated step via `apply_verification_result()`. `audit()` now reports a card's real `promotion_status` instead of a hardcoded `"verified"`.
- **Phase 3 read-path behavior change.** Retrieval now ranks by estimated action value, not word overlap. Two consequent selection-semantics changes (no existing behavioral test asserts numeric scores, so the suite is unaffected): a card with positive net total but **zero relevance** (e.g. pure recency) is now excluded, and a **relevant card driven net-negative by a contradiction penalty is now kept** (relevance-keyed gate, not net-total gate). Pre-registered weight set (the single locked candidate per the spec §10 single-shot rule): `W_PRE=1.0, W_LEX=1.0, W_LIFT=4.0, W_REC=1.0, W_CON=2.0, W_STALE=1.5`; `HALF_LIFE_DAYS=30.0, STALE_WINDOW_DAYS=14.0, CONTRA_SATURATION=2.0`.

### Fixed

- Fixed a `TypeError` in action-brief retrieval on timezone-naive datetimes: `TaskContext.current_time` and `ExperienceCard.valid_from`/`valid_until` now coerce naive values to UTC, so `_card_in_scope` comparisons no longer crash whether the naive value comes from a client-supplied `current_time` or naive card validity bounds (legacy storage / external writes). Closes the standing `current_time` offset-naive/offset-aware follow-up.
- **Adversarial-audit remediation.** Made the two fake-green Correction Capture monitor gates honest: `correction_controller_wired` now evaluates a real falsifiable predicate (controller bound to the active memory root) with a failure canary proving it goes RED when unwired, and the tautological `recent_corrections_recorded` literal-True check was removed (its count folded into the wired check's informational detail). The fake-green allowlist is now empty. Strengthened weak/existence-only tests: vertical-loop counts pinned to exact values, synthetic-eval p95 latency now requires `math.isfinite`, and the tampered-envelope rejection uses `pytest.raises(..., match=...)`. Removed two ghost exports (`trace_body_hash`, `verify_shared_trace_envelope`) from the `cem_core` public surface (kept internal).
- **Phase 4 exam determinism (Phase 5).** `phase4_dataset.EVAL_NOW` was a fixed past instant (`2026-05-29 12:00 UTC`); because the kernel stamps each card's `valid_from` with wall-clock `utc_now()` at promote time, once the wall clock passed that instant every exam-built card was future-dated out of scope (`valid_from > current_time`) → empty briefs → probes could not verify → **MMA silently collapsed to 0.000**. Anchored `EVAL_NOW = utc_now() + timedelta(hours=1)` so exam-built cards are always in scope and the relative recency/staleness deltas stay stable (the exam is deterministic in OUTCOME; the absolute instant enters no score). Reproduces CEM MMA 0.833 / 75pp / PASS. Added a wall-clock-robust regression test (no exam-built card may be `valid_from > EVAL_NOW`).
- **Phase 2 PR review remediation (PR#4).** Three Greptile-flagged fixes: (1) `_matching_card` now skips inactive (superseded/deprecated/quarantined/deactivated) cards, so a re-observed lesson whose title matches a dead card forms a fresh live card instead of being merged into the dead card and rendered permanently unretrievable by `_card_in_scope`. (2) `negative_control_suppression_rate()` now counts a control as suppressed only when its card is actually inactive (was: any status `!= "verified"`), so a freshly planted control whose probe has not run no longer reports a false 1.0 that hides a live hazard; inactive-card check extracted to a shared `_card_is_inactive` predicate. (3) `_supersede_stale_cards` early-exits for non-`invalidation_event` atoms (the only atoms that can populate `superseded_by`), skipping the full `list_atoms()` scan on the common promote path. Each shipped with a failure canary; the negative-control leak canary was rewritten to baseline 1.0 from a genuinely suppressed control rather than the previously-buggy unrun baseline.

### Verification

- **Phase 0:** `python -m pytest` -> 82 passed (21 new Phase 0 tests, including failure canaries for the promotion bug, the audit status, the MMA success bar, the leakage guard, and the no-fake-green guard).
- **Phase 1:** `python -m pytest` -> 91 passed (9 new Phase 1 tests, including failure canaries for untagged action-delta, `close_influence` never verifying a card, and the vertical-loop leakage guard). An independent verifier subagent confirmed real-green, all three canaries bite (break -> fail -> revert -> pass), no ghost code (every new symbol has a real caller), and no Phase 2/3 scope leak (MMA computed not hardcoded; `scorer_version` uniformly `lexical_overlap_v0`).
- `python -m compileall -q packages scripts tests`, `python scripts/run_cem_vertical_loop.py`, `python scripts/run_synthetic_eval.py`, `scripts/session-start-gate.ps1`, and `git diff --check` all clean.
- **Audit remediation:** `python -m pytest` -> 95 passed (2 new correction-controller-gate canaries). The new fake-green failure canary bites (gate goes RED when the controller is unwired); CLI monitor test still green proves the honest gate passes on a healthy seeded root.
- **Phase 2:** `python -m pytest` -> 107 passed (12 new tests across `test_consolidation.py`, `test_verification.py`, and `test_vertical_loop.py`, each consolidation/verification gate paired with a failure canary). `python scripts/run_synthetic_eval.py` clean (false-memory resistance 1.0, contradiction precision/recall 1.0, false-quarantine rate 0.0); `python scripts/run_cem_vertical_loop.py` reports `verified_card_count` 2 and `negative_control_suppression_rate` 1.0. An independent verifier subagent refuted all four Phase 2 claims as SUPPORTED: proved two canaries bite (break -> fail -> revert -> pass) on the grounding guard and suppression-rate gate, grep-confirmed `apply_verification_result` is the only assignment of card `verified` and `scorer_version` stays `lexical_overlap_v0`, and confirmed the real caller chain (`run_vertical_loop` -> `run_probe`/`schedule_probe`; script -> loop). Tree left clean (`git status --short` empty).
- **Phase 2 PR review remediation (PR#4):** `python -m pytest` -> 109 passed (1 new unrun-control failure canary; the leak canary rewritten, not added). Each of the three fixes was driven RED-first: the `_matching_card` canary asserted the re-observed atom merged into the dead card (same `card_id`), the suppression-rate canary asserted a false `1.0 == 0.0`, and the supersession early-exit kept both invalidation and non-invalidation branches green (verified via the existing supersession + re-observation tests). Commits `4ed433b`, `ba9efff`, `d8a5bec`. Greptile re-reviewed at **5/5** (stale re-anchors only); stopped before merge.
- **Phase 3 (action-value retrieval):** `python -m pytest` -> 115 passed (6 ranker tests in `test_action_value_ranker.py`, plus 4 version-string anchors bumped to `action_value_v1`). Canaries proven to bite (break -> fail -> revert -> pass): setting `W_LIFT=0.0` flips the primary canary (the verified high-lift card no longer outranks the lexically-closer unverified card), disabling the `_as_utc` coercion reproduces the offset-naive/-aware `TypeError` on a legacy naive `last_validated_at`, and (after the pre-push review hardening) `W_LIFT=8.0` fails the breakdown test's numeric weight check. `python scripts/run_synthetic_eval.py` clean; `python scripts/run_cem_vertical_loop.py` reports `mma 1.0`, `scorer_version action_value_v1`, `verified_card_count 2`, `negative_control_suppression_rate 1.0`.
- **Phase 4 (MMA + 10-baseline exam):** `python -m pytest` -> 127 passed (11 new: 1 margin-gate boundary in `test_eval_protocol.py` + 10 exam canaries in `test_phase4_exam.py`, incl. a `cem_verified_card_count >= 1` regression guard so the verified-lift prior cannot silently go dark). Canaries cover the leakage gate aborting before any rung, the 10 rungs present with the ceiling excluded from gates, a real (non-hardcoded) no_memory denominator, total negative-control suppression, weights pinned to LEDGER-018, the no-verbatim-task-statement leakage lint, the lexical rung surfacing a trap CEM suppresses, and the margin gate rejecting a no-op (cem==lexical) scorer. `python scripts/run_phase4_exam.py` -> exit 0 (PASS), headline `MMA = 0.833 (95% CI [0.613, 1.054], n=12); lexical MMA = 0.083; margin = 75.0pp`.
- **Phase 3 Greptile review round (PR#5).** First pass 4/5 with two P2 quality findings (retrieval path confirmed correct), both fixed as a behavior-preserving refactor: `_raw_lexical_overlap` is now computed once per card in `retrieve_action_brief` and passed into `score_card` (new optional `raw_lexical` param) instead of being recomputed; and `score_card`'s context-suppressing defaults are documented and locked by a `test_score_card_standalone_defaults_are_context_free` test. Suite -> 116 passed.
- **Phase 3 pre-push review hardening.** An adversarial multi-agent review (5 dimensions -> verify) confirmed 3 minor findings, all fixed before push: (1) the auditability-invariant test was a tautology (re-summed the stored `weighted_*` values) -> rewritten to assert each `weighted_* == weight x raw-feature`, enforce penalty/bonus signs, recompute `total` independently from raw features, and lock `W_LIFT` numerically (now bites a wrong weight). (2) `weighted_lexical` was not reconstructable from the persisted breakdown (the normalization divisor was not stored) -> added `lexical_overlap_norm` to `score_breakdown_by_card`. (3) the staleness `<= 0` branch comment wrongly called itself unreachable -> corrected (it fires at `valid_until == current_time` since `_card_in_scope` uses strict `<`), with a boundary characterization test.
- **Phase 5 (hardening):** `python -m pytest` -> 154 passed (27 new across `test_card_inactive_predicate.py`, `test_fail_closed.py`, `test_production_readiness.py`, `test_eval_protocol.py`, `test_phase4_exam.py`). Canaries proven to bite (break -> fail -> revert): the predicate fix (a deprecated card was clobbered to `superseded` without the shared predicate), the latency operator inversion (`>=` flips the over-budget + boundary tests), the empty-latency-samples fail-closed guard (`DID NOT RAISE` without it), the silent-default store regression (`get_card` returning `None`), and the self-referential-hole closure (a planted `_check('…', True, …)` in `production_readiness.py` now fails the guard). `python scripts/run_phase4_exam.py` -> exit 0 (PASS), headline unchanged + `retrieval p95 = 13.1ms (budget 50ms, within: True)`; `python scripts/run_synthetic_eval.py` clean. An adversarial multi-agent review (4 dimensions -> verify) confirmed 1 finding (a new wall-clock-coupled test assertion inconsistent with the file's anti-flake convention), fixed by deleting it (the deterministic `future_dated` check already bites the regression).

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
