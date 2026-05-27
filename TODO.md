# CEM-0 Build TODO

This is the continuation rail for CEM-0. It is ordered. Work from the first unchecked item downward.

## Continuation Rule

After finishing any checked item:

1. Run the relevant verification commands.
2. Commit and push if the work is clean.
3. Update this TODO.
4. Continue to the next unchecked item unless blocked, explicitly redirected, or the context-save hardgate is triggered.

Do not stop at "task complete" when the next unchecked item is clear.

## Source Of Truth

- `research/2026-05-27-plan-1-causal-experience-memory-foundation.md`
- `specs/2026-05-27-cem-0-memguard-kernel-spec.md`
- `sessions/2026-05-27-cem-0-session-handoff.md`

The old A/B/C/D work remains historical infrastructure context. The active dependency order is:

```text
Plan 1 foundation -> CEM-0 proof -> backend adapters -> MCP integration -> multi-agent protocol
```

Backend adapters, MCP integration, and multi-agent protocol stay gated until the CEM-0 proof is stronger.

## Guardrails

- Stay on CEM-0 write-path quality and eval strength.
- Do not drift into MCP, database adapters, dashboards, or platform integrations before the proof work below is done.
- Keep deterministic fixtures until the eval primitive is stronger.
- Do not claim state-of-the-art.
- Never read or write `C:\Dev\Builds\Waki`.

## Ordered Build Queue

### 0. Foundation Lock

- [x] A: Deep technical review of SuperClaude memory MCP.
- [x] B: SuperClaude memory v0.3 upgrade spec.
- [x] C: Codex memory system design.
- [x] D: ACS protocol design.
- [x] Plan 1: Causal Experience Memory thesis locked.
- [x] CEM-0 / MemGuard Kernel spec written.

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

- [x] Held-out workflow task succeeds with CEM-0 where no-memory fails.
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

- [x] CEM-backed HaluMem write-path runner.
- [x] CEM-backed MemoryArena action-coupling runner.
- [x] CEM-backed LongMemEval-V2 trajectory/retrieval runner.
- [x] Unified external benchmark report object.

### 8. Gated Later Work

Do not start these until CEM-0 proof items above and the external benchmark runner layer are done and verified.

- [x] Storage/backend adapters.
- [x] MCP integration.
- [x] Multi-agent protocol.

## Historical Schedule Note

The original spec used Week 1 through Week 4 as a human-readable grouping of work. That is not the active schedule. For this AI build, the active schedule is the ordered queue above: take the next unchecked item, implement it, verify it, commit it, push it, and continue.
