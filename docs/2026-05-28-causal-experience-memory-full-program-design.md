# Causal Experience Memory — Full Program Design

- Date: 2026-05-28
- Status: draft for review (uncommitted until Hammad approves)
- Decision: build the **full** Causal Experience Memory (CEM) program via **Approach C (eval-first)**
- Extends (does not supersede): `research/2026-05-27-plan-1-causal-experience-memory-foundation.md`
- Source context: `research/GPT Pro - Brutal verdict.md`, Reports 4–5, `specs/2026-05-27-cem-0-memguard-kernel-spec.md`
- Packaging target: `memguard` (a kernel + proving ground, not a platform)

---

## 1. Problem and thesis

The locked thesis is a two-clause bet (Plan 1 §18):

> **Prevent bad memories from becoming trusted experience — then prove that verified experience changes what agents do.**

- **Clause 1 — the write-path (MemGuard).** Built. Ingest trace → extract typed Experience Atoms → validate (grounding + contradiction) → quarantine/promote Experience Cards.
- **Clause 2 — the causal read-path + proof.** Not built. Retrieve by *action value*, return an Action Brief carrying an *expected action delta*, and prove via Marginal Memory Advantage (MMA) that a memory-equipped agent beats a no-memory agent on held-out tasks.

Clause 2 is the field's documented #1 dead end ("memory does not reliably improve future task success") and #3 dead end ("similarity retrieval ≠ causal retrieval"), per `GPT Pro - Brutal verdict.md`. It is also the exact thing Plan 1 §16 (line 497) deferred "after V1." **That deferral is the deadlock this program closes.**

The unifying insight: the frontier the field is stuck on *is* our own unbuilt clause 2. Completing it is both the research contribution and the product.

## 2. Goals and non-goals

### Goals

1. Complete CEM components 4–7 (consolidation, verification/promotion, causal read-path, evaluation harness) to a real, runnable, falsifiable state.
2. Produce a **real MMA number** for a CEM-equipped agent vs. a no-memory agent and the full baseline ladder, on **held-out** tasks — not synthetic fixtures.
3. Make the system **fail visibly**: no fake-green checks, no stubs reported as done, no asserted-but-unproven promotions.

### Non-goals (from Report 5 "what not to build")

- No hosted/multi-tenant API service.
- No all-framework integration matrix (LangChain/LlamaIndex/etc.).
- No graph database UI or memory browser.
- No consumer-facing app.
- No multi-agent orchestration platform.
- No full enterprise governance/compliance layer.

These are explicitly out of scope for the program, not "later phases."

## 3. Current state (verified against source, 2026-05-28)

| # | Component (Plan 1 §8) | Status | Evidence |
|---|---|---|---|
| 1 | Raw Trace Ledger (`ingest_trace`) | Built | kernel API present |
| 2 | Typed Memory Compiler (extract Atoms) | Built | extractor + schema; treat as V0 deterministic fixture |
| 3 | Write-Path Validator (grounding + contradiction) | Built | validator; synthetic eval clean |
| 4 | Experience Consolidator (dedup/merge/abstract) | Partial | merges; abstraction not verified vs. source spans |
| 5 | Verification & Promotion (probes/replays/held-out/negative controls) | Partial | promotes, but **promotion is asserted, not probe-verified** — `promotion_status` is flipped to `verified` unconditionally (`packages/cem-core/src/cem_core/kernel.py:84`, `:105`); no probe runs |
| 6 | Action-Time Adapter (**causal** retrieval + influence logging) | **Not built** | `score_card` is word-overlap (`packages/cem-core/src/cem_core/kernel.py:231`); `expected_action_delta=None` (`kernel.py:129`) |
| 7 | Evaluation Harness (MMA + falsification) | Partial | synthetic proxy only; `packages/cem-eval/src/cem_eval/halumem_runner.py:54` reuses the synthetic delta instead of running an exam |

The write-path (1–3) is the real, tested foundation. The program's weight is on **6 and 7**, with **5** hardened to make "verified" mean verified.

## 4. Target architecture — the seven components

The data primitives (Experience Atom, Experience Card, Action Brief) and their schemas are already defined and implemented per Plan 1 §7 and the CEM-0 spec; this program does not redefine them. It completes the *behavior* around them.

End-to-end flow the completed program must support:

