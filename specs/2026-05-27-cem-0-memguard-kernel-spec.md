# CEM-0 / MemGuard Kernel Spec

Date: 2026-05-27

Status: Draft for build kickoff

Parent foundation: `research/2026-05-27-plan-1-causal-experience-memory-foundation.md`

## 1. Mission

Build the smallest serious version of Causal Experience Memory:

> A memory kernel that ingests agent traces, extracts typed candidate memories, validates them before storage, quarantines bad memories, promotes verified experience, and proves downstream action advantage through benchmarks.

The first wedge is write-path quality because false memory becomes downstream behavior. If the write path is untrusted, every retrieval strategy is contaminated.

## 2. Non-Goals

CEM-0 is not:

- a hosted memory API;
- a generic MCP memory server;
- a vector database;
- a graph database;
- a chat history summarizer;
- a dashboard-first product;
- a universal agent framework;
- a multi-agent governance platform;
- a privacy compliance product.

Those are later layers only if the kernel proves value.

## 3. Build Shape

Recommended V0 stack:

- Python core library for research/eval velocity.
- SQLite + JSONL as the first storage backend.
- Pydantic models for strict schemas.
- Optional Chroma/Qdrant/pgvector adapters after baseline proof.
- TypeScript adapter only after the Python kernel has a measurable result.

Reason:

- Memory benchmarks and research prototypes are Python-first.
- The first claim depends on evaluation speed, not app polish.
- Backend-agnostic design keeps the invention above storage.

## 4. Package Layout

```text
packages/
  cem-core/
    pyproject.toml
    src/cem_core/
      __init__.py
      models.py
      trace_ledger.py
      extractor.py
      validator.py
      contradiction.py
      temporal.py
      quarantine.py
      promoter.py
      retriever.py
      audit.py
      metrics.py
  cem-eval/
    pyproject.toml
    src/cem_eval/
      baselines.py
      synthetic_corruption.py
      halumem_runner.py
      workflow_gotchas.py
      memoryarena_adapter.py
      reports.py
examples/
  coding-agent-memory/
  workflow-gotchas/
docs/
  architecture.md
  benchmark-protocol.md
  experience-atom.md
```

## 5. Core Data Models

### AgentTrace

```python
class AgentTrace(BaseModel):
    trace_id: str
    session_id: str
    agent_id: str
    task_id: str | None
    started_at: datetime
    ended_at: datetime | None
    turns: list[TraceTurn]
    final_outcome: Literal["success", "failure", "partial", "unknown"]
    outcome_score: float | None
    environment: dict[str, JsonValue]
```

### TraceTurn

```python
class TraceTurn(BaseModel):
    turn_id: str
    index: int
    timestamp: datetime
    role: Literal["user", "assistant", "tool", "environment", "system"]
    content: str
    tool_name: str | None
    tool_input: dict[str, JsonValue] | None
    tool_output: dict[str, JsonValue] | None
    observation_ref: str | None
    artifact_refs: list[str]
```

### ExperienceAtom

```python
class ExperienceAtom(BaseModel):
    atom_id: str
    source_trace_ids: list[str]
    source_turn_ids: list[str]
    source_spans: list[SourceSpan]
    source_artifacts: list[str]

    source_agent_id: str
    source_session_id: str
    extracted_by_model: str
    extraction_prompt_version: str

    epistemic_type: Literal[
        "observation",
        "user_claim",
        "tool_output",
        "assistant_hypothesis",
        "derived_claim",
        "preference",
        "instruction",
        "skill",
        "failure_mode",
        "contradiction",
        "invalidation_event",
    ]

    content: str
    domain_scope: str | None
    task_family: str | None
    state_preconditions: list[str]
    action_or_strategy: str | None
    observed_outcome: str | None
    causal_hypothesis: str | None

    observed_at: datetime
    valid_from: datetime | None
    valid_until: datetime | None
    superseded_by: list[str]
    last_confirmed_at: datetime | None

    confidence_score: float
    support_count: int
    contradiction_links: list[str]
    exception_boundary: list[str]
    retrieval_cues: list[str]
    recommended_use: str | None
    verification_probe_ids: list[str]

    promotion_status: Literal[
        "proposed",
        "candidate",
        "verified",
        "deprecated",
        "quarantined",
    ]
    quarantine_reason: str | None
```

