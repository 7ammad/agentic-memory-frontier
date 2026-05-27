# CEM-0 Build TODO

This file is the continuation rail for CEM-0. Codex should update it as work lands.

## Continuation Rule

After finishing any checked item:

1. Run the relevant verification commands.
2. Commit and push if the work is clean.
3. Update this TODO with what became done and what is now next.
4. Start the next unchecked item in the same lane unless blocked, explicitly redirected, or the context-save hardgate is triggered.

Do not stop at "task complete" when there is a clear next unchecked item.

## Guardrails

- Stay on CEM-0 write-path quality and eval strength.
- Do not drift into MCP, database adapters, dashboards, or platform integrations.
- Keep deterministic fixtures until the eval primitive is stronger.
- Do not claim state-of-the-art.
- Never read or write `C:\Dev\Builds\Waki`.

## Full Agreed Program Checklist

This is the full plan as captured in `AGENTS.md` and `research/2026-05-27-plan-1-causal-experience-memory-foundation.md`, not a new plan.

### Historical Design Work

- [x] A: Deep technical review of SuperClaude memory MCP.
- [x] B: SuperClaude memory v0.3 upgrade spec.
- [x] C: Codex memory system design.
- [x] D: ACS protocol design.

### Current Dependency Order

- [x] Plan 1 foundation: Causal Experience Memory thesis locked.
- [ ] CEM-0 proof: prove write-path integrity and action advantage.
- [ ] Backend adapters.
- [ ] MCP integration.
- [ ] Multi-agent protocol.

Current rule: backend adapters, MCP integration, and multi-agent protocol stay unchecked until the CEM-0 proof is stronger.

## Original CEM-0 Plan Checklist

This is the source-of-truth checklist from the CEM-0 spec and foundation plan. Keep this section honest: checked means implemented and covered by current repo evidence, unchecked means still to build.

### Kernel Build Order

- [x] Models: Pydantic schemas for traces, atoms, cards, validation, action briefs, and audits.
- [x] Trace ledger: JSONL plus SQLite persistence for traces, atoms, cards, validations, and decisions.
- [x] Extractor: deterministic V0 extractor for reproducible fixtures.
- [x] Validator: source spans, grounding, epistemic role, confidence, causal support, source trust, and contradiction checks.
- [x] Quarantine: invalid candidates become quarantined before promotion.
- [x] Audit: `audit(memory_id)` returns provenance, validation, confidence, validity, status, and evidence counts.
- [x] Baselines: no-memory, raw-trace retrieval, summary/reflection, and unvalidated-memory baselines.
- [x] Synthetic eval: corruption suite with contradictions, stale/update, unsupported, poisoned, misleading-success, scope, expiry, and repeated-evidence cases.
- [x] Experience Card promotion: candidate atoms promote into cards and repeated evidence consolidates.
- [x] Action Brief retrieval: verified cards become task-scoped action briefs instead of raw memory dumps.
- [x] Workflow demo: local workflow-gotcha demo compares baseline attempts against CEM-0.
- [x] Public benchmark report: polished, reproducible report suitable for external readers.

### Evaluation Targets

- [x] HaluMem-compatible local facsimile.
- [x] Synthetic corruption suite.
- [x] Workflow gotchas environment.
- [ ] Real HaluMem runner or dataset adapter.
- [ ] MemoryArena-style adapter.
- [ ] LongMemEval-V2-style adapter.

### Required Metrics

- [x] Extraction precision/recall/F1.
- [x] Update recall via local HaluMem facsimile.
- [x] False memory resistance.
- [x] Contradiction detection precision.
- [x] Contradiction detection recall.
- [x] Stale-memory suppression.
- [x] Quarantine false-positive rate.
- [ ] Memory harm rate as a named report metric.
- [ ] Action influence rate.
- [x] Evidence support/consolidation metrics.
- [ ] p95 write latency.
- [ ] p95 retrieval latency.
- [ ] Tokens per write.
- [ ] Tokens per retrieval.
- [x] Action-brief relevance recall.
- [x] Action-brief pollution rate.
- [x] Scoped-memory suppression.
- [x] Expired-memory suppression.
- [x] Audit completeness rate.

### Required Baselines

- [x] No memory.
- [x] Full-context baseline.
- [x] Rolling summary / reflection baseline.
- [x] Vanilla vector memory baseline.
- [x] Time-aware vector memory baseline.
- [x] Unverified reflection / unvalidated memory baseline.
- [x] Human-curated runbook upper bound.

### First Demo Acceptance Criteria

- [x] CEM-0 quarantines at least one unsupported or contradictory memory.
- [x] CEM-0 promotes at least one Experience Card with source evidence.
- [x] Held-out workflow task succeeds with CEM-0 where no-memory fails.
- [x] Raw vector retrieval returns related traces but misses or fails the decisive precondition.
- [x] `audit(memory_id)` explains why the memory exists, where it came from, why it was promoted/quarantined, and when it is valid.
- [x] Eval report includes all required baselines, including a dumb baseline expected to lose.