```text
trace
  -> [1] raw trace ledger
  -> [2] typed memory compiler        (Experience Atoms)
  -> [3] write-path validator         (grounding + contradiction -> quarantine | candidate)
  -> [4] experience consolidator      (dedup/merge/abstract -> Experience Cards, supersession, contradiction links)
  -> [5] verification & promotion     (probe/replay/held-out/negative-control -> verified | deprecated)
  -> [6] action-time adapter          (causal retrieval -> Action Brief w/ expected_action_delta; logs action influence)
  -> [7] evaluation harness           (MMA vs. baseline ladder + falsification suite + kill criteria)
  -> action influence log feeds back into [5]/[7]
```

Each component below states purpose, interface, current status, and target.

### 4.1 Component 6 — Action-Time Adapter (the causal read-path) [center of gravity]

**Purpose.** Given a task context and agent state, return an Action Brief: the few cards whose application is expected to *improve the next action's outcome*, plus an explicit expected action delta and the influence id needed to later measure whether reading them changed anything.

**Current.** `retrieve_action_brief` (`kernel.py:110`) ranks cards via `score_card` (`kernel.py:231-234`), which counts shared words >3 chars between the task string and the card text — the weakest possible similarity proxy. `expected_action_delta` is hardcoded `None` (`kernel.py:129`). No action-influence is logged.

**Target.** Replace lexical overlap with an **action-value retrieval scorer**:

- **Score = f(precondition match, verified-lift prior, recency/temporal validity, contradiction penalty, staleness penalty).** Start as a transparent, inspectable feature ranker (each term auditable); a learned scorer is a later option (§10 open questions), never a black box on day one.
- **`expected_action_delta` is populated** from measured outcomes, never invented. **Phase ordering caveat:** component 5's probe-measured lift (its eventual canonical source) does not exist until Phase 2. In Phase 1 the delta is sourced from the action-influence outcome loop below (the observed action/outcome after a brief is read); once component 5 lands, probe lift supersedes it. The field must carry a real measured value or be honestly absent — it must **not** be re-hardcoded to a placeholder. The same caveat applies to the scorer's `verified-lift prior` term in §4.1: it is zero-weighted until component 5 produces lift evidence, then enabled.
- **Action influence is logged.** Each brief writes a `last_action_influence_id`; when the agent's subsequent action and outcome are observed, the loop is closed — this is the off-policy signal component 7 consumes.
- **Bounded output is preserved** (the existing startup-brief caps on directives/cards/evidence/tokens stay; retrieval stays lazy and scoped).

**Interface (unchanged signature, completed semantics).** `retrieve_action_brief(task, max_cards) -> ActionBrief` where the brief now carries a populated `expected_action_delta` and an influence id, and ranking reflects estimated action value rather than word overlap.

### 4.2 Component 5 — Verification & Promotion ("CI/CD for memory")

**Purpose.** A candidate memory becomes *verified* only by passing a verification probe; known-bad memories are caught by negative controls.

**Current.** Promotion exists but is asserted (a status flip), not earned by a probe.

**Target.**

- **Promotion gate:** `candidate -> verified` requires a **verification probe** — a held-out task or replay where applying the card's recommendation beats a no-memory control by a threshold. The measured lift is stored on the card and becomes the `expected_action_delta` source for component 6.
- **Negative controls:** injected known-false / stale / contradictory memories must be **quarantined or deprecated, not promoted**. The negative-control pass rate is a monitored metric.
- **Lifecycle:** `proposed -> candidate -> verified -> deprecated`, with `quarantined` as a terminal-until-review state, matching the Atom `promotion_status` field already in the schema.

### 4.3 Component 7 — Evaluation Harness (the proving ground) [built first]

**Purpose.** Make the central bet falsifiable. We cannot fool ourselves with synthetic proxies.

**Current.** MMA exists only as hand-authored synthetic fixtures (`packages/cem-eval/src/cem_eval/synthetic_corruption.py`, e.g. `HELD_OUT_DECISIVE_ACTIONS` line 42); the external-benchmark runners summarize datasets and reuse the synthetic delta (`halumem_runner.py:54`).

**Target.**

