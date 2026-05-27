# Plan 1: Causal Experience Memory Foundation

Date: 2026-05-27

Status: Provisional foundation lock

Inputs:
- `research/GPT Pro - Brutal verdict.md`
- `research/New reports/Report 1  Frontier Memory Research Map — Agentic Memory for Open-Source AI Systems.md`
- `research/New reports/Report 2  Benchmark and Evaluation Landscape for LLM and Agent Memory.md`
- `research/New reports/Report 3 - Agent Memory System Archaeology.md`
- `research/New reports/Report 4  Unsolved Bottlenecks And Dead Ends in Agentic Memory.md`
- `research/New reports/Report 5  Opportunity Thesis For A Disruptive V1.md`
- MIT-12 corpus lens: decision-making under uncertainty, reinforcement learning, ML systems lineage, and multi-agent coordination
- Web spot checks against primary/current sources: HaluMem, MemoryArena, LongMemEval-V2, Agent Workflow Memory, MemoryAgentBench, STALE, Useful Memories Become Faulty

## 1. Decision

The project should pivot from "agent memory database / MCP memory twin / universal onboarding" to:

> Causal Experience Memory: a memory compiler/runtime that turns raw agent trajectories into verified, evidence-backed, temporally scoped, action-relevant experience that measurably improves future behavior.

This is the right high-risk foundation.

The first implementation wedge should be:

> CEM-0 / MemGuard Kernel: a write-path quality and validity layer that prevents false, stale, unsupported, or contradictory memories from becoming trusted operational experience.

Short version:

- Causal Experience Memory is the research thesis.
- MemGuard is the first attack surface.
- Experience Atoms and Experience Cards are the primitive.
- Marginal Memory Advantage is the score.
- HaluMem, MemoryArena, LongMemEval-V2, and a custom falsification suite are the exam.

This preserves the ambition of Pro's answer while grounding the first build in the strongest evidence from the new reports.

## 2. Brutal Verdict

The commodity lane is dead for us.

Do not build:
- another memory MCP server as the main product;
- another vector store wrapper;
- another temporal graph UI;
- another chat summary store;
- another "universal memory API";
- another framework integration layer.

Those may become distribution paths later. They are not the invention.

The invention is the transformation:

```text
raw trajectory -> typed evidence -> candidate memory -> verified experience -> future action advantage
```

The high-risk claim is:

> An agent can learn operational experience from its own traces without fine-tuning, and that learned experience can be verified, audited, scoped, and shown to change future task success.

That is the line worth taking risk on.

## 3. Source Facts

SOURCE FACT: HaluMem introduces an operation-level benchmark for memory hallucinations, splitting evaluation into memory extraction, memory updating, and memory QA. It reports that hallucinations accumulate in extraction and updating, then propagate into QA. Source: https://arxiv.org/abs/2511.03506

SOURCE FACT: MemoryArena evaluates memory inside multi-session Memory-Agent-Environment loops where later subtasks depend on earlier actions and feedback. Its abstract states that agents with near-saturated performance on LoCoMo perform poorly in the agentic setting. Source: https://arxiv.org/abs/2602.16313

SOURCE FACT: LongMemEval-V2 evaluates whether memory systems help agents become "knowledgeable colleagues" in specialized web environments, with 451 curated questions over abilities such as static state recall, dynamic state tracking, workflow knowledge, environment gotchas, and premise awareness. Source: https://arxiv.org/abs/2605.12493

SOURCE FACT: Agent Workflow Memory extracts reusable workflows from web-agent trajectories and reports 24.6 percent and 51.1 percent relative success-rate improvements on Mind2Web and WebArena. Source: https://arxiv.org/abs/2409.07429

SOURCE FACT: MemoryAgentBench frames memory-agent evaluation around accurate retrieval, test-time learning, long-range understanding, and selective forgetting, and argues current methods do not master all dimensions together. Source: https://arxiv.org/abs/2507.05257

SOURCE FACT: STALE targets the failure mode where later evidence invalidates earlier memories without explicit negation, meaning static recall benchmarks miss a major part of memory revision. Source: https://arxiv.org/abs/2605.06527

SOURCE FACT: Useful Memories Become Faulty argues that continuously updating textual memory banks can make useful memories faulty, and that raw episodic traces can remain competitive with consolidated memories. Source: https://arxiv.org/abs/2605.12978

