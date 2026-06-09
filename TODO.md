# AMS Build TODO

This is the continuation rail for AMS. It is ordered. Work from the first unchecked item downward.

## Terminal Scope Freeze

As of 2026-06-01, the AMS v1 product-completion list is closed. Do not add a
new TODO item to define AMS v1 as "really done" after this list. New work after
this point is allowed only as a regression fix from a failing acceptance check
or as a separately named post-v1 product phase.

AMS v1 terminal acceptance list:

- [x] A1. Primary runtime lock.
- [x] A2. Real trace intake.
- [x] A3. Trust before retrieval.
- [x] A4. Action briefs govern work.
- [x] A5. Outcome influence loop.
- [x] A6. Correction capture.
- [x] A7. Aging and maintenance.
- [x] A8. Frontier eval rerun against the accepted path.
- [x] A9. Operator product proof from a fresh local root.
- [x] Final status freeze: dashboard/monitor report no remaining v1 follow-ups.

Completion evidence is `scripts/run_ams_operator_proof.py`, `python -m pytest`,
`python scripts/ams.py monitor --deep`, and `python scripts/ams.py dashboard`.

## Continuation Rule

After finishing any checked item:

1. Run the relevant verification commands.
2. Commit and push if the work is clean.
3. Update this TODO.
4. Continue to the next unchecked item unless blocked, explicitly redirected, or the context-save hardgate is triggered.

Do not stop at "task complete" when the next unchecked item is clear.

## Source Of Truth

- `IDEA.md`
- `PRODUCT-LOCK.md`
- `docs/2026-06-10-ams-v2-experience-enforcement-plan.md`
- `docs/2026-06-10-ams-v2-acceptance-contract.md`
- `research/2026-05-27-plan-1-causal-experience-memory-foundation.md`
- `specs/2026-05-27-cem-0-memguard-kernel-spec.md`
- `sessions/2026-05-27-cem-0-session-handoff.md`

`PRODUCT-LOCK.md` defines what counted as AMS v1 product-complete. The old
A/B/C/D work remains historical infrastructure context. For post-v1 work, the
active dependency order is AMS V2 Phase 0 through Phase 10 in the V2 plan:

```text
V2 contract -> experience graph -> attribution -> invariants/skills -> matching
-> action decision -> reasoning UX -> supersession -> multi-agent governance
-> V2 eval -> operator proof
```

Older backend adapters and MCP integration remain infrastructure. They should be
used only where they serve the V2 experience-enforcement proof.

## Guardrails

- Preserve the full AMS V2 scope; do not rename it, downgrade it, or trim it
  into V1.5.
- Keep every V2 subsystem tied to the experience-enforcement proof: behavior
  changes under the hood, receipts prove why, and evals verify the result.
- Do not drift into dashboard, database, MCP, or platform work unless it is
  required for a listed V2 phase or acceptance test.
- Keep deterministic fixtures and failure canaries until the V2 eval primitive
  is stronger.
- Do not claim state-of-the-art.
- Never read or write `C:\Dev\Builds\Waki`.

## Ordered Build Queue

### 15. AMS V2 Experience Enforcement Architecture

AMS V2 is the named post-v1 phase. This is not V1.5 and not a smaller proof
kernel. The non-repeat enforcement kernel is a core subsystem inside the full V2
plan alongside reasoning, experience graph, procedural skill memory,
supersession, multi-agent governance, under-the-hood inference receipts, and the
V2 evaluation battery.

Canonical plan: `docs/2026-06-10-ams-v2-experience-enforcement-plan.md`.
Acceptance contract: `docs/2026-06-10-ams-v2-acceptance-contract.md`.

- [x] Phase 0 - V2 contract lock: accept the full V2 plan, add V2 acceptance
      criteria, define the seed corpus, and lock the no-trimming rule.
- [ ] Phase 1 - Experience graph and decision intent: capture expected outcome,
      authority, approval/experiment state, runtime surface, and evidence ids
      for consequential actions.
- [ ] Phase 2 - Error and success attribution: classify mistake,
      approved-experiment failure, acceptable tradeoff, success, and unresolved
      outcomes, including owner-labeled seed cases.
- [ ] Phase 3 - Invariants, skills, and authority scope: compile confirmed
      mistakes into behavior invariants, confirmed successes into skill
      candidates, and retrieve them through authority-ranked lanes.
- [ ] Phase 4 - Situation matching: catch exact and paraphrased repeats while
      suppressing valid neighbors according to the false-block budget.
- [ ] Phase 5 - Action decision point and policy binding: intercept
      consequential decisions and return allow, steer, warn, ask, block,
      override, or degraded-allow verdicts.