- **Primary metric:** `MMA = TaskSuccess(memory_agent) − TaskSuccess(no_memory_agent)` on **held-out** tasks.
- **Baseline ladder (Plan 1 §10), all run honestly:** no-memory, full-context, summary, vector RAG, time-aware RAG, temporal graph, unverified reflection, human runbook. CEM must beat the *honest* baselines, not a strawman.
- **Secondary metrics:** extraction P/R/F1, false-memory resistance, update recall, contradiction P/R, stale-memory suppression, quarantine FP rate, evidence support rate, action-influence rate, memory-harm rate, cost/latency, generalization gap.
- **Environments:** (a) the seeded web/workflow environment with planted gotchas (Plan 1 §9); (b) external benchmarks **actually run**, not summarized — HaluMem (write integrity, arXiv:2511.03506), MemoryArena (multi-agent conflict, arXiv:2602.16313), LongMemEval-V2 (long horizon, arXiv:2605.12493), AgingBench (staleness, arXiv:2605.26302). AgingBench realizes Plan 1 §10's "STALE-style invalidation" slot — it replaces that placeholder with a concrete published benchmark, not a dropped check.
- **Honesty gates wired in:** the 10-item falsification suite (Plan 1 §10) and the kill criteria (§13 below) run as part of the harness and can mark the program failed.

### 4.4 Component 4 — Experience Consolidator

**Purpose.** Turn validated atoms into durable, deduplicated, abstracted cards without inventing claims.

**Current.** Merges exist; abstraction is not checked against source spans; supersession is link-only.

**Target.**