SOURCE FACT: Report 4 ranks Wrong Memory, Evaluation Weakness, and Context Pollution / Memory Laundering as the top three bottlenecks. It translates this into requirements: write-path extraction verification, provenance metadata, temporal validity, contradiction links, uncertainty-gated retrieval, and observability.

SOURCE FACT: Report 5 recommends MemGuard: a write-path quality protocol that validates memory extractions before storage, detects contradictions, assigns TTLs/confidence/provenance, quarantines uncertain writes, and ships with a HaluMem-compatible evaluation harness.

SOURCE FACT: Report 1 recommends a Causal Memory Engine that optimizes for task outcome improvement rather than semantic similarity. Report 2 says a credible benchmark must test memory-action coupling, temporal contradiction, provenance/explainability, harm, cost, and resistance to context stuffing. Report 3 shows top systems converge on vector/graph/hybrid storage while avoiding transparent answers on selection, correction, provenance, poisoning, and quality measurement.

## 4. Inference

INFERENCE: Pro's Causal Experience Memory thesis and Report 5's MemGuard recommendation are not competing directions. They are two layers of the same program.

INFERENCE: Causal Experience Memory is too big to build directly as a platform. The right first wedge is the write path because every downstream failure becomes unrecoverable once false or stale experience is promoted into trusted memory.

INFERENCE: The first public proof does not need universal onboarding. It needs one hard, reproducible demonstration where verified experience beats raw RAG, summaries, graph retrieval, and unverified reflection on held-out tasks.

INFERENCE: "Causal" should be treated as the research direction, not as a loose marketing word. The v0 system can start with evidence-backed action priors and counterfactual ablations, then earn stronger causal claims through evaluation.

INFERENCE: The raw trace ledger must remain first-class. The 2026 evidence around faulty continuous consolidation and HaluMem-style write failures makes "summaries as truth" a trap.

## 5. Judgment

JUDGMENT: Lock Plan 1 around Causal Experience Memory.

JUDGMENT: Build CEM-0 as a MemGuard Kernel rather than a full memory platform.

JUDGMENT: The first valuable primitive is not `memory_save`. It is `propose_memory -> validate -> quarantine/promote -> retrieve_action_brief -> log_action_influence`.

JUDGMENT: The first benchmark claim should be narrow and brutal:

> CEM-0 reduces write-path hallucination and contradiction propagation versus a vanilla memory store, and its verified memories produce measurable marginal memory advantage on held-out workflow tasks.

JUDGMENT: The older A/B/C/D plan becomes infrastructure, not foundation.

- A: historical research context only.
- B: SC schema upgrade can inform provenance, identity, temporal validity, and visibility.
- C: Codex memory MCP twin is useful later as a backend adapter.
- D: ACS protocol is useful later for multi-agent coordination.

None of A/B/C/D is the core invention anymore.

## 6. MIT-12 Theory Lens

SOURCE FACT: MIT-12 decision-making material models uncertain environments through POMDP-style belief updates. Beliefs are updated from prior belief, action, transition dynamics, and observation likelihood. Relevant chunks: `book-04-chunk-0096`, `book-04-chunk-0097`.

INFERENCE: Agent memory should be treated as an approximate belief state, not as a scrapbook. A memory write is a belief update. It should preserve uncertainty, evidence, source role, and time validity.

SOURCE FACT: MIT-12 reinforcement learning material frames policy value and state-action value as expected return, and shows policy improvement depends on better expected action values, not on similarity of descriptions. Relevant chunk: `book-01-chunk-0101`.

INFERENCE: Memory retrieval should be scored by action-value improvement. Semantic similarity is only a candidate generator; it is not the objective.

SOURCE FACT: MIT-12 material distinguishes off-policy and on-policy learning, and notes that off-policy methods evaluate or improve one policy while acting under another. Relevant chunk: `book-01-chunk-0105`.

INFERENCE: Learning memory usefulness from historical traces is an off-policy evaluation problem. We cannot assume a retrieved memory caused success just because it appeared in a successful trace. We need ablations, replay, negative controls, and held-out tasks.

