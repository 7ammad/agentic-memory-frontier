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

- [ ] Make `audit(memory_id)` include the validation decision summary.
- [ ] Add a machine-readable eval report object with timestamp, suite name, baseline rows, and CEM-0 row.
- [ ] Add a small markdown report writer for the synthetic corruption suite.
- [ ] Link the latest eval report shape from `README.md`.

## Later, Not Yet

- [ ] Add raw trace retrieval baseline.
- [ ] Add summary/reflection baseline.
- [ ] Add HaluMem-style adapter or local facsimile.
- [ ] Add workflow gotchas environment.
- [ ] Add storage adapters only after the write-path and action-brief evals are stronger.