- Dedup/merge atoms into cards; **abstraction must be grounded** — every generalized claim traces to its `source_spans` (defends dead end #2, "experience abstraction unverified").
- **Temporal supersession:** a newer atom that contradicts an older one sets `superseded_by` and deactivates the stale card for retrieval (not merely a link).
- Maintain contradiction links so component 6's contradiction penalty has real input.

### 4.5 Components 1–3 (built) — invariants to preserve

Ingest, extraction, and write-path validation stay as-is. The program must not regress their tested behavior (synthetic false-memory resistance, contradiction recall). The deterministic extractor/contradiction detector remain V0 fixtures, not the final reasoning layer (per existing AMS directives).

## 5. Sequencing — Approach C (eval-first), phased

Each phase is independently testable and becomes its own implementation plan (`writing-plans`). The program is fully specified here; **Phase 0 is the first slice taken to plan mode.**

- **Phase 0 — Proving-ground spine.** Build component 7's real exam: the seeded environment, the baseline ladder (≥ no-memory + full-context + summary + unverified-reflection to start), the MMA harness, and the falsification suite. Outcome: we can score *any* memory config against a no-memory control on held-out tasks. **No capability change ships in Phase 0** — it is the measuring instrument.
- **Phase 1 — Causal read-path.** Build component 6 test-first against the Phase 0 spine. Outcome: the **first real MMA number** for the current write-path under action-value retrieval, plus populated `expected_action_delta` and action-influence logging.
- **Phase 2 — Verification & promotion.** Harden component 5 (probe-gated promotion + negative controls). Outcome: `verified` cards carry measured lift; false memories fail the negative-control gate. Re-measure MMA.
- **Phase 3 — Consolidation depth.** Component 4 (grounded abstraction + real supersession). Re-measure MMA and contradiction metrics.
- **Phase 4 — External benchmark integration.** Run CEM vs. the full ladder on HaluMem / MemoryArena / LongMemEval-V2 / AgingBench (replace the synthetic-delta reuse at `halumem_runner.py:54`). Outcome: external, comparable MMA + write-integrity numbers.

**Phase gate (every phase):** MMA does not regress (measured with fixed seeds, or outside a pre-registered noise band when stochastic, so normal run-to-run variance neither trips nor masks the gate), the falsification suite stays green, no kill criterion trips, and full `pytest` + synthetic eval pass. A phase is not "done" until its gate is met with executed evidence.

## 6. Acceptance criteria / Definition of Done (anti-ghost-coding gates)

These are hard requirements, derived directly from this project's recorded failures (the "skeleton scope" and "fake-green monitor" corrections) and Hammad's standing rule.

1. **No stubs reported as done.** A component is "done" only with **grep-proof of real consumers** wired end-to-end — file existence is not functionality.
2. **No fake-green checks.** No monitor/health check may return a hardcoded `True`. (Direct reference: the existing `operations.py:234` and `:249` literal-`True` checks are a known anti-pattern to *not* repeat, and to fix on a separate track.) An honest failing check beats a fake passing one.
3. **No asserted promotions.** A memory may be labeled `verified` only after passing a real verification probe with stored, reproducible lift.
4. **Every "done" claim carries executed evidence** — command output / test pass / MMA number — not a description of intent.
5. **MMA is reported with its baseline ladder.** A bare "memory helps" claim is invalid; the no-memory control number must accompany it.
6. **Fail visibly.** If MMA ≤ 0 after honest effort, the program says so (see kill criteria) rather than trimming the test to pass.

## 7. Testing strategy

- **Unit + integration:** `python -m pytest` (full suite) stays green every phase.
- **Synthetic eval:** `python scripts/run_synthetic_eval.py` (false-memory resistance, contradiction P/R, action-brief pollution) stays clean.
- **Exam:** the Phase 0 MMA harness runs CEM vs. baseline ladder on held-out tasks; numbers recorded in `CHANGELOG.md` + `docs/PROJECT-LEDGER.md`.
- **Negative controls:** injected false/stale/contradictory memories must be suppressed; the suppression rate is asserted in tests.
- **Ablations:** memory-on vs. memory-off vs. unverified-reflection, to isolate the causal contribution.
- **No-fake-green guard:** a test asserts that no monitor/health check in this program's harness is a hardcoded constant — it inspects each check's evaluated value against a literal-`True`/`False` constant and fails if found. This enforces §6.2 mechanically rather than by convention, so the `operations.py:234`/`:249` anti-pattern cannot reappear in new code.

## 8. Risks and kill criteria

The canonical kill-criteria list is Plan 1 §15; the load-bearing ones for this program. Thresholds are fixed here so they cannot be moved post-hoc; Phase 0/1 may tighten them but not relax them.

- **MMA ≤ 0 on held-out** → the central bet fails; report it, do not game the exam. **"Honest effort" stopping rule:** failure is declared only after a bounded, pre-registered tuning budget (max 5 scorer-tuning iterations on the *dev* split, evaluated once on the held-out split), so "keep tuning until it passes" is not an option and neither is "give up at the first negative number."
- **Causal ≈ similarity** → the action-value scorer must beat plain word-overlap retrieval by a **pre-registered MMA margin of ≥ 5 percentage points** of task success on held-out tasks; below that margin the read-path thesis is unproven (mirrors Plan 1 §15's "within 5–10 percent" band).
- **False memories pass** → if any negative control is promoted to `verified`, the write-path guarantee is void (target negative-control suppression = 100%; any leak trips this).
- **No transfer** → verified experience that does not generalize to held-out tasks is not "experience" (generalization gap measured explicitly in §4.3 secondary metrics).
- **Cost/latency exceeds benefit** → a brief whose cost/latency exceeds the per-brief budget set in §10.5 while its measured lift does not clear that budget is net-negative.

## 9. Relationship to the Correction Capture Controller (separate track)

While unblocking this work, the project's own Correction Capture Controller surfaced two issues that are the *same discipline* as this program's acceptance gates: the startup self-DoS coupling (a single correction hard-fails all startup; see `docs/2026-05-28-correction-capture-controller-opus-review.md` P2-3) and fake-green monitor checks (P0-5). These are **not** folded into this program; they are flagged here so the acceptance gates above explicitly forbid repeating the fake-green pattern, and the controller fixes remain tracked in `TODO.md` and the review doc.

## 10. Open design decisions (to resolve in plan mode, with recommendations)

These are decisions for the Phase 0/1 implementation plans, each with a recommended default so none is a blank placeholder:

1. **Proving-ground environment.** Reuse/extend the existing seeded synthetic environment vs. adopt an external harness (e.g., WebArena-style). *Recommendation:* extend the existing seeded environment for Phase 0 (fastest path to a real MMA number), add external benchmarks in Phase 4.
2. **Causal scorer form.** Transparent feature ranker vs. learned model. *Recommendation:* feature ranker first (auditable, no training data needed); revisit learned scoring only if the ranker plateaus below the similarity baseline.
3. **Held-out task source.** Hand-authored held-out set vs. split from benchmark datasets. *Recommendation:* start with a hand-authored held-out set in the seeded env for Phase 0/1; use benchmark splits in Phase 4.
4. **Verification-probe cost.** Full replay vs. cached lightweight probe. *Recommendation:* lightweight cached probe for promotion gating, full replay only at phase gates.
5. **MMA latency/cost budget.** *Recommendation:* set an explicit per-brief budget in Phase 1 and treat budget breach as a kill-criterion input.

## 11. Definition of "program complete"

The full program is complete when: components 4–7 are wired with real consumers (grep-proven); a CEM-equipped agent shows **MMA > 0 on held-out tasks against the honest baseline ladder**, reported with the no-memory control; negative controls are suppressed; the falsification suite is green; no kill criterion trips; and `pytest` + synthetic eval + the exam all pass with recorded evidence. If MMA cannot be made > 0 honestly, the program reports that result as its finding.