SOURCE FACT: MIT-12 ML systems material emphasizes data transformation lineage, versioning, modular pipeline stages, monitoring, and hidden technical debt in evolving ML systems. Relevant chunks: `book-03-chunk-0135`, `book-03-chunk-0392`.

INFERENCE: Memory extraction is a data transformation pipeline. It needs lineage, versioning, regression tests, and observability just like training data and model artifacts.

JUDGMENT: The theory lens strengthens the risky plan rather than weakening it. It says the project should be more rigorous about belief state, action value, off-policy evaluation, and lineage. It does not say "be safe." It says "make the bold claim experimentally sharp."

## 7. Core Primitive

The product primitive is an Experience Atom.

```text
ExperienceAtom
- id
- source_trace_ids
- source_spans
- source_artifacts
- source_agent_id
- source_session_id
- extracted_by_model
- extraction_prompt_version
- epistemic_type:
  observation | user_claim | tool_output | assistant_hypothesis |
  derived_claim | preference | instruction | skill | failure_mode |
  contradiction | invalidation_event
- domain_scope
- task_family
- temporal_scope:
  observed_at | valid_from | valid_until | superseded_by | last_confirmed_at
- state_preconditions
- action_or_strategy
- observed_outcome
- causal_hypothesis
- confidence_score
- support_count
- contradiction_links
- exception_boundary
- retrieval_cues
- recommended_use
- verification_probe_ids
- promotion_status:
  proposed | candidate | verified | deprecated | quarantined
- quarantine_reason
- retrieval_count
- last_retrieved_at
- last_action_influence_id
```

The developer-facing primitive is an Experience Card.

```text
ExperienceCard
- title
- use_when
- do
- do_not
- check_first
- evidence
- confidence
- known_exceptions
- temporal_validity
- tested_by
- last_validated_at
- action_brief_template
```

The runtime output is not a pile of memories. It is an Action Brief.

```text
ActionBrief
- applicable_experience_cards
- why_applicable
- preconditions_to_check
- recommended_next_actions
- risks_and_failure_modes
- stale_or_contested_memories_to_ignore
- evidence_links
- confidence
- expected_action_delta
```

## 8. CEM-0 / MemGuard Kernel

CEM-0 should be a small, sharp library and eval harness.

It should provide:

```python
class CEM:
    def ingest_trace(self, trace: AgentTrace) -> TraceReceipt: ...
    def propose_memories(self, trace_id: str) -> list[ExperienceAtom]: ...
    def validate(self, atom_id: str) -> ValidationResult: ...
    def promote(self, atom_id: str) -> ExperienceCard | None: ...
    def retrieve_action_brief(self, task: TaskContext) -> ActionBrief: ...
    def audit(self, memory_id: str) -> MemoryAudit: ...
    def run_eval(self, suite: str) -> EvalResult: ...
```

Under the hood, it must implement:

1. Raw Trace Ledger
   - Append-only evidence: turns, observations, actions, tool calls, DOM/screenshot references, errors, rewards, and outcomes.
   - This layer is never treated as truth by itself.

2. Typed Memory Compiler
   - Converts traces into typed atoms with source spans and epistemic roles.
   - Must separate observation, user claim, tool output, assistant hypothesis, derived claim, preference, instruction, skill, failure mode, and invalidation event.

3. Write-Path Validator
   - Checks whether the atom is grounded in the source trace.
   - Checks whether the atom contradicts active memory.
   - Assigns confidence and temporal validity.
   - Quarantines low-confidence or unsupported memory.

4. Experience Consolidator
   - Groups repeated patterns, success/failure contrasts, gotchas, and workflow preconditions.
   - Produces Experience Cards only when enough evidence or a strong contrast exists.

5. Verification and Promotion
   - Uses probes, replays, held-out tasks, negative controls, and contradiction injection.
   - Promotion is earned, not assumed.

6. Action-Time Adapter
   - Produces Action Briefs, not raw memory dumps.
   - Logs whether a retrieved memory influenced the decisive action.

7. Evaluation Harness
   - Runs HaluMem, MemoryArena/LME-V2 style tasks, and custom contradiction/poison/stale suites.

## 9. First Demo

The public demo should be narrow and dramatic.

Build a small specialized web/workflow environment with seeded gotchas:

