# IDEA

Canonical project idea source of truth.

Date locked: 2026-05-29

## One-Line Thesis

Memory is not storage. Memory is verified experience that improves future action.

## Project Definition

Agentic Memory System (AMS) is a research-build workspace and product line for
a local, auditable memory operating layer that turns raw agent trajectories into
evidence-backed, temporally scoped, action-relevant experience.

The system should not merely save and retrieve memories. It should prove that a
memory is grounded, current, safe to trust, useful for the task, and measurably
improves future agent behavior.

## Why The Docs Drifted

The project passed through several valid but different stages without a single
idea source of truth:

1. A/B/C/D infrastructure design: SuperClaude memory review, SC v0.3 spec, Codex
   memory twin, and ACS protocol.
2. A broader "universal agent memory onboarding" idea.
3. The research pivot into Causal Experience Memory.
4. CEM-0 / MemGuard as the first kernel wedge.
5. CEM-1 as the full vertical kernel and proof loop.
6. AMS operator/runtime controls around the kernel.

Those layers are related, but they are not equal. This file is the canonical
idea definition. `PRODUCT-LOCK.md` is the canonical product acceptance lock.
Other docs should point to both when explaining what the project is and what
counts as complete.

## Parked A/B/C/D Context

A/B/C/D are historical and supporting infrastructure, not the core invention:

- A: Deep technical review of SuperClaude memory MCP.
- B: SuperClaude memory v0.3 upgrade spec.
- C: Codex memory system design / memory twin.
- D: ACS protocol design for agent-to-agent coordination.

They remain useful later as backend, interop, and multi-agent infrastructure.
They are not the product thesis.

## Research Candidates That Were Nominated

The research sprint nominated five opportunity theses:

1. MemGuard - Memory Write-Path Quality Protocol.
   - Validates extracted memories before storage.
   - Detects contradictions, stale facts, unsupported claims, poisoned inputs,
     and low-confidence writes.
   - Assigns provenance, confidence, temporal validity, and quarantine status.
   - Ranked 1st and selected as the first wedge.

2. AgeProbe - Memory Lifespan Diagnostic and Repair Layer.
   - Diagnoses compression aging, interference aging, revision aging, and
     maintenance gaps.
   - Uses AgingBench-style longitudinal health checks.
   - Ranked 2nd; queued as a future extension after the core write/read proof.

3. SkillBank - Procedural Skill Memory Library.
   - Extracts reusable workflows from successful agent trajectories.
   - Inspired by Agent Workflow Memory and procedural-memory research.
   - Ranked 3rd; useful later once trace quality and verification are stable.

4. MemLedger - Multi-Agent Memory Governance Protocol.
   - Handles ownership, access policy, provenance, conflict resolution, and
     shared-memory leakage tests across agents.
   - Ranked 4th; future infrastructure, not first V1.

5. MemBench-OSS - Native Memory Evaluation Harness.
   - Unified benchmark/eval layer for HaluMem, LongMemEval, LoCoMo,
     MemoryAgentBench, AgingBench, and custom adversarial tests.
   - Marked as infrastructure; strongest as MemGuard's eval layer rather than a
     standalone first product.

## Selected Direction

The selected foundation is:

> AMS: raw trajectory -> typed evidence -> candidate memory -> verified
> experience -> future action advantage.

The selected first wedge is:

> AMS write-path quality and validity: preventing false, stale, unsupported,
> contradictory, poisoned, or non-causal memories from becoming trusted
> operational experience.

The next completed expansion is:

> AMS full kernel: the end-to-end lifecycle plus action-value retrieval,
> influence logging, verification probes, negative controls, and MMA evaluation
> against honest baselines.

## Attack Surfaces Selected First

1. Write-path integrity.
   - If false memories enter the trusted store, every retrieval strategy is
     contaminated.
   - This is why the AMS write-path was selected first.

2. Action advantage proof.
   - Memory only matters if it changes future task success.
   - CEM must beat no-memory and similarity-based memory baselines using
     Marginal Memory Advantage (MMA), not just look plausible.

3. Aging/lifespan reliability.
   - Important, but not first.
   - AgeProbe remains the next major research-product candidate once the core
      AMS proof is stable.

## Benchmark Order

1. HaluMem first.
   - Closest to the MemGuard write-path wedge: extraction, update, QA, and
     hallucination propagation.

2. MemoryArena next.
   - Tests memory-action coupling in multi-session agent environments.

3. LongMemEval-V2 next.
   - Tests environment/workflow experience and "knowledgeable colleague"
     behavior over long histories.

The project may also use custom falsification suites for contradiction,
staleness, poisoning, false success, scope bleed, and negative-memory harm.

## What Complete Means

Complete does not mean a hosted SaaS, dashboard, or broad integration platform.

Complete means a local kernel and operator surface where:

1. Real agent traces are ingested.
2. Typed Experience Atoms are extracted with source spans.
3. Atoms are validated before trust.
4. Bad memories are quarantined.
5. Good evidence consolidates into Experience Cards.
6. Cards become verified only through probes or valid evidence gates.
7. Retrieval ranks by action value, not just semantic similarity.
8. The runtime returns bounded Action Briefs, not raw memory dumps.
9. Influence events record whether the brief affected the outcome.
10. Evals report Marginal Memory Advantage against honest baselines.
11. Failures are reported honestly instead of hidden behind green-looking tests.

## Non-Goals For The Core Project

Do not let these reclaim the center before the kernel proof is solid:

- generic memory MCP server as the main product;
- vector store wrapper;
- chat summary memory;
- universal memory API;
- hosted SaaS;
- multi-tenant auth;
- dashboard-first product;
- framework integration matrix;
- broad multi-agent orchestration platform;
- enterprise compliance suite.

These can become distribution or infrastructure later. They are not the
invention.

## Source Hierarchy

Use this order when docs conflict:

1. `PRODUCT-LOCK.md` - product scope, acceptance criteria, and completion rule.
2. `IDEA.md` - project identity, thesis, selected wedge, and non-goals.
3. `TODO.md` - ordered execution rail.
4. `docs/PROJECT-LEDGER.md` - decisions, evidence, mistakes, and verification.
5. `CHANGELOG.md` - human-readable timeline.
6. Specific design/spec docs - implementation detail for a slice.

Key source documents behind this file:

- `sessions/2026-05-27-cem-0-session-handoff.md`
- `research/2026-05-27-plan-1-causal-experience-memory-foundation.md`
- `research/New reports/Report 5  Opportunity Thesis For A Disruptive V1.md`
- `research/New reports/Report 4  Unsolved Bottlenecks And Dead Ends in Agentic Memory.md`
- `specs/2026-05-27-cem-0-memguard-kernel-spec.md`
- `docs/2026-05-28-causal-experience-memory-full-program-design.md`
- `docs/cem-0-external-benchmark-decision.md`
