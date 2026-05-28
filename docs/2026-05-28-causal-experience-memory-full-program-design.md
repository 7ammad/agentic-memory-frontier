# CEM-1 Full Kernel Build

- Date: 2026-05-28
- Status: draft under review (committed; iterating on GPT Pro feedback, rounds 1 + 2 folded in)
- Decision: build the **full CEM-1 kernel** end-to-end via **Approach C (eval-first)**, with proof embedded in the architecture from day one — not a proof MVP, not a platform.
- Extends (does not supersede): `research/2026-05-27-plan-1-causal-experience-memory-foundation.md`
- Source context: `research/GPT Pro - Brutal verdict.md`, Reports 4–5, `specs/2026-05-27-cem-0-memguard-kernel-spec.md`, and GPT Pro review — round 1 (`docs/GPT Pro 1st feedback.md`, technical fixes) + round 2 (`docs/GPT revised feedback.md`, authoritative for framing + sequencing)
- Packaging target: `memguard` (a complete local kernel + proving ground, not a hosted platform)

---

## 1. Problem and thesis

The locked thesis is a two-clause bet (Plan 1 §18):

> **Prevent bad memories from becoming trusted experience — then prove that verified experience changes what agents do.**

- **Clause 1 — the write-path (MemGuard).** Built. Ingest trace → extract typed Experience Atoms → validate (grounding + contradiction) → quarantine/promote Experience Cards.
- **Clause 2 — the causal read-path + proof.** Not built. Retrieve by *action value*, return an Action Brief carrying an *expected action delta*, and prove via Marginal Memory Advantage (MMA) that a memory-equipped agent beats a no-memory agent on held-out tasks.

Clause 2 is the field's documented #1 dead end ("memory does not reliably improve future task success") and #3 dead end ("similarity retrieval ≠ causal retrieval"), per `GPT Pro - Brutal verdict.md`. It is also the exact thing Plan 1 §16 (line 497) deferred "after V1." **That deferral is the deadlock this program closes.**

**Proof-first is not proof-only.** The earlier framing ("smallest kernel + ruthless eval") risks being read as "build a measurement slice, stub the rest, call it progress." That is rejected. The correct reading: every major component is built end-to-end against an evidence contract. We build the complete causal-memory loop, with proof gates wired into each transition — not a thin proof artifact, and not a broad platform around the idea.

## 2. What we are building: the full CEM-1 kernel

CEM-1 is **a complete, local, end-to-end Causal Experience Memory kernel where every memory-lifecycle transition, retrieval decision, and action-improvement claim is auditable, testable, and measurable.** It is a sharper full project, not a smaller one.

Three strategies were on the table; we pick the third:

1. **Full platform (rejected — premature).** Hosted API, UI, framework integration matrix, graph browser, learned scorer, multi-agent orchestration, enterprise governance. Out of scope.
2. **Proof-only slice (rejected — the underbuild trap).** Eval harness + synthetic MMA, with consolidation/verification/read-path left shallow and "proof claimed later." This creates motion, not a system.
3. **Full CEM-1 vertical kernel (chosen).** The complete core loop, built end-to-end, with proof embedded in every transition.

### Build now (these are the invention)

- **Full memory lifecycle** — real states, not a status flip (§4.2).
- **Full consolidation** — dedup, near-duplicate merge, source-span preservation, grounded abstraction, exception boundaries, supersession, deactivation, contradiction links (§4.4).
- **Full verification + negative controls** — probes, results, runner, negative-control injector, held-out replay, staleness probe, contradiction probe, promotion gate (§4.2).
- **Full action-time adapter** — candidate generation, scope/temporal filtering, precondition matching, contradiction/staleness penalties, verified-lift prior, score breakdown, bounded Action Brief, influence id (§4.1).
- **Full influence ledger** — every brief is a traceable record; outcomes close the loop (§4.5).
- **Full eval harness** — MMA against the honest baseline ladder on held-out tasks (§4.3).
- **Full CLI / operator surface** — makes the kernel usable, inspectable, and hard to fake (§4.6).