- [ ] Phase 6 - Reasoning controller and under-the-hood UX: allow reasoning with
      experience while preventing silent rationalization past confirmed
      mistakes; surface concise inference receipts instead of raw hidden
      reasoning.
- [ ] Phase 7 - Supersession and active forgetting: retire stale or wrong
      invariants and skills through authority-ranked supersession.
- [ ] Phase 8 - Multi-agent experience governance: share governed experience
      across agents without scope pollution.
- [ ] Phase 9 - V2 eval harness: run non-repeat, false-block,
      approved-experiment, skill-transfer, supersession, multi-agent conflict,
      and context-pollution evals.
- [ ] Phase 10 - Operator proof and release lock: fresh-root V2 operator proof,
      dashboard/monitor V2 status, review receipts, and product-lock update.

### 0. Foundation Lock

- [x] A: Deep technical review of SuperClaude memory MCP.
- [x] B: SuperClaude memory v0.3 upgrade spec.
- [x] C: Codex memory system design.
- [x] D: ACS protocol design.
- [x] Plan 1: AMS verified-experience thesis locked.
- [x] AMS V0 / MemGuard Kernel spec written.

### 1. Kernel Primitive

- [x] Models: Pydantic schemas for traces, atoms, cards, validation, action briefs, and audits.
- [x] Trace ledger: JSONL plus SQLite persistence for traces, atoms, cards, validations, and decisions.
- [x] Extractor: deterministic V0 extractor for reproducible fixtures.
- [x] Validator: source spans, grounding, epistemic role, confidence, causal support, source trust, and contradiction checks.
- [x] Quarantine: invalid candidates become quarantined before promotion.
- [x] Audit: `audit(memory_id)` returns provenance, validation, confidence, validity, status, and evidence counts.
- [x] Experience Card promotion: candidate atoms promote into cards and repeated evidence consolidates.
- [x] Action Brief retrieval: verified cards become task-scoped action briefs instead of raw memory dumps.
- [x] Extractor and contradiction detector refactored behind strategy interfaces.

### 2. Synthetic Eval Primitive

- [x] Synthetic corruption suite.
- [x] HaluMem-compatible local facsimile.
- [x] Workflow gotchas environment.
- [x] Contradiction fixture cases.
- [x] Explicit stale/update supersession fixture cases.
- [x] Unsupported assistant-hypothesis fixture cases.
- [x] Poisoned/untrusted-source fixture cases.
- [x] Misleading-success/non-causal fixture cases.
- [x] Failed-trace lesson fixture cases.
- [x] False-quarantine negative-control fixture cases.
- [x] Multi-session and off-task scope fixture cases.
- [x] Expired-card retrieval suppression fixture cases.
- [x] Repeated-evidence consolidation fixture cases.

### 3. Baselines

- [x] No-memory baseline.
- [x] Full-context baseline.
- [x] Raw-trace retrieval baseline.
- [x] Rolling summary / reflection baseline.
- [x] Vanilla vector memory baseline.
- [x] Time-aware vector memory baseline.
- [x] Unverified reflection / unvalidated memory baseline.
- [x] Human-curated runbook upper bound.

### 4. Workflow Proof And Reporting

- [x] Held-out workflow task succeeds with AMS V0 where no-memory fails.
- [x] Raw vector retrieval returns related traces but misses or fails the decisive precondition.
- [x] Unvalidated memory pollutes the action brief with false/stale actions.
- [x] Machine-readable eval report object.
- [x] Markdown synthetic eval report.
- [x] Public benchmark report.
- [x] README linked to current eval/report shape.

### 5. Required Metrics

- [x] Extraction precision/recall/F1.
- [x] Update recall via local HaluMem facsimile.
- [x] False memory resistance.
- [x] Contradiction detection precision.
- [x] Contradiction detection recall.
- [x] Stale-memory suppression.
- [x] Quarantine false-positive rate.
- [x] Evidence support/consolidation metrics.
- [x] Action-brief relevance recall.
- [x] Action-brief pollution rate.
- [x] Scoped-memory suppression.
- [x] Expired-memory suppression.
- [x] Audit completeness rate.
- [x] Memory harm rate.
- [x] Action influence rate.
- [x] p95 write latency.
- [x] p95 retrieval latency.
- [x] Tokens per write.
- [x] Tokens per retrieval.

### 6. External Benchmark Decision And Adapters

- [x] Decide whether to integrate real HaluMem now or keep strengthening the local facsimile first.
- [x] Real HaluMem runner or dataset adapter.
- [x] MemoryArena-style adapter.
- [x] LongMemEval-V2-style adapter.