### 30-Day Sprint Status

- [x] Week 1: scaffold packages, models, trace ledger, synthetic trace generator.
- [x] Week 2: extractor, source grounding, contradiction detector, quarantine, audit logs.
- [x] Week 3: local HaluMem facsimile, partial baselines, first integrity table.
- [ ] Week 3 remaining: real/external benchmark adapter decision and missing baseline coverage.
- [x] Week 4: workflow demo, Experience Card promotion, Action Brief retrieval, held-out task comparison.
- [x] Week 4 remaining: public-ready benchmark report.

## Current State

- [x] Scaffold CEM-0 kernel: trace ingest, deterministic extraction, validation, quarantine, promotion, action brief, audit.
- [x] Add unvalidated memory vs CEM-0 validation baseline.
- [x] Add write-path metrics: false memory resistance, contradiction recall, false quarantine rate, promoted count, action brief card count.
- [x] Refactor extractor and contradiction detector behind strategy interfaces.
- [x] Expand synthetic corruption eval to 9 labeled fixture cases.
- [x] Add validation decision aggregation, decision reason codes, and per-risk metric breakdown.
- [x] Add stale-memory fixture cases with explicit update supersession.
- [x] Add poisoned-memory fixture cases with untrusted-source quarantine.
- [x] Add misleading-success fixture cases with non-causal derived-claim quarantine.
- [x] Add failed-trace lesson fixture cases with valid failure-mode promotion.
- [x] Add action-brief recommended-action assertions and unvalidated-memory harm checks.
- [x] Add no-memory baseline row to the synthetic eval.
- [x] Add `expected_action_delta` placeholder computation from fixture labels.
- [x] Make atom and card audits include validation decision summaries.
- [x] Add a machine-readable eval report object with baseline rows and CEM-0 row.
- [x] Add a markdown report writer for the synthetic corruption suite.
- [x] Link the latest eval report shape from `README.md`.
- [x] Add raw trace retrieval baseline.
- [x] Add summary/reflection baseline.
- [x] Add HaluMem-style local facsimile runner.
- [x] Add workflow gotchas environment.
- [x] Add repeated-evidence consolidation fixture.

## Active Lane: Write-Path Decision Quality

- [x] Add a `ValidationDecision` model that aggregates check results into one decision.
  - Inputs: atom id, validation results, contradiction links, confidence, expected status where available.
  - Outputs: `candidate` or `quarantined`, reason codes, metric labels, human-readable explanation.
  - First files: `packages/cem-core/src/cem_core/models.py`, `packages/cem-core/src/cem_core/validator.py`, `tests/test_cem_kernel.py`.
  - Verification: `python -m pytest`, `python scripts/run_synthetic_eval.py`.

- [x] Replace string-matched quarantine checks in the eval with decision reason codes.
  - Goal: metrics should read validator decisions, not quarantine reason prose.
  - First files: `packages/cem-eval/src/cem_eval/synthetic_corruption.py`, `packages/cem-core/src/cem_core/validator.py`.

- [x] Add per-risk-type metric breakdown.
  - Report false memory resistance by `contradiction`, `assistant_hypothesis`, and `unsupported`.
  - Report valid-memory retention by `valid_preference`, `valid_instruction`, `valid_skill`, and `valid_failure_mode`.

## Next Lane: Eval Suite Strength

- [x] Add stale-memory fixture cases.
  - Example: later user preference supersedes old preference without treating historical truth as deleted.
  - Needed outcome: current memory is promoted or selected, stale memory is suppressed or marked contested.

- [x] Add poisoned-memory fixture cases.
  - Example: adversarial or unrelated trace tries to insert an operational instruction.
  - Needed outcome: quarantine or scope-block before it becomes trusted experience.

- [x] Add misleading-success fixture cases.
  - Example: successful trace includes irrelevant action that should not become the recommended strategy.
  - Needed outcome: unsupported or non-causal action does not become a promoted card.

- [x] Add failed-trace lesson fixture cases.
  - Example: a failure trace contains the critical negative rule.
  - Needed outcome: valid failure mode can be promoted into an action brief warning.

## Next Lane: Action-Brief Utility

- [x] Add held-out task assertions that check decisive recommended action text, not just card count.
- [x] Add a no-memory baseline for held-out task success.
- [x] Add an unvalidated-memory harm check where a false card pollutes the action brief.
- [x] Add `expected_action_delta` placeholder computation from fixture labels.

## Next Lane: Audit And Reporting

- [x] Make `audit(memory_id)` include the validation decision summary.
- [x] Add a machine-readable eval report object with timestamp, suite name, baseline rows, and CEM-0 row.
- [x] Add a small markdown report writer for the synthetic corruption suite.
- [x] Link the latest eval report shape from `README.md`.

## Later, Not Yet