1. A form silently rejects submission unless field X is set before field Y.
2. A user preference changes mid-history and the old preference becomes operationally invalid.
3. A failed trace contains the critical negative lesson.
4. A successful trace contains misleading irrelevant actions.
5. A poisoned/stale memory is injected.

Run:

- no memory agent;
- full-context baseline;
- vector RAG over raw traces;
- rolling summary memory;
- unverified reflection memory;
- CEM-0 verified experience memory.

The demo should show:

1. The agent fails repeatedly.
2. CEM ingests failures and successes.
3. CEM proposes atoms, quarantines bad candidates, and promotes an Experience Card.
4. On a held-out workflow task, the Action Brief causes a different decisive action.
5. RAG retrieves related traces but misses the causal precondition.
6. The stale/poisoned memory is not promoted or is suppressed at retrieval.

This is the story:

> The agent did not just remember. It became more experienced.

## 10. Benchmark Strategy

Primary metric:

```text
Marginal Memory Advantage = TaskSuccess(memory_agent) - TaskSuccess(no_memory_agent)
```

But MMA alone is not enough. Track:

- extraction precision, recall, and F1;
- false memory resistance;
- update recall;
- contradiction detection precision/recall;
- stale-memory suppression rate;
- quarantine false-positive rate;
- evidence support rate;
- action influence rate;
- memory harm rate;
- cost per write;
- p95 write latency;
- p95 retrieval latency;
- token cost per task;
- generalization gap between near-duplicate and held-out tasks.

Required baselines:

- no memory;
- full context;
- summary memory;
- vector RAG;
- time-aware vector RAG;
- temporal graph memory if available;
- unverified reflection;
- human-curated runbook as upper bound.

External benchmark targets:

- HaluMem for extraction/update/QA hallucination;
- MemoryArena for memory-action coupling;
- LongMemEval-V2 for environment-specific web-agent experience;
- MemoryAgentBench for retrieval, test-time learning, long-range understanding, selective forgetting;
- STALE-style invalidation tests for stale memory and implicit conflict;
- AWM/WebArena-style workflow reuse for procedural experience.

Custom falsification suite:

1. same semantic query, different causal rule;
2. same UI labels, different required order;
3. stale preference vs current preference;
4. assistant speculation vs tool-observed fact;
5. successful trace with misleading irrelevant action;
6. failed trace with crucial negative lesson;
7. multi-agent contamination;
8. poisoned memory injection;
9. memory whose preconditions do not apply;
10. historically true fact that is operationally invalid now.

## 11. Thirty-Day Attack

Week 1: Kernel and Trace Ledger
- Define `AgentTrace`, `ExperienceAtom`, `ExperienceCard`, `ValidationResult`, `ActionBrief`.
- Build SQLite + JSONL append-only trace ledger.
- Implement a minimal extractor with structured output.
- Store all source spans and extraction metadata.
- Add a synthetic 200-turn memory corruption fixture.

Week 2: Write-Path Quality
- Implement grounding check against source spans.
- Implement contradiction detection against active atoms.
- Implement temporal validity and TTL policy.
- Implement quarantine.
- Implement `audit(memory_id)` with provenance and validation history.

Week 3: Eval Harness
- Build HaluMem adapter or HaluMem-like subset runner if dataset access slows us down.
- Build synthetic contradiction and stale-memory suite.
- Implement baselines: raw vector, summary, unvalidated extraction, CEM-0.
- Produce first metrics: false memory resistance, update recall, contradiction detection, latency.

Week 4: Experience Card Demo
- Add simple web/workflow environment with seeded gotchas.
- Generate failed/success traces.
- Compile Experience Cards.
- Retrieve Action Briefs.
- Run held-out tasks against baselines.
- Publish a reproducible report and README.

Thirty-day success target:

```text
CEM-0 beats unvalidated memory by >=10 absolute points on extraction/update integrity
AND shows a positive held-out task-success delta on the workflow demo
AND produces full provenance for every memory-derived recommendation.
```

## 12. Ninety-Day Research Program

Month 1:
- CEM-0 kernel, HaluMem-style eval, synthetic corruption suite, first demo.

Month 2:
- LongMemEval-V2 / MemoryArena integration.
- Action influence logging.
- Experience Card consolidation from repeated traces.
- Ablation study: raw RAG vs unverified cards vs verified cards.