### 7. External Benchmark Runner Layer

- [x] AMS-backed HaluMem write-path runner.
- [x] AMS-backed MemoryArena action-coupling runner.
- [x] AMS-backed LongMemEval-V2 trajectory/retrieval runner.
- [x] Unified external benchmark report object.

### 8. Gated Later Work

Do not start these until the AMS V0 proof items above and the external benchmark runner layer are done and verified.

- [x] Storage/backend adapters.
- [x] MCP integration.
- [x] Multi-agent protocol.

### 9. Usable Local Memory System

- [x] AMS v1 plan grounded with MIT-12 and Claude Opus 4.7 review.
- [x] Local CLI entry point: `python scripts/ams.py`.
- [x] Persistent root default: `~/.codex/memory/cem`.
- [x] Session continuity with current-session rotation.
- [x] `remember` command writes learned experience through AMS validation.
- [x] `pin` command stores explicit directives separately from learned experience.
- [x] `bootstrap-codex` seeds this workspace's first Codex directives without creating AMS cards.
- [x] `brief` command returns directives plus verified AMS action recommendations.
- [x] `list` and `audit` expose cards, atoms, and directives.
- [x] Subprocess tests cover persistence, quarantine, directives, bootstrap idempotency, root isolation, and JSON output.

### 10. Migration And Monitor Operations

- [x] AMS v1.1 migration and monitor plan written.
- [x] Migration dry-run builds a reviewable ledger without mutating memory.
- [x] Migration apply pins curated directives and remembers verified operational experience idempotently.
- [x] Migration records write JSONL, latest JSON, and latest Markdown.
- [x] Monitor-0 checks root, SQLite, directives, learned cards, and action-brief guardrails.
- [x] Monitor records write JSONL, latest JSON, and latest Markdown.
- [x] Dashboard command summarizes counts and latest migration/monitor state.
- [x] Subprocess tests cover migration, monitor, dashboard, and failure visibility.

### 11. Memory Use Controller

- [x] Dashboard and monitor separate AMS operational records from global Codex behavior records.
- [x] Dashboard exposes completed-through, current phase, and next step.
- [x] Add bounded `startup-brief` / controller command.
- [x] Enforce directive cap, card cap, evidence cap, and approximate token budget.
- [x] Attach monitor id, brief id, and evidence ids to startup gate output.
- [x] Warn/degrade session-start readiness when required startup directives are missing.
- [x] Wire `startup-brief` into `scripts/session-start-gate.ps1`.
- [x] Verify global `ams-memory` MCP availability after Codex runtime restart.

### 12. Correction Capture Controller

- [x] Add correction event schema.
- [x] Add deterministic V0 mistake classifier.
- [x] Add correction router for directives, AMS failure-mode candidates, project ledger entries, stale/contradicted memory review, and human resume gate.
- [x] Add `correction capture`, `correction gate`, `correction list`, and `correction resume` CLI commands.
- [x] Add Monitor-0 checks for correction controller wiring, resume gate state, recorded corrections, and correction directive surfacing in action briefs.
- [x] Add subprocess tests for plan-first violation, repeated drift, routing, resume gate, and action-brief retrieval.
- [x] Wire Correction Capture Controller into live agent runtime hooks beyond the CLI surface. Runtime-agnostic `correction_hooks.py` core (`hook_on_user_prompt_submit` classify-first/zero-side-effect-on-benign + `hook_on_pre_tool_use_gate` fail-closed deny; `HookDecision` + named exit codes); `correction hook-prompt`/`hook-gate` CLI subcommands (untyped stdin + UTF-8-BOM tolerant; `main()` maps the decision to the exit code); two PowerShell wrappers mirroring `session-start-gate.ps1`. Monitor-0 single-source-of-truth bridge test; human-approval-only resume preserved (no agent self-resume). **169 pytest green (+15); both gate canaries bit; PS wrappers smoke-verified end-to-end (caught a real PS UTF-8-BOM stdin bug pytest missed).** Live Codex payload projection is now verified in §14; Codex command-hook blocking is not.

### 13. AMS Full Kernel Build

Full AMS kernel program (Approach C, eval-first), per `docs/2026-05-28-causal-experience-memory-full-program-design.md` and the round-2 phase sequencing. Every lifecycle transition, retrieval decision, and action-improvement claim must be auditable, testable, and measurable. No stubs, no fake-green.