- [x] Add raw trace retrieval baseline.
- [x] Add summary/reflection baseline.
- [x] Add HaluMem-style adapter or local facsimile.
- [x] Add workflow gotchas environment.
- [ ] Add storage adapters only after the write-path and action-brief evals are stronger.

## Next Lane: Eval Hardening V2

- [x] Add repeated-evidence consolidation fixture.
  - Example: the same valid skill appears in multiple successful traces.
  - Needed outcome: support count increases without duplicating action-brief cards.

- [x] Add false-quarantine negative-control fixture.
  - Example: two similar-looking memories have different scopes and should both survive.
  - Needed outcome: contradiction detection respects scope before quarantine.

- [x] Add multi-session scope fixture.
  - Example: preference in one session should not leak into a different project/session unless scope allows it.
  - Needed outcome: action brief excludes out-of-scope memory.

- [x] Add report comparison against the new hardening cases.
  - Needed outcome: synthetic report distinguishes write-path integrity from action-brief utility.

## Next Lane: Action-Brief Metrics V2

- [x] Add action-brief relevance recall and pollution-rate metrics.
  - Needed outcome: reports separate "retrieved the right operational experience" from "avoided wrong/out-of-scope experience".

- [x] Add scoped-memory suppression metric.
  - Needed outcome: off-task true memories can be promoted while being excluded from unrelated held-out briefs.

- [x] Add evidence consolidation metric.
  - Needed outcome: repeated evidence increases support without inflating action-brief card count.

- [x] Add markdown/report rows for the new action-brief utility metrics.
  - Needed outcome: humans can read utility, integrity, and scope behavior without decoding raw JSON.

## Next Lane: Temporal Validity V1

- [x] Add expired-card retrieval suppression.
  - Needed outcome: cards outside `valid_from` / `valid_until` do not appear in action briefs.

- [x] Add temporal-validity synthetic fixture.
  - Needed outcome: stale-but-on-topic true memories are stored or deprecated correctly but not recommended after expiry.

- [x] Add temporal validity metrics to the synthetic report.
  - Needed outcome: report exposes expired memory suppression separately from contradiction and false-memory resistance.

- [x] Update README with temporal-validity expected signal.
  - Needed outcome: current smoke output documents the time-validity behavior.

## Next Lane: Audit Explainability V1

- [x] Add audit provenance, confidence, validity, and evidence-count fields.
  - Needed outcome: `audit(memory_id)` can explain where a memory came from, how trusted it is, and when it is valid.

- [x] Add synthetic audit completeness metric.
  - Needed outcome: eval reports whether promoted cards have source spans, validation decisions, confidence, and validity metadata.

- [x] Add markdown audit section for CEM-0 report.
  - Needed outcome: humans can inspect audit coverage without decoding raw atom/card payloads.

- [x] Update README with audit explainability expected signal.
  - Needed outcome: current smoke output documents auditability alongside write-path and action-brief behavior.

## Next From Original Plan: CEM-0 Proof Completion

- [x] Complete held-out workflow comparison reporting.
  - Original source: Week 4 says "Run held-out task comparison."
  - Needed outcome: report shows no-memory, raw-trace, summary/reflection, unvalidated-memory, and CEM-0 workflow success side by side.

- [x] Add Marginal Memory Advantage / workflow success delta.
  - Original source: benchmark strategy says `MMA = TaskSuccess(memory_agent) - TaskSuccess(no_memory_agent)`.
  - Needed outcome: eval reports CEM-0's held-out workflow advantage against each baseline, not just write-path integrity.

- [x] Write public-ready benchmark report.
  - Original source: Week 4 says "Write public-ready benchmark report."
  - Needed outcome: current smoke output connects audit/write-path quality to held-out task behavior and is readable outside the codebase.

## Next From Original Plan: Missing Baselines And Metrics

- [x] Add full-context baseline.
  - Original source: required baselines include "full context."
  - Needed outcome: compare CEM-0 against an agent given all fixture trace text.

- [x] Add vanilla vector memory baseline.
  - Original source: required baselines include "vanilla vector memory."
  - Needed outcome: compare CEM-0 against semantic retrieval over raw memories/traces.

- [x] Add time-aware vector memory baseline.
  - Original source: required baselines include "time-aware vector memory."
  - Needed outcome: compare CEM-0 against recency-aware semantic retrieval.

- [x] Add human-curated runbook upper bound.
  - Original source: required baselines include "human-curated runbook upper bound."
  - Needed outcome: establish the best expected action brief for the fixture.

- [x] Add extraction precision/recall/F1.
  - Original source: required metrics include extraction precision, recall, and F1.
  - Needed outcome: evaluate proposed atoms against fixture labels before validation.

- [x] Add contradiction detection precision.
  - Original source: required metrics include contradiction detection precision.
  - Needed outcome: distinguish true contradictions from safe same-key/different-scope cases.

- [ ] Add memory harm rate as a named report metric.
  - Original source: required metrics include memory harm rate.
  - Needed outcome: expose the share of action guidance polluted by false, stale, unsupported, or out-of-scope memory.