### Defer (full-platform features, not the CEM invention)

Hosted API · multi-tenant auth · dashboard UI · graph browser · LangChain/LlamaIndex adapters · enterprise compliance layer · learned scorer · large-scale distributed storage · multi-agent orchestration platform · production SaaS packaging.

These are deferred because they wrap the invention; they are not part of proving it. The following are **not** deferred — they are the invention and ship in CEM-1: verification, consolidation, causal retrieval, influence logging, eval harness, auditability, negative controls, staleness handling, supersession.

## 3. Current state (verified against source, 2026-05-28)

| # | Component (Plan 1 §8) | Status | Evidence |
|---|---|---|---|
| 1 | Raw Trace Ledger (`ingest_trace`) | Built | kernel API present |
| 2 | Typed Memory Compiler (extract Atoms) | Built | extractor + schema; treat as V0 deterministic fixture |
| 3 | Write-Path Validator (grounding + contradiction) | Built | validator; synthetic eval clean |
| 4 | Experience Consolidator (dedup/merge/abstract) | Partial | merges; abstraction not verified vs. source spans; supersession is link-only |
| 5 | Verification & Promotion (probes/replays/held-out/negative controls) | Partial | promotes, but **promotion is asserted, not probe-verified** — `promotion_status` is flipped to `verified` unconditionally (`packages/cem-core/src/cem_core/kernel.py:84`, `:105`); no probe runs |
| 6 | Action-Time Adapter (**causal** retrieval + influence logging) | **Not built** | `score_card` is word-overlap (`packages/cem-core/src/cem_core/kernel.py:231-234`); `expected_action_delta=None` hardcoded (`kernel.py:129`); no influence logged |
| 7 | Evaluation Harness (MMA + falsification) | Partial — local facsimiles exist, no real exam | local adapters + CEM-backed runners exist for HaluMem / MemoryArena-style / LongMemEval-V2-style data with a unified report (`docs/cem-0-external-benchmark-decision.md`), but `halumem_runner.py:54` reuses the synthetic delta (`baseline_action_delta=synthetic.unvalidated_memory.expected_action_delta`) instead of running a real exam |

The write-path (1–3) is the real, tested foundation. The program's weight is on **4, 5, 6, 7**, with the read-path (6) and proof (7) as the center of gravity and verification (5) hardened so "verified" means verified.

**Schema gaps (verified in `packages/cem-core/src/cem_core/models.py`).** `ActionBrief` (line 136) carries only `expected_action_delta: float | None = None` (line 146) — no `brief_id`, `influence_id`, `scorer_version`, `expected_action_delta_source`, or `score_breakdown_by_card`. `ExperienceCard` (line 110) has no `measured_lift`, `measured_lift_ci`, `verification_result_ids`, `deactivated_at`, `deactivated_reason`, or card-level `superseded_by_card_ids`. No `VerificationProbe`, `VerificationResult`, `ActionBriefRecord`, or `ActionInfluenceEvent` model exists. These are added in Phase 0 (§6).

## 4. Target architecture — the full vertical loop

The completed kernel must support this loop end-to-end, with real persisted objects at every step:

```text
 1. ingest real traces            -> [1] raw trace ledger
 2. extract typed atoms           -> [2] typed memory compiler
 3. validate atoms                -> [3] write-path validator (grounding + contradiction)
 4. consolidate into candidates   -> [4] experience consolidator (grounded cards, supersession, contradiction links)
 5. run probes + negative controls-> [5] verification (VerificationProbe -> VerificationResult)
 6. promote only probe-passers    -> [5] promotion gate (verified iff stored lift)
 7. retrieve by action value      -> [6] action-time adapter (not similarity)
 8. return bounded Action Brief    -> [6] brief w/ influence id + score breakdown
 9. close the influence loop       -> [6] ActionInfluenceEvent after outcome observed
10. evaluate MMA vs. baselines     -> [7] harness on held-out tasks
11. report failure honestly        -> [7] kill criteria can mark the program failed
```