- [x] Phase 0 - Contract lock: evidence primitives (`VerificationProbe`, `VerificationResult`, `ActionBriefRecord`, `ActionInfluenceEvent`, `ConfidenceInterval`, `ExpectedActionDeltaSource`); `ExperienceCard`/`ActionBrief` field extensions; SQLite + in-memory persistence for the new tables; `promote()`/`apply_verification_result()` lifecycle separation (asserted-promotion bug fixed); locked eval protocol (MMA + 10-baseline ladder + leakage guard); no-fake-green AST guard with failure canaries.
- [x] Phase 1 - Full vertical skeleton: end-to-end trace -> atom -> card -> action brief -> influence event path with real persisted state at every hop, no stubs. Brief enrichment (sourced delta + score breakdown), `ActionBriefRecord` persistence, observational `close_influence`, `run_vertical_loop` + MMA, and a runnable script consumer; independently verified (canaries bite, no ghost code, no scope leak).
- [x] Phase 2 - Grounded consolidation + verification: real consolidation into cards and the evidence-gated verification loop (probes -> results -> verified promotion). Consolidation pipeline (dedup -> near-duplicate merge -> source-span preservation -> grounded abstraction -> exception boundaries -> temporal supersession -> contradiction links) and the verified lifecycle (held-out replay probe measures lift; only `apply_verification_result` sets `verified`; negative controls suppressed at 100%). Driven from `run_vertical_loop` (reports `verified_card_count` + `negative_control_suppression_rate`); independently verifier-refuted (107 pytest green, two canaries proven to bite, scorer still `lexical_overlap_v0`).
- [x] Phase 3 - Action-value retrieval: task-scoped action briefs ranked by measured/expected action value, with influence events recorded. Replaced `lexical_overlap_v0` with the transparent feature ranker `action_value_v1` (precondition_match + verified_lift_prior + recency_temporal - contradiction_penalty - staleness_penalty, plus the preserved normalized lexical floor); `verified_lift_prior` hard-gated to 0.0 until a passed probe sets `measured_lift`; per-feature `score_breakdown_by_card` persisted with an assertable weighted-sum==total invariant; `expected_action_delta` sourced (`probe_verified`/`observational_unverified`/`none`, never invented); relevance-keyed selection so penalties never silently drop a relevant card. 114 pytest green; two canaries proven to bite (W_LIFT=0 flips the lift-dominance canary; removing tz-coercion reproduces the naive-datetime TypeError). Pre-registered weights recorded for the Phase 4 single-shot held-out rule.
- [x] Phase 4 - MMA + baseline ladder exam: run all 10 baselines honestly on held-out tasks against the locked eval protocol; report MMA with 95% CI and the >=5pp lexical margin. Built `eval_protocol.beats_lexical_by_margin`/`lexical_margin_pp` (the missing >=5pp gate), `phase4_dataset.py` (12 paraphrased held-out tasks + the corruption-fixture memory source, namespace-disjoint leakage guard), `phase4_exam.py` (all 10 BASELINE_LADDER rungs, paired per-task scoring, MMA+CI per rung, two gates), and `scripts/run_phase4_exam.py`. Single-shot held-out result at the LEDGER-018 locked weights: **AMS MMA 0.833 (95% CI [0.613, 1.054], n=12) vs lexical 0.083 -> margin 75.0pp; PASS**; negative-control suppression 1.0; AMS beats every honest baseline (best non-AMS = summary 0.333) and sits below the human_runbook ceiling (1.0). 126 pytest green (10 new canaries); margin honest (lexical/vector/full-context surface the planted traps AMS validates away).
- [x] Phase 5 - Hardening: latency budgets, failure-mode coverage, and production-readiness gates. Shared module-level `card_is_inactive` predicate (one inactivity axis for supersession/retrieval/loop count). Phase 4 exam determinism fix (`EVAL_NOW` anchored to the build clock; a fixed past instant future-dated all cards out of scope -> MMA collapsed to 0). LOCKED `RETRIEVAL_LATENCY_BUDGET_MS=50.0` + `within_latency_budget` (`<=`); p95 AMS-rung retrieval latency wired into the Phase 4 report (fail-closed sample-count guard; verdict unchanged). Failure-mode coverage (`tests/test_fail_closed.py`: empty-store graceful, missing-id KeyError store+kernel, run_probe null-target ValueError, StrictModel ValidationError). Composite `production_readiness.py` gate (`ready` = all of mma_passes + beats_lexical_by_margin + suppression==1.0 + within_latency_budget + no-fake-green-AST-clean), reusing a shared `fake_green_guard.py` scanner that now also policies the gate module. **154 pytest green; exam reproduces AMS MMA 0.833 / 75pp / PASS, p95 ~12ms within 50ms budget; 6 canaries proven to bite; dynamic design + adversarial-review workflows (1 finding fixed).**