### ExperienceCard

```python
class ExperienceCard(BaseModel):
    card_id: str
    title: str
    use_when: str
    do: list[str]
    do_not: list[str]
    check_first: list[str]
    evidence_atom_ids: list[str]
    confidence_score: float
    known_exceptions: list[str]
    valid_from: datetime | None
    valid_until: datetime | None
    tested_by_probe_ids: list[str]
    last_validated_at: datetime | None
    action_brief_template: str
```

### ActionBrief

```python
class ActionBrief(BaseModel):
    task_id: str | None
    applicable_card_ids: list[str]
    why_applicable: list[str]
    preconditions_to_check: list[str]
    recommended_next_actions: list[str]
    risks_and_failure_modes: list[str]
    stale_or_contested_memory_ids_to_ignore: list[str]
    evidence_links: list[str]
    confidence_score: float
    expected_action_delta: float | None
```

## 6. Public API

```python
class CEM:
    def ingest_trace(self, trace: AgentTrace) -> TraceReceipt: ...

    def propose_memories(
        self,
        trace_id: str,
        *,
        strategy: Literal["facts", "procedures", "failures", "all"] = "all",
    ) -> list[ExperienceAtom]: ...

    def validate(
        self,
        atom_id: str,
        *,
        checks: set[ValidationCheck] | None = None,
    ) -> ValidationResult: ...

    def promote(self, atom_id: str) -> ExperienceCard | None: ...

    def retrieve_action_brief(
        self,
        task: TaskContext,
        *,
        max_cards: int = 5,
    ) -> ActionBrief: ...

    def audit(self, memory_id: str) -> MemoryAudit: ...

    def confirm(self, memory_id: str) -> None: ...

    def reject(self, memory_id: str, reason: str) -> None: ...

    def run_eval(self, suite: str, *, baseline: str | None = None) -> EvalResult: ...
```

## 7. Validation Pipeline

Every candidate atom passes through these gates:

1. Source Span Presence
   - Candidate must cite source spans.
   - No span means quarantine.

2. Epistemic Role Check
   - Distinguish observed fact, user claim, tool output, assistant hypothesis, derived claim, preference, skill, and failure mode.
   - Assistant hypotheses are never promoted as facts without evidence.

3. Grounding Check
   - Candidate content must be entailed by cited spans or explicitly labeled as hypothesis.
   - Unsupported details quarantine the atom.

4. Contradiction Check
   - Compare candidate against active atoms with overlapping scope.
   - Store contradiction links instead of overwriting.

5. Temporal Validity
   - Assign validity window or TTL policy by memory type.
   - A later update can supersede an older memory without deleting historical truth.

6. Scope Check
   - Enforce user, agent, task, project, and artifact scope.
   - Scope mismatch prevents retrieval.

7. Confidence Calibration
   - Store confidence, but do not treat model confidence as truth.
   - Confidence affects quarantine/promote thresholds.

8. Promotion Probe
   - For skills/failure modes, require a probe, replay, or held-out task where possible.
   - If no probe exists, status remains candidate.

## 8. Retrieval Contract

Retrieval must not return raw memory dumps by default.

The default runtime output is an Action Brief:

```text
Given task context T,
return a compact operational brief containing:
- relevant verified cards;
- why each card applies;
- preconditions to verify before use;
- recommended next actions;
- failure modes to avoid;
- stale/contested memories to ignore;
- evidence links;
- confidence;
- expected action delta when known.
```

Raw atom/card retrieval can exist for debugging, but agent-facing retrieval should be action-brief-first.

## 9. Storage Contract

V0 storage:

- `traces.jsonl`: append-only raw trace ledger.
- `atoms.sqlite`: candidate and promoted atoms.
- `cards.sqlite`: promoted experience cards.
- `audit.sqlite`: validation, contradiction, retrieval, and influence logs.

Do not mutate evidence. Corrections create new records and links.

Minimum tables:

```text
traces(trace_id, session_id, agent_id, task_id, started_at, ended_at, outcome, path)
turns(turn_id, trace_id, turn_index, timestamp, role, content_hash, artifact_refs)
atoms(atom_id, status, epistemic_type, content, confidence, valid_from, valid_until, created_at)
atom_sources(atom_id, trace_id, turn_id, span_start, span_end)
contradictions(left_atom_id, right_atom_id, relation_type, detected_at)
cards(card_id, title, confidence, valid_from, valid_until, last_validated_at)
card_atoms(card_id, atom_id)
validations(validation_id, atom_id, check_name, result, reason, created_at)
retrievals(retrieval_id, task_id, query_hash, returned_ids, created_at)
influence_logs(influence_id, retrieval_id, action_id, outcome_delta, notes)
```

## 10. Evaluation Plan

### Primary Evals

1. HaluMem or HaluMem-compatible subset
   - extraction precision/recall/F1;
   - update recall;
   - QA accuracy over stored memory;
   - false memory resistance.

2. Synthetic Corruption Suite
   - injected contradictions;
   - stale preference;
   - unsupported assistant hypothesis;
   - poisoned memory;
   - misleading success trace;
   - crucial negative lesson from failed trace.

3. Workflow Gotchas Environment
   - small browser/workflow domain;
   - hidden order dependencies;
   - held-out tasks;
   - compare CEM-0 Action Briefs to baselines.

### Metrics

```text
MMA = TaskSuccess(memory_agent) - TaskSuccess(no_memory_agent)
```

Additional required metrics:

- extraction F1;
- update recall;
- false memory resistance;
- contradiction detection precision;
- contradiction detection recall;
- stale-memory suppression;
- quarantine false-positive rate;
- memory harm rate;
- action influence rate;
- evidence support rate;
- p95 write latency;
- p95 retrieval latency;
- tokens per write;
- tokens per retrieval.

### Baselines

- no memory;
- full context;
- rolling summary memory;
- vanilla vector memory;
- time-aware vector memory;
- unverified reflection memory;
- human-curated runbook upper bound.

## 11. First Demo Acceptance Criteria

The demo is accepted only if all are true:

1. CEM-0 quarantines at least one unsupported or contradictory memory.
2. CEM-0 promotes at least one Experience Card with source evidence.
3. A held-out workflow task succeeds with CEM-0 where no-memory fails.
4. Raw vector retrieval returns semantically related traces but does not produce the decisive precondition.
5. `audit(memory_id)` explains why the memory exists, where it came from, why it was promoted/quarantined, and when it is valid.
6. The eval report includes all baselines, including a dumb baseline that we expect to lose to.

## 12. 30-Day Sprint

Week 1:
- Scaffold `cem-core` and `cem-eval`.
- Implement Pydantic models.
- Implement JSONL/SQLite trace ledger.
- Implement synthetic trace generator with known contradictions and stale facts.

Week 2:
- Implement candidate extractor.
- Implement source-span grounding.
- Implement contradiction detector.
- Implement quarantine and audit logs.

Week 3:
- Implement HaluMem-compatible runner or local facsimile if external runner blocks.
- Implement baselines.
- Publish first extraction/update integrity table.

Week 4:
- Implement workflow gotchas demo.
- Implement Experience Card promotion.
- Implement Action Brief retrieval.
- Run held-out task comparison.
- Write public-ready benchmark report.

## 13. Kill Signals

Stop or pivot if:

- vanilla vector memory matches CEM-0 on write integrity and held-out tasks;
- verification does not improve over unverified reflection;
- false quarantine blocks useful memories too often;
- action briefs do not change decisive actions;
- the project becomes a pile of storage adapters;
- the first demo requires heavy manual curation.

## 14. Launch Claim Target

Do not claim state of the art.

Claim this if the data supports it:

> CEM-0 catches false and stale memories at write time, promotes only evidence-backed experience, and improves held-out workflow task success versus unvalidated memory baselines.

That is enough to be taken seriously.

## 15. Build Order

```text
models -> trace ledger -> extractor -> validator -> quarantine -> audit ->
baselines -> synthetic eval -> experience card promotion -> action brief ->
workflow demo -> public benchmark report
```

Do not build integrations before the synthetic eval passes.