The data primitives (Experience Atom, Experience Card, Action Brief) exist (Plan 1 §7, CEM-0 spec); this program completes their *behavior* and adds the missing evidence primitives (§6). Each component below states purpose, current status, and target.

### 4.1 Component 6 — Action-Time Adapter (the causal read-path) [center of gravity]

**Purpose.** Given a task context, return an Action Brief: the few cards whose application is expected to *improve the next action's outcome*, plus an explicit expected action delta (with its source) and the influence id needed to later measure whether reading them changed anything.

**Current.** `retrieve_action_brief` (`kernel.py:110`) ranks cards via `score_card` (`kernel.py:231-234`), counting shared words >3 chars between task string and card text — the weakest similarity proxy. `expected_action_delta` is hardcoded `None` (`kernel.py:129`). No influence is logged.

**Target.** An **action-value retrieval scorer**, built as a transparent feature ranker (every term auditable; learned scoring is deferred, never a black box on day one):

- **Score = f(precondition match, verified-lift prior, recency/temporal validity, contradiction penalty, staleness penalty).** A per-card `score_breakdown` is persisted on the brief so any ranking is explainable.
- **The verified-lift prior is zero-weighted until component 5 produces lift evidence**, then enabled — it never invents a prior.
- **`expected_action_delta` is never invented** and is always tagged with `expected_action_delta_source` (see the three-way delta split in §4.2 / §6). Before probes exist, it is observational/estimated and marked as such — it is **not** re-hardcoded to a placeholder and **not** presented as causal.
- **Bounded output preserved** — the startup-brief caps (directives/cards/evidence/tokens) stay; retrieval stays lazy and scoped.

**Interface (signature unchanged, semantics completed).** `retrieve_action_brief(task, max_cards) -> ActionBrief`, where the brief now carries `brief_id`, `influence_id`, `scorer_version`, `score_breakdown_by_card`, and a source-tagged `expected_action_delta`, and ranking reflects estimated action value rather than word overlap.

### 4.2 Component 5 — Verification & Promotion ("CI/CD for memory")

**Purpose.** A candidate memory becomes *verified* only by passing a verification probe; known-bad memories are caught by negative controls.

**Current.** Promotion is asserted (a status flip at `kernel.py:84`/`:105`), not earned by a probe.

**Target — the real lifecycle.**

```text
proposed atom -> candidate atom -> candidate card -> verification probe scheduled
   -> verification result stored -> verified card -> retrieval eligible
   -> deprecated | superseded | quarantined (if invalidated)
```

- **Hard API rule: `promote()` must never mean `verified`.** It means `create_or_update_candidate_card()`. Only an applied verification result may set `promotion_status="verified"` (a separate `verify_card()` / `apply_verification_result()` path). This is the structural fix for the asserted-promotion bug.
- **Probes:** `VerificationProbe` (a held-out task or replay) runs and writes a `VerificationResult` carrying the measured lift over a no-memory control. The probe runner, negative-control injector, held-out replay probe, staleness probe, and contradiction probe are all built.
- **Negative controls:** injected known-false / stale / contradictory memories must be **quarantined or deprecated, never promoted**. Negative-control suppression rate is a monitored metric (target 100%; any leak trips a kill criterion).
- **Three-way delta split (do not collapse these):**
  - `observed_post_brief_delta` — outcome observed after a brief was read. **Observational, not causal** (no counterfactual).
  - `estimated_action_delta` — the scorer's estimate. Uncertain.
  - `verified_action_lift` — probe/ablation measured causal lift, with CI.
  - **Only `verified_action_lift` may set a card `verified` or count as proof.** A post-brief outcome is never a counterfactual.

### 4.3 Component 7 — Evaluation Harness (the proving ground)

**Purpose.** Make the central bet falsifiable. Synthetic proxies cannot be allowed to masquerade as proof.