### 14. Primary Runtime Adoption

The kernel, MCP bridge, startup gate, hook wrappers, default Codex entrypoint wrapping, memory-surface reconciliation, governed-run close/finalize, automatic runtime trace intake, aging/maintenance review, fresh operator proof, and frontier eval rerun are complete.

- [x] Lock `PRODUCT-LOCK.md` as the canonical product acceptance source.
- [x] Start the execution plan from the product lock (`docs/2026-05-31-ams-product-lock-execution-plan.md`).
- [x] Audit the repo against `PRODUCT-LOCK.md` and mark each acceptance criterion pass/partial/fail with evidence.
- [x] Write independent review prompts for Greptile and optional Codex review (`docs/2026-05-31-ams-review-prompts.md`).
- [x] Attach `brief_id`, `monitor_id`, and evidence ids to governed-run receipts created by `startup-brief`; expose the latest receipt in dashboard output.
- [x] Live runtime smoke: confirm the real Codex hook payload projection for `scripts/correction-hook-prompt.ps1` and `scripts/correction-hook-gate.ps1`. `UserPromptSubmit` sends `prompt` + `session_id`; the prompt wrapper maps them correctly. `PreToolUse` invokes the gate wrapper before tools. **Finding:** Codex CLI 0.128.0 command hooks report non-zero exits as hook failures but do not block the turn/tool; evidence recorded in `docs/2026-05-31-codex-hook-runtime-smoke.md`.
- [x] Replace the Codex command-hook exit-code blocking assumption with an enforceable AMS runtime control path: `ams runtime-control` records allow/degraded/block receipts and `scripts/ams-guarded-command.ps1` refuses to invoke the downstream command only when runtime-control/action-safety blocks.
- [x] Wire the AMS guarded launcher into the default Codex entrypoint. `scripts/install-ams-codex-entrypoint.ps1` installed wrappers for `codex.ps1`, `codex.cmd`, and Git Bash `codex` with `codex.ams-original*` backups and `AMS_CODEX_BYPASS=1` escape hatch; live smoke proves missing memory degrades before raw Codex runs while correction prompts can still block through action-safety.
- [x] Reconcile legacy Codex memories, `codex-memory`, and `ams-memory` so AMS is the primary startup source. `ams memory-surfaces` reports `ams-memory` as primary, `codex-memory` as secondary, and native Codex memory as an applied secondary import source; tests include a canary that fails until the legacy registry is actually migrated.
- [x] Add governed-run close/finalize records for outcomes and influence. `ams governed-run close` finalizes receipts with observed outcome, links back to the startup/action brief, writes the observational influence event, refuses to fake-close receipts missing action-brief/influence ids, and the guarded launcher now auto-closes governed receipts after blocked, allowed, and downstream-launch-failure outcomes.
- [x] Add automatic real trace intake from ordinary Codex work. `ams runtime-trace record` ingests guarded work as real `AgentTrace` evidence, proposes marker-backed memory candidates with source spans, writes `runtime-trace-latest`, dashboard exposes the latest trace, and `scripts/ams-guarded-command.ps1` records traces automatically after allow/degraded/block decisions and downstream launch failures without polluting quiet raw command output; quiet mode still reports AMS trace-recording failures to stderr.
- [x] Add aging and maintenance checks as a product surface. `ams maintenance review` now detects expired, stale, contradicted, inactive, and pending memory records; monitor names maintenance risks without making them execution authority; dashboard exposes `latest_maintenance`; expired/inactive records are pinned by canaries so they do not leak into action briefs.
- [x] Package the local operator path. `scripts/run_ams_operator_proof.py` creates a fresh local AMS root, writes isolated Codex memory/config inputs, runs init/bootstrap/remember/migrate, proves `ams-memory` primary and legacy memory secondary, retrieves a startup brief, runs maintenance, runs Monitor-0 deep checks, audits a real card, closes the governed run with outcome success, and reruns the Phase 4 frontier eval. Final proof: `AMS_OPERATOR_PROOF_PASS`, startup `brief_f3a88b2624454ddd886505de39e407f6`, monitor `monitor_17adf0c7bc9f4d84a906210bce318d0f`, maintenance items `0`, governed run `run_946ba867b16947438ac0a50919b66619 outcome=success`, frontier eval `PASS margin=75.0pp`.

## Historical Schedule Note

The original spec used Week 1 through Week 4 as a human-readable grouping of work. That is not the active schedule. For this AI build, the active schedule is the ordered queue above: take the next unchecked item, implement it, verify it, commit it, push it, and continue.