Month 3:
- Public benchmark report.
- Memory harm gallery.
- Backend adapters: flat file, SQLite, optional Qdrant/pgvector.
- One framework adapter only after primitive proof.
- Publish "From Recall to Experience" essay/spec.

## 13. What Happens To A/B/C/D

The previous plan is not thrown away. It is demoted.

A: SC memory deep review
- Keep as local background and evidence that storage-level memory is not enough.

B: SC v0.3 schema upgrade
- Reuse ideas: `agent_id`, `visibility`, temporal validity, identity, and auth.
- Do not make it the product center.

C: Codex memory MCP twin
- Later backend adapter or developer convenience layer.
- Do not build this before CEM-0 proof.

D: ACS protocol
- Later multi-agent communication layer.
- Useful after we have a memory primitive worth sharing.

The new dependency order:

```text
Plan 1 foundation -> CEM-0 proof -> backend adapters -> MCP integration -> multi-agent protocol
```

Not:

```text
MCP twin -> storage schema -> multi-agent plumbing -> hope memory gets smart later
```

## 14. Public Narrative

One-liner:

> Causal Experience Memory turns agent traces into verified operational experience that improves future action.

Sharper launch line:

> Your agent's memory is wrong before retrieval. CEM validates experience before it becomes behavior.

Research blog title:

> From Recall to Experience: A Causal Memory Runtime for Long-Horizon Agents

README positioning:

```text
CEM-0 is a write-path quality and experience compiler for AI agent memory.

It does not replace your vector DB, graph DB, MCP server, or agent framework.
It sits above them and asks the harder question:

Should this memory be trusted enough to change a future action?

CEM-0 stores raw traces as evidence, extracts typed Experience Atoms, validates
grounding and contradiction, promotes verified Experience Cards, and returns
Action Briefs with evidence, preconditions, and known failure modes.
```

## 15. Kill Criteria

Kill or pivot if:

1. Hybrid RAG over raw traces matches CEM-0 within 5-10 percent on held-out tasks at comparable cost.
2. Verified Experience Cards do not beat unverified reflections.
3. Write-path validation improves extraction metrics but does not improve action outcomes.
4. False quarantine is so high that useful memory is suppressed.
5. The system requires humans to author the useful memories.
6. The demo works only on near-duplicate tasks.
7. Latency or token cost makes the system impractical.
8. The invention disappears when swapping storage backends.
9. The project becomes mostly adapters, dashboards, and MCP glue.
10. After eight weeks, there is no clear primitive stronger than "structured memory with metadata."

## 16. Open Questions

OPEN QUESTION: Can we get HaluMem, MemoryArena, and LongMemEval-V2 data/runners quickly enough to run real baselines in the first month?

OPEN QUESTION: What is the smallest web/workflow environment that convincingly demonstrates experience acquisition without looking toy?

OPEN QUESTION: Should the first public name be `CEM`, `MemGuard`, or a combined name like `cem-guard`? Current judgment: public thesis should be CEM; first package can be `memguard` or `cem-kernel`.

OPEN QUESTION: How much of contradiction detection can be non-LLM, using NLI, schema rules, temporal logic, and source spans?

OPEN QUESTION: Can action influence be measured automatically, or do we need replay/ablation instrumentation around the agent loop?

OPEN QUESTION: Does "causal retrieval scorer" come in V1, or after write-path quality proves usefulness? Current judgment: after V1. Write-path integrity is the first wedge.

## 17. Immediate Next Steps

1. Clean the GPT Pro verdict encoding and preserve the raw original separately if needed.
2. Commit the five reports, Pro verdict, and this synthesis as the research foundation.
3. Create `specs/2026-05-27-cem-0-spec.md`.
4. Create a tiny runnable repo skeleton:
   - `packages/cem-core`
   - `packages/cem-eval`
   - `examples/workflow-gotchas`
5. Build the synthetic corruption fixture first.
6. Run baseline vs CEM-0 on the fixture before touching broad integrations.

## 18. Bottom Line

The right project is not a memory database.

It is not even "universal agent memory."

The right project is a research-grade runtime for turning experience into future competence.

The first risky, meaningful bet:

> Prevent bad memories from becoming trusted experience, then prove that verified experience changes what agents do.

That is the foundation.