**Current.** MMA exists only as hand-authored synthetic fixtures (`packages/cem-eval/src/cem_eval/synthetic_corruption.py`, e.g. `HELD_OUT_DECISIVE_ACTIONS` line 42); local external-benchmark facsimile runners exist but reuse the synthetic delta (`halumem_runner.py:54`).

**Target.**

- **Primary metric:** `MMA = TaskSuccess(memory_agent) − TaskSuccess(no_memory_agent)` on **held-out** tasks.
- **Baseline ladder (§7), all run honestly:** CEM must beat the *honest* baselines, not a strawman.
- **Secondary metrics:** extraction P/R/F1, false-memory resistance, update recall, contradiction P/R, stale-memory suppression, quarantine FP rate, evidence support rate, action-influence rate, memory-harm rate, cost/latency, generalization gap.
- **Environments:** (a) the seeded web/workflow environment with planted gotchas (Plan 1 §9); (b) external benchmarks **actually run**, claim-specific — HaluMem (write integrity, arXiv:2511.03506, github.com/MemTensor/HaluMem), MemoryArena (primary external MMA / multi-agent conflict, arXiv:2602.16313, memoryarena.github.io), LongMemEval-V2 (environment experience / long horizon, arXiv:2605.12493, xiaowu0162.github.io/longmemeval-v2), AgingBench (staleness, arXiv:2605.26302 — realizes Plan 1 §10's "STALE-style invalidation" slot with a concrete published benchmark).
- **Honesty gates wired in:** the 10-item falsification suite (Plan 1 §10) and the kill criteria (§9) run as part of the harness and can mark the program failed.

### 4.4 Component 4 — Experience Consolidator

**Purpose.** Turn validated atoms into durable, deduplicated, abstracted cards without inventing claims.

**Current.** Merges exist; abstraction is not checked against source spans; supersession is link-only.

**Target (full, not shallow).** dedup → near-duplicate merge → **source-span preservation** → **grounded abstraction** (every generalized claim traces to its `source_spans`; defends dead end #2) → exception boundaries → **temporal supersession** (a contradicting newer atom sets `superseded_by`, sets `deactivated_at`/`deactivated_reason`, and removes the stale card from retrieval — not merely a link) → contradiction links (so §4.1's contradiction penalty has real input).

**Ordering constraint (rounds 1–2).** Verification depends on *what object* is verified. If consolidation rewrites a card after verification, the result is semantically unstable. So the order is **minimum grounded consolidation → verification → read-path → deeper abstraction**, not read-path → verification → consolidation-later. This is reflected in the Phase plan (§8): consolidation and verification land together in Phase 2, *before* the action-value read-path in Phase 3.

### 4.5 Component 6′ — Influence ledger

Every Action Brief creates a traceable record and, after the outcome is observed, a closing event:

```text
ActionBriefRecord:   brief_id, task_id, candidate_card_ids, selected_card_ids,
                     score_breakdown, scorer_version, expected_action_delta_source, influence_id
ActionInfluenceEvent: influence_id, action_taken, outcome, observed_post_brief_delta,
                     counterfactual_method, baseline_comparison
```

Without this, the kernel cannot learn from its own memory use, and component 7 has no off-policy signal to consume. `observed_post_brief_delta` is observational (§4.2) — it informs, but never promotes.

### 4.6 Operator surface (CLI)

Because this is a local kernel (not a hosted platform), the operator surface is load-bearing: it makes the system usable and **hard to fake**. Target commands (extending the existing `ams.py` surface):

```text
cem ingest   cem propose   cem validate   cem consolidate   cem verify
cem brief    cem close-influence   cem eval   cem audit   cem inspect-card
cem inject-negative-control
```

Each maps to a real kernel operation with persisted state and is exercised by tests.

### 4.7 Components 1–3 (built) — invariants to preserve

Ingest, extraction, and write-path validation stay as-is. The program must not regress their tested behavior (synthetic false-memory resistance, contradiction recall). The deterministic extractor/contradiction detector remain V0 fixtures, not the final reasoning layer (per existing AMS directives).

## 5. The build contract (anti-scaffolding)

This contract is load-bearing and derives from this project's own recorded failures (the "skeleton scope" and "fake-green monitor" corrections, `docs/PROJECT-LEDGER.md` LEDGER-CORRECTION-20260528 entries) and Hammad's standing rule against ghost coding.

> **No phase is allowed to land as isolated scaffolding. Every phase must move the full vertical loop closer to completion. Every component must have a real caller, real persisted state, real tests, and a failure canary.**

- **Real caller** — grep-proof of a consumer wired end-to-end (a barrel export does not count).
- **Real persisted state** — the component reads/writes actual stored objects, not in-memory throwaways.
- **Real tests** — behavior is asserted, not existence.
- **Failure canary** — every gate ships with a test that **injects a known-bad condition and asserts the gate fails**. This is stronger than scanning for a literal `True`: a gate that cannot fail is not a gate.

Codex's likely failure mode (round 2): reading "eval-first" as "build the measurement slice, then mark scaffolds done." The contract forbids that mechanically — a phase is not done until its slice of the vertical loop runs on real objects with a canary that proves the gate bites.

## 6. Schema & evidence model (Phase 0 deliverable)

New/extended Pydantic models (storage is SQLite JSON-blob `payload TEXT`, so adding defaulted fields is cheap; new query-heavy primitives get their own tables):

- **`ActionBrief` (+fields):** `brief_id`, `influence_id`, `scorer_version`, `expected_action_delta_source ∈ {none, observational_unverified, probe_verified, heldout_eval}`, `score_breakdown_by_card`.
- **`ExperienceCard` (+fields):** `measured_lift`, `measured_lift_ci`, `verification_result_ids`, `deactivated_at`, `deactivated_reason`, `superseded_by_card_ids`.
- **`VerificationProbe` (new):** probe id, kind (held-out replay | staleness | contradiction | negative-control), target card/atom, control definition, threshold.
- **`VerificationResult` (new):** result id, probe id, measured lift, CI, pass/fail, stored evidence pointer, timestamp.
- **`ActionBriefRecord` (new)** and **`ActionInfluenceEvent` (new):** §4.5.

**Lifecycle rules, eval protocol, no-fake-green gates, and a storage migration plan** are locked in Phase 0 alongside the schema, so later phases build against a fixed contract.

## 7. Baseline ladder (operational definitions)

All baselines run honestly on the same held-out tasks; CEM must beat the honest ones.

- **no-memory** — agent with no memory access. The MMA denominator/control.
- **full-context** — all allowed prior trace material within the same token/cost budget policy (no retrieval selectivity).
- **lexical overlap** — current `score_card` word-overlap retrieval. CEM must beat this by a pre-registered margin (§9) or the causal-retrieval thesis is unproven.
- **summary** — rolling summary of prior traces injected as context.
- **vector RAG** — embedding similarity retrieval over the trace/card corpus.
- **time-aware RAG** — vector RAG with recency weighting / temporal filtering.
- **temporal graph** — graph retrieval over entity/event/time links, with no causal scorer.
- **unverified reflection** — self-generated lessons with no verification gate (isolates whether *verification* — not just reflection — is what helps).
- **CEM** — the full kernel.
- **human runbook** — a hand-written ideal playbook. This is a **ceiling / upper-bound reference, NOT a must-beat baseline.** Beating it is not required; it bounds how much headroom exists. (Round 1 leakage control — do not turn the ceiling into a pass/fail gate.)

## 8. Sequencing — Phase 0–5 (round 2, authoritative)

Each phase is independently testable, advances the full vertical loop (never lands as scaffolding, §5), and becomes its own implementation plan (`writing-plans`). **Phase 0 is the first slice taken to plan mode.**

- **Phase 0 — Contract lock.** Schemas (§6), lifecycle rules, eval protocol, no-fake-green gates, storage migration plan. No capability change ships; this fixes the contract every later phase builds against.
- **Phase 1 — Full vertical skeleton, no stubs allowed.** `ingest → atom → validate → candidate card → brief → influence record → eval run`. Every step persists real objects; nothing fake is marked `verified`; the brief carries a source-tagged (observational/estimated) delta, never a placeholder. Outcome: the loop executes end-to-end on real objects with a minimal eval run.
- **Phase 2 — Grounded consolidation + verification.** Dedup, source-span support, grounded abstraction (minimum viable), probes, negative controls, the verified lifecycle and promotion gate. Consolidation and verification land **together and before the read-path** (§4.4 ordering constraint). Outcome: `verified` cards carry stored measured lift; negative controls are suppressed.
- **Phase 3 — Action-value retrieval.** The feature scorer with score breakdown, temporal/staleness/contradiction penalties, and the verified-lift prior. `expected_action_delta` is now sourced only from verified evidence where available. Outcome: retrieval ranks by action value, not similarity.
- **Phase 4 — MMA + baseline ladder.** Run CEM vs. the full honest ladder (§7) on held-out tasks. Outcome: the **first real MMA number** with its baseline ladder and CI.
- **Phase 5 — Hardening.** External benchmark runners (replace `halumem_runner.py:54` synthetic-delta reuse with a real exam), better probes, deeper abstraction, cost/latency budgets, stronger audit tools.

**Phase gate (every phase):** MMA does not regress (measured with fixed seeds, or outside a pre-registered noise band when stochastic, so normal variance neither trips nor masks the gate), the falsification suite stays green, no kill criterion trips, every new gate has a passing failure-canary, and full `pytest` + synthetic eval pass. A phase is not "done" until its gate is met with executed evidence.

## 9. Risks and kill criteria

Canonical list is Plan 1 §15; the load-bearing ones for this program, with thresholds fixed here so they cannot move post-hoc (Phase 0/1 may tighten, never relax):

- **MMA ≤ 0 on held-out** → the central bet fails; report it, do not game the exam. **"Honest effort" stopping rule:** failure is declared only after a bounded, pre-registered tuning budget (max 5 scorer-tuning iterations on the *dev* split, evaluated **once** on the held-out split per locked candidate), so neither "tune until it passes" nor "give up at the first negative number" is allowed. If held-out n is small, a positive result is reported as **directional** (with CI) rather than overclaimed.
- **Causal ≈ similarity** → the action-value scorer must beat lexical-overlap retrieval by a **pre-registered MMA margin of ≥ 5 percentage points** of held-out task success; below that, the read-path thesis is unproven.
- **False memories pass** → if any negative control is promoted to `verified`, the write-path guarantee is void (suppression target 100%; any leak trips this).
- **No transfer** → verified experience that does not generalize to held-out tasks is not "experience" (generalization gap measured explicitly, §4.3).
- **Cost/latency exceeds benefit** → a brief whose cost/latency exceeds the per-brief budget (set in Phase 3, §10.5) while its measured lift does not clear that budget is net-negative.

## 10. Testing, leakage controls, and failure canaries

- **Unit + integration:** `python -m pytest` (full suite) stays green every phase.
- **Synthetic eval:** `python scripts/run_synthetic_eval.py` (false-memory resistance, contradiction P/R, action-brief pollution) stays clean.
- **Exam:** the Phase 4 MMA harness runs CEM vs. baseline ladder on held-out tasks; numbers recorded in `CHANGELOG.md` + `docs/PROJECT-LEDGER.md`.
- **Negative controls:** injected false/stale/contradictory memories must be suppressed; suppression rate is asserted in tests.
- **Ablations:** memory-on vs. memory-off vs. unverified-reflection, to isolate the causal contribution.
- **Leakage controls (round 1):**
  - Memory-source traces and held-out task answers are **disjoint** — the corpus that feeds memory may not contain held-out answers. Held-out tasks may share environment rules/patterns, but never exact task statements or answer artifacts.
  - All tuning happens on a **dev split**; the **held-out split is evaluated once per locked candidate** (mirrors §9's stopping rule).
  - The **human runbook is a ceiling, not a must-beat baseline** (§7).
- **Failure canaries (the §5 contract, mechanized):** every gate ships a test that injects a known-bad condition and asserts the gate fails. Includes a **no-fake-green guard** — a test that inspects each monitor/health check's evaluated value and fails if it is a hardcoded literal, so the `operations.py:234`/`:249` anti-pattern cannot reappear in new code.

## 11. Acceptance contract — CEM-1 complete

CEM-1 is complete only when the **whole loop** works with real consumers (grep-proven) and recorded evidence:

1. Ingest real traces.
2. Extract typed atoms.
3. Validate atoms against grounding and contradiction checks.
4. Consolidate atoms into grounded candidate cards.
5. Run verification probes and negative controls.
6. Promote **only** probe-passing cards to `verified`.
7. Retrieve cards by action value, not similarity.
8. Return bounded Action Briefs with influence ids.
9. Close the action-influence loop after outcomes.
10. Evaluate MMA against honest baselines on held-out tasks.
11. Report failure honestly if memory does not help.

**Plus the experimental-rigor contract (round 1) — the proof must also satisfy:**

- The exam contract (held-out split + baseline ladder + metrics) is **locked in Phase 0, before any scorer tuning**.
- All baselines run under the **same task set and reporting contract**.
- MMA is reported as a **paired task-level delta** with n, 95% CI, cost, and latency — never a bare mean.
- CEM beats no-memory on held-out, and beats lexical-overlap by **≥ 5pp** task success.
- **No** injected known-false / stale / contradictory / poisoned memory is promoted to `verified`.
- Every `verified` card has a stored `VerificationResult`; every Action Brief has a persisted record and influence id.
- `expected_action_delta` is never populated from unpaired observation without `expected_action_delta_source="observational_unverified"`.
- `pytest` + synthetic eval + the MMA exam pass with **committed machine-readable reports**.
- If MMA ≤ 0 after the pre-registered tuning budget, the program **reports failure rather than changing the exam**.

Plus the standing anti-ghost-coding gates: no stubs reported as done; no fake-green checks; no asserted promotions; every "done" carries executed evidence; MMA is reported with its baseline ladder; the system fails visibly. **If MMA cannot be made > 0 honestly, the program reports that result as its finding** — and that is a valid, publishable outcome, not a reason to trim the exam.

## 12. Relationship to the Correction Capture Controller (separate track)

While unblocking this work, the project's Correction Capture Controller surfaced two issues that are the *same discipline* as this program's acceptance gates: the startup self-DoS coupling (a single correction hard-fails all startup; `docs/2026-05-28-correction-capture-controller-opus-review.md` P2-3) and fake-green monitor checks (`operations.py:234`/`:249`, P0-5). These are **not** folded into CEM-1; they are flagged here so the build contract (§5) and the no-fake-green guard (§10) explicitly forbid repeating the pattern. The controller fixes stay tracked in `TODO.md` and the review doc.

## 13. Open design decisions (resolve in plan mode, with recommendations)

Each has a recommended default so none is a blank placeholder:

1. **Proving-ground environment.** Extend the existing seeded synthetic environment vs. adopt an external harness. *Recommendation:* extend the seeded environment for Phases 1–4 (fastest path to a real MMA number); external benchmarks in Phase 5.
2. **Causal scorer form.** Transparent feature ranker vs. learned model. *Recommendation:* feature ranker first (auditable, no training data); revisit learned scoring only if the ranker plateaus below the similarity baseline.
3. **Held-out task source.** Hand-authored held-out set vs. benchmark splits. *Recommendation:* hand-authored held-out set in the seeded env for Phases 1–4; benchmark splits in Phase 5.
4. **Verification-probe cost.** Full replay vs. cached lightweight probe. *Recommendation:* lightweight cached probe for promotion gating; full replay only at phase gates.
5. **MMA latency/cost budget.** *Recommendation:* set an explicit per-brief budget in Phase 3 and treat budget breach as a kill-criterion input.
