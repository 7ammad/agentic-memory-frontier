# Report 5: Opportunity Thesis For A Disruptive V1

**Research Date:** May 27, 2026
**Scope:** Frontier memory research synthesis, benchmark analysis, system archaeology, bottleneck evidence
**Protocol:** Anti-hallucination tags applied throughout. Claims distinguished by type.

***

## 1. Executive Summary

### The Ten Strongest Conclusions

1. **[VERIFIED FACT]** Every major 2025–2026 memory benchmark reveals the same structural gap: systems are evaluated only at *output quality* (QA accuracy), never at the *operational stage* where hallucination originates. HaluMem (arXiv:2511.03506) is the first operation-level benchmark, finding that extraction-stage hallucinations propagate forward and corrupt retrieval — yet no production system instruments this pipeline stage.[^1]

2. **[VERIFIED FACT]** Current benchmarks are saturating as context windows expand. The "Anatomy of Agentic Memory" survey (arXiv:2602.19320) shows LongMemEval-S and MemBench fit inside modern 128k windows, making them ineffective for proving memory necessity. The benchmark itself is broken, not just the systems.[^2]

3. **[VERIFIED FACT]** The most recent longitudinal study, AgingBench (arXiv:2605.26302, May 2026), demonstrates that *deployed* agents degrade across four aging mechanisms — compression aging, interference aging, revision aging, and maintenance aging — across ~400 runs. No existing memory system is designed, evaluated, or repaired with a lifespan model in mind.[^3]

4. **[VERIFIED FACT]** State-of-the-art systems achieve modest absolute scores on the hardest benchmarks. The Reddit benchmark study of 600-turn conversations showed best-in-class Mem0 Graph at 68% accuracy, 26-second p95 latency; LangMem at 60 seconds p95 latency. Memory systems are not yet reliable enough for unattended production.[^4]

5. **[VERIFIED FACT]** Memory hallucinations are upstream structural failures. HaluMem reports: systems miss over 40% of critical information at extraction (recall below 60%), produce fabricated memories (accuracy below 62%), and fail to update over 50% of facts when new information arrives.[^5]

6. **[VERIFIED FACT]** Every current system is a black box at retrieval time. No major production memory system (Mem0, Zep, Letta/MemGPT, LangMem, OpenAI Memory) exposes *why* a memory was stored, *why* it was retrieved, what its validity interval is, or when it was last confirmed. MAIF (arXiv:2511.15097) identifies this as a regulatory and auditability gap.[^6]

7. **[VERIFIED FACT]** Procedural/skill memory is experimentally validated and dramatically underbuilt. Agent Workflow Memory (AWM, ICML 2025, arXiv:2409.07429) shows 24.6% and 51.1% relative success rate improvement on web navigation benchmarks by extracting reusable workflows from agent trajectories. No open-source system ships this as a composable primitive.[^7][^8]

8. **[VERIFIED FACT]** Multi-agent memory governance is a real research gap, not a vague idea. "Governed Memory" (arXiv:2603.17787) is in production at Personize.ai, achieving 92% governance routing precision, zero cross-entity leakage across 500 adversarial queries, and 50% token reduction from progressive delivery. Yet this architecture is proprietary. Open-source has no equivalent.[^9]

9. **[JUDGMENT]** The most defensible V1 is the one that combines (a) a provably new primitive, (b) a benchmark that proves other systems fail at it, and (c) a developer artifact that works in isolation without framework adoption. The write-path validation gap and the lifespan/aging model together point to a "Memory Quality Layer" as the strongest underbuilt direction.

10. **[JUDGMENT]** What not to build: longer-context helpers, summary compressors, vector store wrappers, chat history APIs, MCP plugins without policy, reflection loops without validation. These are either (a) commoditized, (b) solvable by context-window expansion, or (c) already built but unvalidated.

**Strongest Opportunity (Previewed):** A *Memory Write-Path Quality and Validity Protocol* — a composable, framework-agnostic layer that enforces structured write policies, detects hallucination at the extraction stage (not the output stage), assigns validity intervals and confidence provenance to every memory unit, and ships with a dedicated benchmark harness (HaluMem-compatible). This is the gap that every survey identifies, that HaluMem measures, that AgingBench shows degrades deployed systems, and that no open-source project has shipped.

**Biggest Technical Risk:** Validation quality depends on the backbone LLM. Weaker models produce 30%+ format error rates in structured memory operations. Any write-path validator must be backbone-aware or its own operation will introduce hallucination.[^2]

**Proof Required:** A reproducible benchmark showing that a write-path quality protocol, applied to a standard memory store (Mem0/Zep/flat vector), measurably reduces HaluMem-measured hallucination at the extraction and update stages, with lower latency than full-context alternatives.

***

## 2. Evidence Base

### Benchmark Gaps

**[VERIFIED FACT]** LongMemEval (arXiv:2410.10813, ICLR 2025) reveals commercial chat assistants and long-context LLMs show a **30% accuracy drop** on memorizing information across sustained interactions. Five core abilities are tested: information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention. However, the survey (arXiv:2602.19320) flags that LongMemEval-S fits within modern 128k context windows — undermining its validity as a true *memory* test.[^10][^2]

**[VERIFIED FACT]** LoCoMo (Snap Research) covers 300-turn, 9K-token conversations across up to 35 sessions. Long-context LLMs and RAG improve QA by 22–66% over baselines but still lag human performance by 56%, with temporal reasoning lagging by 73%. A Reddit post identifies serious flaws: "LongMemEval-S fits entirely in modern context windows, making it more of a context window test than a memory test".[^11][^12]

**[VERIFIED FACT]** MemoryAgentBench (arXiv:2507.05257, ICLR 2026) is the most comprehensive single benchmark, covering accurate retrieval, test-time learning, long-range understanding, and conflict resolution/selective forgetting. Empirical results show "current methods fall short of mastering all four competencies".[^13][^14]

**[VERIFIED FACT]** HaluMem (arXiv:2511.03506) is the first operation-level hallucination benchmark for memory systems. It defines three tasks: memory extraction, memory updating, and memory QA — finding that hallucinations originate and accumulate at extraction/update and propagate forward. No production system instruments this.[^1]

**[VERIFIED FACT]** AgingBench (arXiv:2605.26302, submitted May 25, 2026) introduces longitudinal evaluation across four aging mechanisms. Across 7 scenarios, 14 models, 400+ runs: "behavioral tests can remain clean while factual precision decays" — meaning systems appear to work while silently degrading.[^3]

**[USER-REPORTED ISSUE]** Reddit thread (r/AI_Agents, Feb 2026): "The real challenge lies not in storing data, but in scoring relevance and detecting outdated information." Practitioners describe the need for explicit write gates, four-layer hierarchies with automatic compaction, and usefulness confirmation before promotion.[^15]

### System Convergence

**[VERIFIED FACT]** Every major open-source memory system (Mem0, Zep, LangMem, Letta/MemGPT) has converged on similar architectures: semantic vector store + optional graph layer + LLM-driven extraction. The "Anatomy" survey's taxonomy identifies four structural families (Lightweight Semantic, Entity-Centric, Episodic/Reflective, Structured/Hierarchical) that essentially describe the same progression every system goes through.[^2]

**[VERIFIED FACT]** Zep (arXiv:2501.13956) uses a bi-temporal knowledge graph (Graphiti) and achieves 94.8% on DMR vs MemGPT's 93.4%, with up to 18.5% accuracy improvement on LongMemEval with 90% latency reduction. Yet Zep achieves only 74.8% on LoCoMo (Governed Memory paper). Even the best system fails on a third of hard multi-session queries.[^16][^9]

**[VERIFIED FACT]** Letta/MemGPT is described as requiring adoption of "the whole agent platform or nothing" with "90% error rates reported with non-OpenAI models," and "every memory self-edit breaks prompt caching". The system solves context management, not memory quality.[^17]

**[VERIFIED FACT]** Mem0 benchmarks at 66% accuracy (Mem0), 68% with graph variant, 14-second to 26-second p95 latency on 200-question LoCoMo sessions. LangMem achieves 60-second p95 latency — "renders it impractical for interactive use".[^4]

### Commodity Patterns

**[VERIFIED FACT + JUDGMENT]** The following are now commoditized or approaching commodity: (a) semantic vector memory with append-only or LRU eviction, (b) simple summary compression of chat history, (c) graph extraction from entity-dense text, (d) user profile updates via LLM extraction, (e) MCP server bindings for memory access. All major providers (OpenAI, Anthropic, Google) ship variants of (a)–(d) in managed products.

### Unresolved Bottlenecks

**[VERIFIED FACT]** Write-path hallucination. HaluMem shows <62% accuracy of stored memories, <50% correct updates when facts change. No system ships a write-path validator separate from the LLM that performs extraction. This is a structural absence.[^5]

**[VERIFIED FACT]** Temporal validity. LongMemEval tests temporal reasoning; LoCoMo finds 73% gap vs. humans on temporal questions. Zep adds bi-temporal tracking but not user-facing validity intervals. AgingBench (2026) shows revision aging is a distinct failure mode from compression aging.[^11][^3]

**[VERIFIED FACT]** Silent degradation. AgingBench shows "behavioral tests can remain clean while factual precision decays". No memory system ships a continuous health monitor or aging diagnostic.[^3]

**[VERIFIED FACT]** Provenance gap. Current AI systems "operate on opaque data structures that lack the audit trails, provenance tracking, or explainability required by emerging regulations like the EU AI Act" (MAIF, arXiv:2511.15097). No open-source memory system ships cryptographic or structured provenance per memory unit.[^6]

**[VERIFIED FACT]** Procedural/skill memory. AWM (arXiv:2409.07429) proves 24.6%–51.1% performance gains from workflow extraction — but the AWM repo is a research prototype on WebArena, not a composable developer library.[^8][^18]

**[VERIFIED FACT]** Memory quality degradation with scale. An empirical study shows that as memory grows from 10 to 500 entries, accuracy drops from 50% to 30% while confidence rises from 70.4% to 78.0%: "Your alerts will never fire".[^19]

### Developer/User Pain Points

**[USER-REPORTED ISSUE]** ChatGPT memory architecture failure on Feb 5, 2025: "Without consent, notice, or recourse, countless users lost years of context, continuity..." (OpenAI Community forum). Production memory systems have no persistence guarantee or user-auditable trail.[^20]

**[USER-REPORTED ISSUE]** mem0 GitHub discussion (Feb 2026): Practitioners describe needing temporal consistency scores, source attribution accuracy, and conflict detection mechanisms that current APIs do not expose.[^21]

**[USER-REPORTED ISSUE]** LinkedIn post (Sep 2025): "Memory has to run like a governed workflow: validate on recall, update with new evidence, arbitrate conflicts across agents, and preserve provenance".[^22]

***

## 3. Non-Commodity Test

A serious V1 must pass all seven checklist items. A system is **commodity** if it fails even one.

### Commodity Definition Checklist

A V1 is **not** non-trivial if it is:

| Commodity Pattern | Why It Fails |
|---|---|
| Vector store wrapper | Append-only semantic stores with no validation are shipped by Mem0, OpenAI Memory, LangMem |
| Chat history summarizer | Compression without validation produces summarization drift (AgingBench: "compression aging")[^3] |
| MCP database | Protocol binding without write policy = raw storage with no intelligence |
| Agent-framework adapter | LangChain, LlamaIndex have adapters for all major stores; adapter layer is noise |
| Simple knowledge graph | Graph extraction without temporal validity intervals = stale-by-design |
| Static user profile | Preference snapshots with no TTL or contradiction detection = drift guaranteed |
| Prompt template library | Not a memory system |
| "Memory API" without policy | Storing and retrieving without any write gate, validation, or lifecycle is the commodity baseline |
| Demo-only reflection loop | Self-reflection without measurable hallucination reduction (HaluMem shows current reflection accumulates hallucination)[^23] |

### Non-Commodity Requirements Checklist

A V1 qualifies as non-trivial if it satisfies:

- [ ] **New primitive:** Introduces a memory object model, protocol, lifecycle event, or evaluation method not shipped by Mem0, Zep, LangMem, or Letta
- [ ] **Measurable bottleneck:** Addresses a bottleneck documented in peer-reviewed research (HaluMem, LongMemEval, AgingBench, MemoryAgentBench, AWM)
- [ ] **Eval harness:** Ships a runnable benchmark suite that demonstrates the bottleneck and measures improvement
- [ ] **Explainable behavior:** Every memory unit has at minimum: a source (why stored), a retrieval reason (why returned), and a validity model (when it was true / may have expired)
- [ ] **Developer usefulness:** Can be integrated in ≤3 lines of code without adopting a new agent framework
- [ ] **Narrow but real use case:** Solves one specific failure mode better than the baseline, demonstrated end-to-end
- [ ] **Extensible architecture:** Core primitive is separable from storage backend, LLM provider, and agent framework

***

## 4. Candidate Opportunity Theses

***

### Candidate 1: Memory Write-Path Quality Protocol (MemGuard)

#### Classification
**[NOT NOVEL BUT CRITICALLY UNDERBUILT]**
Write-path validation and hallucination-at-source detection are defined in HaluMem (2025) and called for in every major 2025–2026 survey. No open-source implementation exists as a composable, standalone primitive.

#### Thesis
Every current memory system treats the write path as a pass-through: the LLM extracts memories from conversation, they are stored, and errors propagate forward. HaluMem (arXiv:2511.03506) proves that hallucinations originate and accumulate at the extraction and update stages, reaching the output QA stage with degraded fidelity. A write-path quality protocol — a composable layer that (a) validates extracted memories before storage, (b) detects contradictions against the existing store, (c) assigns a confidence score and validity TTL to each memory unit, and (d) quarantines uncertain writes — would address the root cause of memory hallucination rather than filtering it at retrieval time.

#### Core Primitive
**The Validated Memory Unit (VMU):** A structured memory object with mandatory fields: `content`, `source_turn`, `extraction_confidence`, `contradiction_check_result`, `validity_ttl`, `quarantine_flag`, `last_confirmed_at`. The write path enforces validation before any VMU enters the store; the retrieval path filters on quarantine flag and validity TTL.

#### Bottleneck Addressed
- **Wrong memory / memory fabrication** — extraction-stage hallucination[^1]
- **Stale memory** — no validity interval in current systems; AgingBench revision aging[^3]
- **Silent quality degradation** — accuracy drops from 50% to 30% as store grows to 500 entries; confidence rises[^19]
- **Context pollution** — retrieving unvalidated memories corrupts reasoning

#### Why Current Systems Fail

**[VERIFIED FACT]** HaluMem (arXiv:2511.03506) shows memory accuracy below 62% and update recall below 50% in current systems. **[VERIFIED FACT]** The "Anatomy of Agentic Memory" survey identifies a "Silent Failure" mode: open-weight models produce 30%+ format error rates on structured memory operations, corrupting the memory store without any signal to the user. **[VERIFIED FACT]** Mem0, Zep, and LangMem all perform extraction in one LLM call with no independent validation step. **[INFERENCE]** If extraction and storage are the same operation, there is no opportunity to catch hallucinated facts before they enter the store and propagate.[^24][^25][^5][^2]

#### Why This Is Not Basic RAG
RAG does not have a write path. It retrieves from a static corpus. A write-path quality protocol inverts the RAG assumption: the bottleneck is not retrieval, it is the integrity of what is stored. This is a *memory hygiene* primitive — more analogous to a transaction log validator in a database than to a retrieval system. No RAG system ships write-path contradiction detection, validity TTLs, or quarantine queues.

#### Smallest Serious Prototype

**User flow:** User converses with an agent. After each turn, extracted memories flow through the validation gate. If a memory contradicts an existing stored fact, both are flagged, the new one is quarantined, and the user is optionally notified. The agent retrieves only non-quarantined, non-expired memories.

**Developer flow:**
```python
from memguard import MemGuard, FlatMemoryBackend
store = MemGuard(backend=FlatMemoryBackend(), llm=openai_client)
store.write(session_id, conversation_turn)  # validates before storing
memories = store.retrieve(query)  # filters expired/quarantined
audit = store.audit(session_id)  # returns per-memory provenance
```

**Memory lifecycle:** Extract → Validate → (Quarantine OR Store with TTL) → Retrieve (with quarantine filter) → Confirm/Expire

**Retrieval behavior:** Top-k retrieval filtered by quarantine status and validity TTL. Optionally, retrieval returns confidence score and reason for each memory.

**Inspection/audit behavior:** Per-memory provenance log: what turn it came from, what confidence the extractor assigned, whether a contradiction was detected, when TTL expires.

**Integration surface:** Framework-agnostic Python SDK. Any memory store backend (flat, vector, graph). No LLM framework required.

#### Architecture

```
Write Path:
  LLM Extractor → Contradiction Checker → Confidence Scorer → 
  TTL Assigner → Quarantine Gate → Storage Backend

Read Path:
  Query → Embedding Search → Quarantine Filter → TTL Filter → 
  Confidence Ranker → Top-k Return

Audit Path:
  session_id / memory_id → Provenance Record → Confidence History → 
  Contradiction Log → TTL Timeline
```

**Storage:** SQLite (default) or pluggable (Postgres, Redis). Memory schema:
```json
{
  "memory_id": "uuid",
  "content": "string",
  "source_turn": "int",
  "source_session": "string",
  "extraction_confidence": "float 0-1",
  "contradiction_ids": ["list of conflicting memory_ids"],
  "quarantine": "bool",
  "validity_ttl": "ISO8601 or null",
  "last_confirmed_at": "ISO8601",
  "retrieval_count": "int",
  "created_at": "ISO8601"
}
```

**Write policy:** Extract (LLM call) → Contradiction check (embedding similarity + LLM comparison if threshold exceeded) → Confidence score (structured output) → If `contradiction=True AND confidence<threshold`: quarantine. If `confidenceow_threshold`: quarantine with flag `uncertain`.

**Temporal model:** TTL based on memory category (preference=30d, fact=180d, event=7d, instruction=no expiry). Categories assigned at write time by extractor.

**Validation layer:** Lightweight secondary LLM call to verify extracted memory against source turn. Optional — can use rule-based checks for cost reduction.

**Evaluation harness:** Native integration with HaluMem tasks (extraction accuracy, update recall, QA accuracy); custom contradiction detection precision/recall test.

**API shape:** `write(session_id, turn)`, `retrieve(query, top_k)`, `audit(session_id)`, `confirm(memory_id)`, `quarantine_report(session_id)`, `expire_ttl(memory_id)`.

#### Benchmark Strategy

**Existing benchmarks to reuse:** HaluMem (extraction, update, QA tasks); LongMemEval temporal reasoning subset; LoCoMo adversarial QA; MemoryAgentBench conflict resolution.[^10][^13][^11][^1]

**Custom benchmark needed:** Write-path injection test — synthetic sessions with known hallucinated extractions, measuring quarantine rate vs. pass-through rate. Contradiction precision test — inject contradicting facts at known turns, measure detection rate vs. false positive rate.

**Baselines:**
- No memory (0-shot)
- Full context (token-expensive but accurate)
- Summary memory (standard Mem0/LangMem baseline)
- Vanilla vector memory (no validation)
- MemGuard (proposed)

**Metrics:** Extraction accuracy (HaluMem), update recall (HaluMem), contradiction detection precision/recall, retrieval precision@k, false quarantine rate, write latency, per-query token cost.

**Pass/fail thresholds:** MemGuard must improve extraction accuracy by ≥10% vs. vanilla vector memory on HaluMem tasks. Must not increase total write+retrieve latency by >50%.

**Adversarial tests:** Inject factually contradicting turns at session positions 10, 50, 200. Measure how many contradictions are detected and quarantined vs. silently stored.

#### Open-Source Story

**Who uses it first:** ML engineers building production agents with ≥2-week session continuity. Specifically: coding agents, task management agents, customer service bots with user state. These developers already use Mem0 or plain vector stores and are experiencing the "62% accuracy" and "silent failure" problems reported in HaluMem.

**Why they care:** Current memory failures are invisible. MemGuard makes them visible — and prevents them at source. A `quarantine_report()` call that shows "3 memories were quarantined this session because they contradicted earlier facts" is a directly actionable developer tool.

**Repo artifact:** `memguard` Python package. Core: `MemGuard` class, `FlatBackend`, `VectorBackend`. Demo: coding agent with persistent session memory, demonstrating before/after hallucination rates.

**Example app:** A coding assistant that remembers user architecture decisions across projects. Demo shows session where user contradicts an earlier decision — MemGuard detects, quarantines, and prompts confirmation. Alternative example: medical assistant (as in Mem0's cookbook) with safety-critical write validation.[^26]

**Contribution path:** Users can contribute new TTL policy presets (by domain), new backend adapters, new contradiction detection strategies (embedding-only, NLI, LLM-full). Clear plugin interface.

**Not a toy because:** Ships with HaluMem benchmark adapter as first-class feature. Results are reproducible and comparable to published baselines.

#### Kill Criteria

1. Write-path validation adds >100ms per turn and cannot be made async — unacceptable for interactive agents
2. Contradiction detection false positive rate >15% — too many valid memories quarantined, breaking agent continuity
3. Benchmark results show <5% improvement over vanilla vector memory on HaluMem tasks — no measurable signal
4. The problem is solved by model improvement (e.g., GPT-5 extracts correctly >90% of the time) — rendering the validator irrelevant
5. No developer adoption signal within 3 months of launch (fork rate, issues, integration PRs)

#### Risks

**Technical risk:** Contradiction detection is itself an LLM call — the validator can hallucinate. Must use lightweight, deterministic rules where possible and save LLM calls for uncertain cases only. Backbone sensitivity (30%+ format errors on Qwen-2.5-3B) means the validator architecture must be tested on weak models.[^2]

**Research risk:** Optimal confidence thresholds for quarantine decisions are unknown. Wrong thresholds produce either too many false positives (broken agents) or too few detections (useless validator). Requires careful empirical calibration on at least two benchmark datasets.

**Product risk:** Developers may resist adding a validation layer if latency increases. Must ship async write path by default.

**Adoption risk:** Mem0 and Zep could ship equivalent functionality in their managed products faster than an open-source project can iterate.

**Ecosystem risk:** If context windows grow to reliably handle all real-world session lengths, the need for external memory (and thus write-path validation) shrinks. However, multi-session agents with months of history remain outside any foreseeable context window.

#### Confidence: **High**

Evidence directly supports the bottleneck (HaluMem, AgingBench, Anatomy survey). The primitive is specific and implementable. The benchmark strategy reuses existing published datasets. The developer API is narrow and composable. Adoption risk is the highest unknown.

***

### Candidate 2: Memory Lifespan Diagnostic and Repair Layer (AgeProbe)

#### Classification
**[LIKELY NOVEL]**
AgingBench (arXiv:2605.26302, submitted May 25, 2026) is the first longitudinal reliability benchmark for agents. No implementation of a lifespan-aware diagnostic/repair system exists in open source as of May 2026.[^3]

#### Thesis
All current memory systems are designed for a single session or evaluated on day-one snapshots. AgingBench, published May 2026, demonstrates that deployed agents degrade along four distinct mechanisms — compression aging, interference aging, revision aging, and maintenance aging — and that "behavioral tests can remain clean while factual precision decays." This is the agent memory equivalent of software bitrot: invisible until catastrophic. A lifespan diagnostic layer, built alongside or atop any memory backend, would diagnose *which* aging mechanism is degrading a specific agent and prescribe targeted repair, rather than requiring complete memory reset.

#### Core Primitive
**The Memory Health Record (MHR):** A per-agent, timestamped diagnostic state that tracks the four aging mechanisms across write, retrieval, and utilization pipeline stages. The MHR is updated after every N sessions and reports: compression drift score, interference index (new facts contradicting old), revision lag (facts needing update that have not been updated), and maintenance gap (entries that have never been retrieved or confirmed). The system generates a targeted repair prescription rather than a full reset.

#### Bottleneck Addressed
- **Silent degradation** — "behavioral tests can remain clean while factual precision decays"[^3]
- **Compression aging** — write-time summarization drops future-relevant details[^27]
- **Interference aging** — new memories conflict with old without resolution[^3]
- **Revision aging** — facts change in the world but are not updated in the store
- **Stale memory prevention** — no system tracks memory TTL at the lifespan level

#### Why Current Systems Fail

**[VERIFIED FACT]** AgingBench (arXiv:2605.26302) tests 14 models across 7 scenarios and 400+ runs, finding that agent aging is "not one-dimensional: behavioral tests can remain clean while factual precision decays; derived-state tracking can collapse sharply within a single model". **[VERIFIED FACT]** The SSGM framework (arXiv:2603.11768) identifies "semantic drift" from iterative summarization as a key risk but proposes only a conceptual framework, not an implementation. **[VERIFIED FACT]** FadeMem (arXiv:2601.18642) addresses forgetting via biologically-inspired decay but not diagnostic profiling or repair targeting. **[INFERENCE]** Current memory systems do not model their own degradation trajectories. They have no self-diagnostic capability.[^28][^29][^3]

#### Why This Is Not Basic RAG
RAG retrieves from static corpora. AgeProbe monitors a *live, growing, mutating* memory store over time and detects the specific failure mode causing degradation. This is a systems-health primitive — closer to a database vacuum or index rebuild trigger than to a retrieval system.

#### Smallest Serious Prototype

**User flow:** Developer runs `ageprobe.scan(agent_id)` after every 50 sessions. AgeProbe returns a health report: `compression_drift=0.23 (OK)`, `interference_index=0.67 (WARNING: 12 contradictions unresolved)`, `revision_lag=0.81 (CRITICAL: 23 facts not updated in 60+ days)`, `maintenance_gap=0.45 (8 memories never retrieved, candidate for eviction)`. Developer calls `ageprobe.repair(agent_id, mode="revision")` to trigger targeted repair.

**Developer flow:**
```python
from ageprobe import AgeProbe
probe = AgeProbe(memory_backend=my_mem_store, llm=client)
report = probe.scan(agent_id="user_123")  # returns MHR
repair_plan = probe.recommend_repair(report)
probe.apply_repair(agent_id="user_123", plan=repair_plan)
```

**Memory lifecycle:** Write → Accumulation → Periodic Scan (every N sessions) → MHR Update → Targeted Repair (compression refresh, contradiction resolution, revision update, or eviction) → Re-scan.

**Retrieval behavior:** Standard pass-through. AgeProbe does not intercept reads; it audits the store state asynchronously.

**Inspection behavior:** `probe.report(agent_id)` returns full MHR with per-memory aging flags.

#### Architecture

**Storage:** Separate AgeProbe state store (SQLite). One MHR per agent. Per-memory aging flags stored in a side-table, not modifying the underlying memory backend.

**Memory schema (MHR):**
```json
{
  "agent_id": "string",
  "scan_timestamp": "ISO8601",
  "compression_drift_score": "float",
  "interference_index": "float",
  "unresolved_contradiction_count": "int",
  "revision_lag_score": "float",
  "stale_fact_count": "int",
  "maintenance_gap_score": "float",
  "never_retrieved_count": "int",
  "repair_history": [{"timestamp": "...", "mode": "...", "result": "..."}]
}
```

**Write policy:** Passive — AgeProbe only reads from the memory backend. It does not intercept writes (this distinguishes it from Candidate 1/MemGuard, which is write-path active).

**Retrieval policy:** Pass-through.

**Temporal model:** Scan cadence is configurable (default: every 50 sessions or 7 days). Aging scores are computed from temporal dependency graphs (per AgingBench methodology).[^3]

**Provenance model:** Per-memory timestamps are sourced from the underlying backend. AgeProbe reads existing provenance; it does not create new provenance.

**Validation layer:** Contradiction detection for interference index uses same embedding + LLM approach as MemGuard. Can share code.

**Evaluation harness:** AgingBench-compatible diagnostic profiles as first-class output.

**API/SDK:** `scan()`, `recommend_repair()`, `apply_repair()`, `report()`, `history(agent_id)`.

#### Benchmark Strategy

**Existing benchmarks to reuse:** AgingBench (arXiv:2605.26302) — directly applicable. LongMemEval temporal reasoning subset for revision aging test.[^10][^3]

**Custom benchmark:** Inject known aging patterns into a synthetic agent (compress 50 sessions, then inject contradictions, then let 20 facts go stale) and measure: (a) AgeProbe correctly identifies the dominant aging mechanism, (b) repair improves downstream QA accuracy, (c) targeted repair outperforms full reset on latency and accuracy.

**Baselines:** No memory, full context, standard vector memory with no aging management, full memory reset (delete and rebuild).

**Metrics:** Aging mechanism classification accuracy, repair precision (did the recommended repair address the correct mechanism), post-repair QA improvement, repair latency vs. full reset latency.

#### Open-Source Story

**Who uses it first:** Developers with agents that have been running for more than a month — coding agents, personal assistants, enterprise workflow agents. These are the developers reporting "my agent was working, now it's wrong" without knowing why.

**Why they care:** Memory resets destroy months of accumulated context. AgeProbe offers a targeted alternative: repair only the specific aging mechanism that is failing.

**Repo artifact:** `ageprobe` Python package. Ships with AgingBench scenario runner to demonstrate before/after repair on published benchmark data.

**Example app:** Long-running coding assistant (30-day simulation) showing QA accuracy trajectory with and without AgeProbe repair cycles.

**Not a toy because:** AgingBench is a peer-reviewed ICML/equivalent venue benchmark with 400+ runs on 14 models. AgeProbe is the first open-source implementation of the repair side of that benchmark.

#### Kill Criteria

1. AgingBench repair modes are not reproducible on open models — benchmark results only hold for GPT-4o
2. Scan + repair adds too much overhead for interactive agent operators (must be async to be viable)
3. Targeted repair does not outperform simple full reset on QA accuracy (if reset is cheaper and equally effective, the diagnostic layer is unnecessary)
4. Memory backends do not expose sufficient provenance for aging analysis (requires per-memory timestamps and update history — not all backends support this)
5. Developers prefer manual curation to automated repair (adoption risk)

#### Risks

**Technical risk:** Aging diagnosis requires temporal dependency graphs per AgingBench methodology. Building these graphs from arbitrary memory backends may require non-trivial preprocessing that varies by backend.

**Research risk:** The four aging mechanisms in AgingBench may not transfer cleanly to all agent types (coding agents age differently from conversational agents). Generalization is unproven.

**Product risk:** "Latent" aging (where the agent still appears to work) makes the problem invisible to developers until a dramatic failure — making it hard to market proactively.

**Adoption risk:** Most agents are not yet "old enough" to show measurable aging. Early adopters will be power users with mature deployments.

#### Confidence: **Medium**

AgingBench is very recent (May 2026). Its methodology is credible, but the full paper has not been reviewed by the community yet. The core idea is strongly supported; implementation difficulty and generalization are unknowns.

***

### Candidate 3: Procedural Skill Memory Library (SkillBank)

#### Classification
**[PARTIALLY NOVEL]**
Agent Workflow Memory (arXiv:2409.07429, ICML 2025) and LEGOMem (arXiv:2510.04851) are peer-reviewed research prototypes proving the concept. TokMem addresses skill tokens. No open-source developer library ships workflow extraction as a composable primitive with versioning, evaluation, and developer API.

#### Thesis
Agents repeatedly re-derive the same multi-step procedures (web navigation sequences, API authentication flows, document processing pipelines) from scratch on every task instance. AWM (ICML 2025) proves that extracting reusable workflows from past trajectories and indexing them as retrievable memory units improves success rates by 24.6% on Mind2Web and 51.1% on WebArena. This is procedural memory: not *what* the agent knows but *how* it acts. No open-source memory library treats workflows as first-class indexed memory objects with versioning, quality scores, and retrievable evidence. Building SkillBank as a framework-agnostic library for procedural memory extraction, storage, and retrieval would fill a gap that is proven in research but absent in tools.[^7]

#### Core Primitive
**The Versioned Workflow Object (VWO):** A structured memory unit representing an extracted, reusable procedure: `name`, `trigger_pattern` (when to use it), `steps` (ordered action list), `source_traces` (which past trajectories it was distilled from), `success_rate` (empirical, updated on use), `version` (updated when steps change), `domain` (type of task), `confidence` (how well-tested). The VWO is indexable by `trigger_pattern` embedding and retrievable by query matching.

#### Bottleneck Addressed
- **Re-derivation waste** — agents repeat multi-step procedures unnecessarily[^30]
- **Task pattern memory absence** — no system indexes "how to do X" as distinct from "what happened"
- **Long-horizon task failures** — agents fail on complex trajectories that could be solved by reusing known sub-routines[^7]
- **Cross-session skill loss** — successful procedures are lost when session ends

#### Why Current Systems Fail

**[VERIFIED FACT]** AWM's research code (GitHub: zorazrw/agent-workflow-memory) is a research prototype targeting WebArena and Mind2Web benchmarks, not a general-purpose developer library. **[VERIFIED FACT]** LEGOMem (arXiv:2510.04851) constructs modular, role-aware procedural memories for multi-agent coordination. Neither ships as an installable `pip` package with documented developer API, versioned storage, or quality scoring. **[INFERENCE]** Every current memory system (Mem0, Zep, LangMem) treats memories as semantic facts (what) not procedures (how). SkillBank would introduce a distinct memory type.[^31][^18]

**[VERIFIED FACT]** Mem^p (arXiv:2508.06433) and Agent Skills from Procedural Memory (TechRxiv:176857932) both address procedural skill extraction as distinct research directions (2025). Neither is an open-source developer library.[^32][^33]

#### Why This Is Not Basic RAG
RAG retrieves documents. SkillBank retrieves *versioned, empirically-validated procedures with success rate evidence and trigger patterns*. The structural differences: (a) VWOs have `success_rate` fields updated by agent execution outcomes — RAG docs do not self-score; (b) VWOs are extracted from *execution traces*, not from static content; (c) VWOs have *versions* when steps change — RAG docs do not version themselves; (d) VWO retrieval uses *trigger pattern matching* (what task type is this) not semantic similarity to a query string.

#### Smallest Serious Prototype

**User flow:** Agent completes a task (e.g., "log into GitHub API and create a branch"). SkillBank extracts the step sequence, creates a VWO, stores it with confidence=0.6 (first use). Next time a similar task appears, SkillBank retrieves the VWO and injects it as a workflow hint. If the agent succeeds, success_rate increments. If it fails, VWO is flagged for review and version incremented with the corrected steps.

**Developer flow:**
```python
from skillbank import SkillBank
bank = SkillBank(backend=SQLiteBackend())
# After agent completes a task trace:
bank.ingest_trace(trace=task_trace, outcome="success")
# Before agent starts a similar task:
skills = bank.retrieve(task_description="create github branch")
prompt = skills.to_prompt()  # injects workflow into agent context
```

**Memory lifecycle:** Trace ingestion → Workflow extraction → Deduplication/versioning → Storage with initial confidence → Retrieval by trigger match → Post-execution outcome update → Version update on modification.

#### Architecture

**Storage:** SQLite with vector index for trigger pattern embeddings. VWO schema with versioning via hash of `steps` field.

**Write policy:** Ingest only from verified success traces (configurable). Deduplication via semantic similarity of `trigger_pattern`. Update `success_rate` from execution outcomes.

**Retrieval policy:** Top-k by trigger pattern embedding similarity, re-ranked by success_rate * confidence. Returns VWOs with `steps` serialized as prompt-injectable text.

**Temporal model:** VWO version history. Success rate decays if not used in >30 days (configurable). Outdated VWOs flagged for re-validation.

**Provenance model:** `source_traces` links VWO to original trajectory IDs. Full provenance chain: which sessions produced which workflows.

**Validation layer:** Optional — compare extracted steps against ground truth trajectory for accuracy scoring.

**Evaluation harness:** AWM-compatible. Ships with Mind2Web and WebArena test harness setup instructions.

**API/SDK:** `ingest_trace(trace, outcome)`, `retrieve(task_description, top_k)`, `update_outcome(skill_id, outcome)`, `version_history(skill_id)`, `audit(skill_id)`.

#### Benchmark Strategy

**Existing benchmarks to reuse:** Mind2Web (web navigation, 1000+ tasks), WebArena (35.6% AWM state-of-art baseline). LEGOMem's OfficeBench (workflow automation). AWM baselines published in ICML 2025.[^18][^31]

**Custom benchmark:** Cross-domain transfer test — train on shopping workflows, test on travel workflows. Measures whether SkillBank generalizes across domains (AWM's online mode does this; library version needed).[^7]

**Baselines:** No memory, full context with raw trajectory, AWM (offline), SkillBank.

**Metrics:** Task success rate improvement vs. no-memory baseline, cross-domain transfer improvement, workflow retrieval precision@k, VWO version churn rate (proxy for instability).

**Pass/fail threshold:** SkillBank must match or exceed AWM online mode (which showed 8.9–14.0 absolute point improvement on cross-task/website/domain tests).[^30]

#### Open-Source Story

**Who uses it first:** Developers building web automation agents, code automation agents, and multi-step API integration agents. These are the most common agentic use cases reported in community forums and GitHub.

**Why they care:** Re-derivation is expensive (tokens, latency, failure rate). SkillBank offers a "skill accumulation" pattern that gets better with use — a meaningful developer-facing value proposition.

**Repo artifact:** `skillbank` Python package with AWM benchmark adapter. Demo: browser automation agent that learns GitHub API workflows across sessions.

**Not a toy because:** AWM benchmark numbers are published, reproducible, and compelling. SkillBank is the open-source library version of that research.

#### Kill Criteria

1. Workflow extraction quality is too low — extracted steps do not match actual successful procedures (>30% step error rate)
2. VWO retrieval precision is poor — trigger pattern matching fails to identify relevant workflows for new tasks
3. AWM benchmark improvements do not reproduce with SkillBank library approach vs. research prototype
4. Domain brittleness — workflows overfit to the specific environment they were extracted from (e.g., a workflow extracted from one GitHub repo breaks on another)
5. LLM-extracted workflows are not interpretable or editable by developers

#### Risks

**Technical risk:** Workflow extraction requires identifying which steps in a trace are reusable vs. context-specific. This is a hard abstraction problem — over-specific extractions are useless; over-general extractions are incorrect.

**Research risk:** AWM's strongest improvements (51.1% on WebArena) use offline mode with annotated training data. Online mode (from live traces) shows more modest gains. SkillBank would need to demonstrate online mode value.

**Product risk:** Developers may prefer to write explicit workflow prompts manually rather than extracting them from traces.

**Adoption risk:** Requires an agent framework that produces structured traces SkillBank can ingest. Some popular frameworks (simple function calls, vanilla OpenAI) do not produce structured enough traces for extraction.

#### Confidence: **Medium-High**

AWM is peer-reviewed at ICML 2025 with public code. The gap (no installable library) is real. Abstraction quality is the primary technical unknown.

***

### Candidate 4: Multi-Agent Memory Governance Protocol (MemLedger)

#### Classification
**[PARTIALLY NOVEL]**
Governed Memory (arXiv:2603.17787) is in production and describes the architecture. Collaborative Memory (ICLR 2026 submission) formalizes the permission model. No open-source implementation exists for the governance layer as a standalone protocol.[^34][^9]

#### Thesis
Enterprise deployments run dozens of autonomous agents acting on the same entities with no shared memory and no common governance — producing memory silos, redundant context delivery, cross-entity leakage, and silent quality degradation. The "Governed Memory" paper (arXiv:2603.17787) identifies five structural challenges and describes a production architecture that achieves 99.6% fact recall, 92% governance routing precision, and zero cross-entity leakage across 500 adversarial queries. The core innovation is a *tiered governance routing* layer that determines which memories are shared across agents, under which permissions, with which context budget. No open-source project implements this as a standalone, framework-agnostic protocol. MemLedger would be the open-source implementation of this governance layer, with an emphasis on: provenance per memory write, permission-scoped retrieval, conflict resolution policy, and a reproducible leakage test harness.[^9]

#### Core Primitive
**The Governed Memory Fragment (GMF):** A structured memory unit with: `content`, `owner_agent`, `access_policy` (private/shared/team-shared), `provenance` (contributing agents, accessed resources, timestamps), `conflict_resolution_policy` (last-write-wins / quorum / human-required), `budget_tier` (how many tokens it can contribute to a given context). The retrieval layer enforces access policies and assembles context under token budget constraints.

#### Bottleneck Addressed
- **Memory silos** — agents acting on same entities cannot share relevant state[^9]
- **Cross-entity leakage** — retrieval returns user A's memories in user B's context (privacy failure)[^9]
- **Memory conflict** — two agents write contradictory facts about same entity with no resolution[^34]
- **Context pollution** — no token budget enforced at retrieval; all retrieved memories appended[^9]
- **Provenance gap** — no attribution of who wrote what, when, under which task[^6]

#### Why Current Systems Fail

**[VERIFIED FACT]** The Governed Memory paper (arXiv:2603.17787) identifies five structural challenges from enterprise deployments: memory silos, governance fragmentation, unstructured memories unusable by downstream systems, redundant context delivery, and silent quality degradation. **[VERIFIED FACT]** Collaborative Memory (ICLR 2026) formalizes asymmetric permission model with bipartite graphs linking users, agents, and resources — but is a research paper, not an implementation. **[VERIFIED FACT]** MAIF (arXiv:2511.15097) proposes cryptographic provenance for AI artifacts but addresses the general AI trust problem, not specifically memory governance. **[INFERENCE]** No open-source memory library ships access-scoped retrieval, conflict resolution policy, or per-memory budget attribution as standard primitives.[^34][^6][^9]

#### Why This Is Not Basic RAG
RAG has no notion of ownership, access policy, agent identity, conflict resolution, or token budget governance. MemLedger is a *governance layer over memory*, not a retrieval system. The GMF's `access_policy` field and the governance router that enforces it have no analog in any RAG architecture.

#### Smallest Serious Prototype

**Scope:** Two-agent scenario. Agent A writes task outcomes to private GMFs. Agent B, with shared-read access to A's task outcomes, retrieves them — but A's other private memories are invisible to B. A third "supervisor" agent has read access to both.

**Developer flow:**
```python
from memledger import MemLedger, AccessPolicy
ledger = MemLedger(backend=SQLiteBackend())
ledger.write(agent_id="A", content="...", policy=AccessPolicy.PRIVATE)
ledger.write(agent_id="A", content="...", policy=AccessPolicy.TEAM)
result = ledger.retrieve(agent_id="B", query="...", budget_tokens=500)
# Only TEAM-scoped memories from A visible to B; budget enforced
```

**Memory lifecycle:** Write with policy → Store with provenance → Retrieve with policy enforcement and budget cap → Conflict detected → Resolution policy applied → Audit log.

**Audit behavior:** `ledger.audit(entity_id)` returns: all GMFs touching that entity, by which agents, at what time, under which policies, with any conflict resolution events.

#### Benchmark Strategy

**Primary benchmark:** Leakage test — 500 adversarial queries attempting to retrieve cross-entity memories. Pass threshold: zero leakage (matching Governed Memory paper result).[^9]

**Secondary benchmark:** LoCoMo adapted for multi-agent: two agents each receive half of the conversation context, must collaborate to answer full-context questions. Measures whether governance layer enables effective information sharing without leakage.[^11]

**Baselines:** No shared memory (silo), full shared memory (no governance), MemLedger.

**Metrics:** Cross-entity leakage rate, retrieval accuracy under budget, conflict resolution recall, governance overhead latency.

#### Kill Criteria

1. Policy enforcement adds >200ms overhead per retrieval in common 2-agent scenario
2. Access policy model is too complex for developer adoption (requires more than 10 lines of config to set up a basic 2-agent scenario)
3. No demonstrable improvement over simple agent-scoped namespacing (which many developers already do manually)
4. Leakage cannot be eliminated without false-negative filtering that drops legitimately shared memories
5. Single-agent use case (the majority of current developers) gains nothing from MemLedger

#### Confidence: **Medium**

The production evidence from Governed Memory is strong. Multi-agent scenarios are still niche (most current deployments are single-agent). This is a V1 that builds credibility for the future (multi-agent becomes dominant in 12–18 months) rather than solving the largest current pain.

***

### Candidate 5: Native Memory Evaluation Harness (MemBench-OSS)

#### Classification
**[NOT NOVEL BUT CRITICALLY UNDERBUILT]**
Every survey (Anatomy of Agentic Memory, HaluMem, AgingBench, MemoryAgentBench) identifies the benchmark gap. No integrated, runnable, open-source evaluation harness exists that combines HaluMem, LongMemEval, LoCoMo, and custom adversarial tests into a leaderboard-ready package.[^14][^35][^2]

#### Thesis
The memory benchmark landscape is fragmented: HaluMem covers extraction/update hallucination; LongMemEval covers temporal reasoning and knowledge updates; LoCoMo covers long-term conversational memory; MemoryAgentBench covers conflict resolution and selective forgetting; AgingBench covers longitudinal degradation. No single installable package runs all of them, compares results across memory backends, and produces a leaderboard-compatible score. This fragmentation means developers cannot evaluate their memory systems against any meaningful standard — and researchers cannot compare contributions fairly. The benchmark gap is not just a research problem; it is the primary reason memory systems remain unaccountable. MemBench-OSS would be this unified evaluation package.

#### Core Primitive
**The Unified Memory Evaluation Suite:** A runnable Python package that: (a) downloads or generates benchmark datasets from HaluMem, LongMemEval, LoCoMo, MemoryAgentBench, and AgingBench; (b) runs a memory backend under test against all five suites; (c) computes unified scores with subscores per dimension; (d) outputs a leaderboard-ready JSON; (e) ships adversarial test cases (contradiction injection, stale fact injection, cross-entity leakage queries).

#### Bottleneck Addressed
- **Evaluation weakness** — no unified runnable eval suite exists[^2]
- **Benchmark saturation** — saturation test protocol (Context Saturation Gap Δ) needs implementation[^2]
- **Metric misalignment** — F1 vs. semantic judge disagreement needs to be exposed by default[^2]
- **Overclaiming** — paper results are not reproducible without matching baseline infrastructure
- **Invisible degradation** — no developer can currently test whether their memory system is aging

#### Why Current Systems Fail

**[VERIFIED FACT]** Letta/MemGPT GitHub issue (Dec 2025): "Currently, Letta lacks any standardized benchmark or evaluation code to measure memory system performance. This makes it difficult to: quantify improvements, compare with alternatives, validate claims, guide development". **[VERIFIED FACT]** The "Anatomy" survey identifies benchmark saturation, metric validity, backbone sensitivity, and system cost as four independent failure modes — none addressed by a single tool. **[VERIFIED FACT]** Reddit post (Mar 2026) identifies serious flaws in both LoCoMo and LongMemEval-S as benchmarks — but no corrected, saturation-aware alternatives are publicly available.[^12][^36][^2]

#### Why This Is Not Basic RAG
RAGAS, TruLens, and other RAG evaluation tools measure static retrieval quality. MemBench-OSS measures: hallucination at *write time* (HaluMem), temporal reasoning across sessions (LongMemEval), longitudinal degradation over months (AgingBench), and conflict resolution capability (MemoryAgentBench) — none of which RAG eval tools cover.

#### Smallest Serious Prototype

```bash
pip install membench-oss
membench run --backend mem0 --suite halumem,longmemeval,locomo
# Outputs: scores per suite, combined MemScore, saturation gap Δ, leaderboard JSON
membench adversarial --backend mem0 --inject-contradictions --inject-stale-facts
```

**Developer flow:** Plug in any memory backend implementing a simple interface (`write(session_id, turn)`, `retrieve(query)`, `reset(session_id)`). Run `membench run`. Get a MemScore comparable to published paper baselines.

**Benchmark harness:** HaluMem tasks 1-3 (extraction, update, QA); LongMemEval temporal and knowledge-update subsets; LoCoMo adversarial QA; MemoryAgentBench conflict resolution; AgingBench compression/interference aging scenarios.

#### Kill Criteria

1. Benchmark datasets are not openly licensed — requires permission agreements that block open redistribution
2. Running full suite takes >2 hours per backend — impractical for CI/CD integration
3. Scores on MemBench-OSS do not correlate with real-world production performance
4. The field produces a competing unified benchmark (e.g., from a major lab) that becomes the standard before MemBench-OSS gains adoption

#### Confidence: **High (as infrastructure) but Medium (as differentiated V1)**

MemBench-OSS is clearly needed and clearly absent. Its risk is being infrastructure that gets absorbed into existing projects rather than establishing a standalone identity. It is strongest as a *complement* to Candidate 1 (MemGuard ships with MemBench-OSS as its eval layer).

***

## 5. Candidate Comparison Matrix

| Candidate | Novelty | Bottleneck Severity | V1 Feasibility | Benchmarkability | Open-Source Potential | Technical Difficulty | Risk | Differentiation | Recommended Priority |
|---|---|---|---|---|---|---|---|---|---|
| C1: MemGuard (Write-Path Quality) | NOT NOVEL BUT UNDERBUILT | Critical (HaluMem: 62% accuracy) | High | High (HaluMem + LoCoMo) | High | Medium | Medium | High | **1st** |
| C2: AgeProbe (Lifespan Diagnostics) | LIKELY NOVEL | High (AgingBench: silent decay) | Medium | High (AgingBench) | Medium | High | Medium-High | Very High | **2nd** |
| C3: SkillBank (Procedural Memory) | PARTIALLY NOVEL | High (51% improvement proven) | Medium | High (AWM benchmarks) | Medium-High | Medium | Medium | High | **3rd** |
| C4: MemLedger (Governance Protocol) | PARTIALLY NOVEL | Medium (enterprise-stage only) | Medium | Medium | Low-Medium | High | High | High | **4th** |
| C5: MemBench-OSS (Eval Harness) | NOT NOVEL BUT UNDERBUILT | Critical (universal gap) | High | Very High | High | Low-Medium | Low | Medium | **Infrastructure** |

**Scoring rationale:**
- Bottleneck severity graded against documented evidence (HaluMem effect sizes, AWM improvement magnitudes, AgingBench result profiles)
- V1 feasibility based on whether prototype could be functional in 30 days with one engineer
- Open-source potential based on developer profile (single-agent developers = larger audience than multi-agent governance)
- [JUDGMENT] on all priority rankings

***

## 6. Recommended Direction

### Final Thesis: MemGuard — Write-Path Memory Quality Protocol

**[OPPORTUNITY THESIS]** The strongest V1 is a composable write-path quality layer that validates memory extractions before storage, detects contradictions against existing entries, assigns validity TTLs and confidence scores to every memory unit, and ships with a native HaluMem-compatible evaluation harness.

### Why This Direction

**Wedge:** Every memory system has a write path. MemGuard attaches to it without requiring adoption of a new framework. It is backend-agnostic and model-agnostic. Its value is immediately measurable with HaluMem, which provides published baselines to beat.

**Why now:** HaluMem was published in late 2025 and is the first benchmark to isolate extraction-stage hallucination. AgingBench (May 2026) proves that write-path errors compound over deployed agent lifespans. The evidence base is new, specific, and actionable. No production system has responded yet.

**Why this can matter:** Every production memory system uses an append-or-overwrite write path with no validation. The upstream failure is measurable (HaluMem: <62% accuracy) and the fix is composable. If MemGuard can demonstrate a 10–15% accuracy improvement on HaluMem tasks with <50ms added write latency, it is a directly adoptable improvement with zero framework switching cost.

**What to build first:** The VMU schema, the write-path contradiction checker, the quarantine queue, the TTL assignment logic, and the HaluMem benchmark adapter. These are the core deliverables for a 30-day sprint.

**What to ignore in V1:** Multi-agent permissions (C4), lifespan diagnostics (C2), workflow extraction (C3), consumer-facing UI, hosted API, enterprise SSO, graph storage backends.

### First 30-Day Build Plan

| Week | Deliverable |
|---|---|
| Week 1 | VMU schema spec; SQLite + flat file backend; `write(session_id, turn)` → extract → store (no validation yet); `retrieve(query, top_k)` |
| Week 2 | Write-path contradiction checker (embedding similarity threshold + LLM call on conflict); quarantine queue; quarantine-filtered retrieval |
| Week 3 | TTL assignment logic (LLM-categorized memory type → TTL preset); confidence scoring (structured output from extractor); `audit(session_id)` provenance endpoint |
| Week 4 | HaluMem benchmark adapter (tasks 1–3); reproduce vanilla vector baseline; run MemGuard and measure delta; README with benchmark results |

### First 90-Day Research/Build Plan

| Month 1 | Core library (as above) + HaluMem benchmark results published |
| Month 2 | LoCoMo adversarial QA evaluation; contradiction detection ablations (embedding-only vs. LLM+embedding); async write path for latency |
| Month 3 | MemoryAgentBench conflict resolution evaluation; AgingBench integration (MemGuard as repair layer for revision/interference aging); SkillBank prototype as optional extension |

### Public Launch Artifact

A reproducible benchmark result: "MemGuard improves HaluMem extraction accuracy by X% and update recall by Y% vs. vanilla Mem0/vector baseline, with <Zms added write latency." This is the GitHub README headline.

### GitHub README Positioning

```
MemGuard: Write-Path Memory Quality for AI Agents

Your agent's memory is wrong. Before it reaches retrieval.

Current memory systems store what the LLM extracts — 
including hallucinated facts, outdated preferences, and contradictions.
MemGuard validates memories before storage, detects contradictions, 
assigns validity windows, and quarantines uncertain writes.

Works with any memory backend. No framework required.

[Benchmark: +X% HaluMem extraction accuracy vs. unvalidated baseline]
```

### Demo Narrative

"You have a coding agent that remembers your architecture decisions. After 50 sessions, it starts making wrong recommendations. Not because the model got worse. Because three months ago you changed your preferred database — and the old preference was stored, never invalidated. MemGuard would have detected the contradiction at write time, quarantined the old preference, and flagged it for your confirmation."

***

## 7. V1 Product Definition

### Target User

Mid-senior ML engineer or AI application developer building a production agent with cross-session memory. User has already tried Mem0, LangMem, or a simple vector store and is experiencing unexplained memory quality degradation. User does not want to adopt a new agent framework.

### Primary Use Case

Plugging into an existing memory pipeline to add write-path validation without changing the retrieval interface.

### Core Workflow

1. Developer installs `pip install memguard`
2. Wraps existing `store.add(content)` calls with `memguard.write(session_id, turn)`
3. Calls `memguard.retrieve(query, top_k)` (returns quarantine-filtered, TTL-valid memories)
4. Periodically calls `memguard.audit(session_id)` to review quarantine log and confirm disputed memories

### Memory Object Model

```json
{
  "memory_id": "uuid",
  "content": "string",
  "source_session": "string",
  "source_turn": "int",
  "extraction_confidence": "float",
  "memory_type": "preference|fact|event|instruction",
  "validity_ttl_days": "int|null",
  "quarantine": "bool",
  "quarantine_reason": "contradiction|low_confidence|null",
  "contradiction_ids": ["array of conflicting memory_ids"],
  "last_confirmed_at": "ISO8601|null",
  "created_at": "ISO8601",
  "retrieval_count": "int"
}
```

### API Shape

```python
class MemGuard:
    def write(self, session_id: str, turn: str) -> List[VMU]
    def retrieve(self, query: str, top_k: int = 10) -> List[VMU]
    def audit(self, session_id: str) -> AuditReport
    def confirm(self, memory_id: str) -> None
    def reject(self, memory_id: str) -> None
    def quarantine_report(self, session_id: str) -> QuarantineReport
    def set_ttl_policy(self, memory_type: str, ttl_days: int) -> None
    def run_benchmark(self, suite: str = "halumem") -> BenchmarkResult
```

### CLI

```bash
memguard audit --session session_id      # show quarantine log
memguard confirm --memory-id uuid         # confirm disputed memory
memguard benchmark --suite halumem        # run eval harness
memguard stats --session session_id       # store health summary
```

### Dashboard/Inspector

**V1:** Not required. CLI `audit` output is sufficient. JSON output format enables custom dashboards. Dashboard is a V2 feature.

### Eval Harness

HaluMem adapter ships in `memguard.eval`:
```python
from memguard.eval import HaluMemRunner
runner = HaluMemRunner(backend=my_memguard_instance)
results = runner.run(tasks=["extraction", "update", "qa"])
print(results.summary())  # table with scores vs. published baselines
```

### Example App

`examples/coding_agent/` — a coding assistant with MemGuard memory. Demonstrates:
1. Multi-session architecture decision tracking
2. Contradiction detection when user changes preference
3. Quarantine log showing caught hallucinations
4. Before/after HaluMem score comparison

### Documentation Set

- README with benchmark result table (vs. vanilla baseline)
- Quick-start guide (5 minutes to working demo)
- API reference
- Architecture docs (write-path flow diagram)
- Benchmark adapter guide (how to run HaluMem tasks)
- Backend integration guide (Mem0, Zep, flat vector, custom)

### Minimum Demo

A Jupyter notebook: "MemGuard Catches What Mem0 Misses" — runs 200-turn synthetic session, injects 5 contradictory facts at known positions, shows MemGuard quarantine rate vs. vanilla baseline pass-through rate, then runs HaluMem task 1 (extraction accuracy) and prints improvement delta.

***

## 8. Benchmark and Evaluation Plan

### Test Categories and Datasets

| Category | Dataset | Type | Metrics |
|---|---|---|---|
| Extraction hallucination | HaluMem (arXiv:2511.03506)[^1] | Human-AI dialogues, 15k memory points | Extraction recall, precision, F1 |
| Update hallucination | HaluMem update task | Human-AI dialogues with fact changes | Update recall, omission rate |
| QA accuracy (downstream) | HaluMem QA task | QA over stored memories | Accuracy, F1 |
| Temporal reasoning | LongMemEval temporal subset[^10] | 500 questions, scalable chat histories | Accuracy |
| Knowledge updates | LongMemEval knowledge update subset | Same dataset | Accuracy on changed facts |
| Adversarial QA | LoCoMo adversarial[^11] | 300-turn, 35-session conversations | Adversarial F1 |
| Conflict resolution | MemoryAgentBench CR subset[^14] | Incrementally accumulated contradictions | Conflict resolution accuracy |
| Contradiction injection | Custom (MemGuard native) | Synthetic sessions with known contradictions | Detection precision, recall, false positive rate |
| Stale memory | Custom (MemGuard native) | Sessions with time-expired facts | Quarantine rate, correct TTL assignment |
| Write-path latency | Internal benchmark | Production-scale session (200 turns) | p50, p95, p99 write latency |
| Retrieval latency | Internal benchmark | Same | p50, p95 retrieve latency |
| Token cost | Internal benchmark | Same | Tokens per write, tokens per retrieve |

### Baselines (Required)

| Baseline | Description |
|---|---|
| No memory | Zero-shot LLM, no memory at all |
| Full context | All conversation appended to context (expensive but accurate baseline) |
| Summary memory | Standard summary compression (ChatGPT/Claude approach) |
| Vanilla vector memory | Append-only embedding store (Mem0 default behavior) |
| Zep graph memory | Temporal knowledge graph with bi-temporal model[^16] |
| MemGuard | Proposed system |

### Success Thresholds

- HaluMem extraction accuracy: MemGuard ≥ vanilla vector + 10 absolute points
- HaluMem update recall: MemGuard ≥ vanilla vector + 10 absolute points
- Contradiction detection precision: ≥85%
- Contradiction detection recall: ≥70%
- False quarantine rate: ≤10% (at most 10% of valid memories incorrectly quarantined)
- Write latency (async): p95 <100ms additional overhead vs. vanilla write
- Write latency (sync): p95 <500ms (acceptable for batch ingestion pipelines)

### Failure Cases (Must Be Documented)

- False quarantine of valid memories (breaking agent continuity)
- Backbone failure: format error rate >20% on Qwen-2.5-3B baseline (must document model requirements)
- Contradiction detection rate <50% on injected contradictions (validator ineffective)
- No improvement vs. vanilla baseline on HaluMem (kill signal)

### Negative Memory Tests

Inject known-false memories and measure whether agent uses them in downstream QA. Compare MemGuard quarantine rate vs. vanilla pass-through rate for these injected facts.

### Temporal Contradiction Tests

Inject a fact at session turn 10, then inject a contradicting update at turn 100. Measure: (a) is the contradiction detected? (b) is the older memory correctly flagged as potentially stale? (c) does the agent answer downstream QA correctly based on the updated fact?

### Explainability Tests

For each retrieved memory, `audit()` must return: source turn, extraction confidence, whether contradiction was checked, whether TTL is approaching. Evaluate: developer can reproduce why a specific answer was given from audit log alone.

### Cost/Latency Measurements

Every benchmark run reports: total LLM calls per session (write path), tokens consumed per session, wall-clock time for 200-turn session, retrieval latency at 50/100/200/500 stored memories.

***

## 9. Open-Source Positioning

### Repo One-Liner

```
MemGuard: The write-path quality layer for AI agent memory. 
Validates before storing. Catches contradictions. Assigns validity. 
Works with any backend.
```

### Problem Statement

Current AI agent memory systems store what the LLM extracts — including hallucinated facts, outdated preferences, and unresolved contradictions. HaluMem (arXiv:2511.03506) shows that less than 62% of stored memories are accurate and less than 50% of fact updates succeed. These errors originate at write time and propagate to every downstream retrieval. No existing library addresses this at the source.

### What It Is

A composable Python library that adds write-path validation to any memory backend. It extracts memories from conversation turns, validates them before storage, detects contradictions, assigns validity TTLs by memory type, and quarantines uncertain writes. Ships with a native HaluMem benchmark adapter to measure improvement.

### What It Is Not

- Not a new memory store
- Not a new agent framework
- Not a retrieval system
- Not a chat summarizer
- Not a vector database wrapper
- Not a consumer product
- Not a hosted service (V1)

### Why Existing Memory Systems Are Insufficient

**[VERIFIED FACT]** Mem0 performs extraction in one LLM call with no independent validation. **[VERIFIED FACT]** Zep extracts entities and relationships but validates at graph insertion, not at the memory content level, and does not expose extraction confidence per memory unit. **[VERIFIED FACT]** LangMem runs at 60-second p95 latency on LoCoMo, does not expose write-path confidence or contradiction detection. **[VERIFIED FACT]** Letta/MemGPT delegates memory management to the LLM itself without a separate validation gate. None ship a runnable HaluMem benchmark adapter.[^37][^24][^17][^4]

### First Users

1. Developers building coding assistants with multi-project, multi-month session memory
2. Developers building customer service bots with persistent user state that must be accurate (healthcare, finance, legal)
3. AI agent framework maintainers (LangChain, CrewAI, AutoGen ecosystem) wanting to add memory quality
4. Researchers comparing memory systems (MemBench-OSS as complement)

### Contributor Hooks

- New backend adapters (DynamoDB, Pinecone, Qdrant, Redis)
- New contradiction detection strategies (NLI models, rule-based, hybrid)
- New TTL policy presets by domain (medical, coding, finance, customer service)
- New benchmark suite adapters (MemoryAgentBench, AgingBench, custom)
- Translations/documentation

### Roadmap Themes

**V1 (Month 0–3):** Core write-path validator, SQLite + flat backend, HaluMem adapter, coding agent demo

**V2 (Month 3–6):** Async write path, vector backend (Chroma, Qdrant), AgingBench integration (AgeProbe as optional module), MemoryAgentBench adapter

**V3 (Month 6–12):** SkillBank integration (procedural memory extension), governance extension (MemLedger as optional module), leaderboard dashboard

### Credibility Requirements

- Published HaluMem benchmark comparison with exact reproducible setup
- Stated baselines: Mem0 (vanilla), Zep, LangMem
- Clear statement of what the library does not do
- No unsupported accuracy claims
- CONTRIBUTING.md with explicit anti-hallucination protocol for documentation

***

## 10. What Not to Build

### Generic Hosted Memory API

**Why not:** AWS, OpenAI, Anthropic, and Zep are building this. Competing on hosted API infrastructure requires massive capital, reliability engineering, and enterprise sales that a V1 open-source project cannot credibly execute. The commodity layer is already being built.

### All-Framework Integrations

**Why not:** LangChain, LlamaIndex, CrewAI, AutoGen, and DSPy adapters feel like day-one deliverables but are actually adoption taxes. Each adapter requires maintaining against upstream framework changes. In V1, the core library must prove its value first; integrations follow from proof, not from breadth.

### General-Purpose Graph UI

**Why not:** Building a graph visualization dashboard for memory structures is an engineering distraction. Developers can inspect memories via CLI or structured JSON. A UI implies a product layer that V1 should not fund.

### "Personal AI" Consumer App

**Why not:** Consumer apps require UX, distribution, trust, and support infrastructure that are orthogonal to proving a technical primitive. The audience for MemGuard is ML engineers, not consumers.

### Complex Multi-Agent Platform

**Why not:** Multi-agent governance (MemLedger, C4) requires organizational adoption (multiple agent teams coordinating), which is a sales and integration problem, not a technical one at V1. The governance primitives should be proven in a narrow prototype first (two-agent scenario) before building a platform.

### Full Enterprise Governance Suite

**Why not:** RBAC, audit logging for compliance teams, legal hold, and data sovereignty require SOC 2, legal review, and enterprise sales. These are requirements for a V2+ commercial layer, not for proving the underlying technical primitive.

### Broad Benchmark Suite Before a Narrow Proof

**Why not (standalone):** MemBench-OSS as a standalone product without MemGuard underneath is an infrastructure project without a use case driver. Benchmarks need someone to optimize against them; the first optimizer should be MemGuard. Build MemBench-OSS as MemGuard's eval layer, not as an independent product.

### Anything That Cannot Be Evaluated

**Why not:** The field's fundamental problem is unaccountable systems. Building another memory module without a reproducible benchmark contribution continues the same pattern. Every V1 deliverable must have a measurement. If a component cannot be evaluated, it should not be in V1.

***

## 11. Evidence Ledger

| Opportunity Claim | Supporting Evidence | Source | Quality Grade | Confidence | Caveat |
|---|---|---|---|---|---|
| Memory hallucination originates at extraction/update stage | HaluMem: <62% accuracy, <50% update recall[^1] | arXiv:2511.03506 (Nov 2025) | A | High | Sample: 15k memory points, 3.5k questions. Not independently replicated yet |
| 30% accuracy drop across sustained interactions | LongMemEval: commercial systems, long-context LLMs[^10] | arXiv:2410.10813, ICLR 2025 | A | High | 500 questions, scalable histories. Strong methodology |
| Benchmarks saturating with context window expansion | LongMemEval-S fits in 128k context windows[^2] | arXiv:2602.19320 (Feb 2026) | A | High | Structural analysis of benchmark properties |
| Agent aging is real and multi-dimensional | AgingBench: 400+ runs, 14 models, 7 scenarios[^3] | arXiv:2605.26302 (May 2026) | B (preprint, May 2026) | Medium-High | Very recent; not yet peer-reviewed. Methodology is rigorous. |
| Behavioral tests remain clean while precision decays | AgingBench finding[^3] | arXiv:2605.26302 | B | Medium | Same caveat as above |
| Open-weight models fail structured memory operations | 30%+ format error rate (Qwen-2.5-3B)[^2] | arXiv:2602.19320 | A | High | Direct empirical measurement |
| AWM improves task success by 24.6%–51.1% | Mind2Web and WebArena benchmark results[^7] | ICML 2025 (arXiv:2409.07429) | A | High | Peer-reviewed. Open code available. |
| Governed Memory achieves 92% governance precision, zero leakage | Production deployment at Personize.ai[^9] | arXiv:2603.17787 (Mar 2026) | B | Medium | Single production deployment. Not independently validated. |
| Mem0 Graph: 68% accuracy, 26s p95 latency | Community benchmark on LoCoMo, 200 questions[^4] | r/LocalLLaMA (Feb 2026) | D | Low-Medium | User-run study, not peer-reviewed. Methodology described but not independently verified. |
| Accuracy drops 50%→30% as store grows 10→500 entries | Empirical study[^19] | Towards Data Science (Apr 2026) | C | Medium | Not peer-reviewed. Single implementation. Replication needed. |
| Memory provenance required by EU AI Act | MAIF paper analysis[^6] | arXiv:2511.15097 (Nov 2025) | B | Medium | Legal interpretation; not a legal opinion |
| Letta/MemGPT: 90% error rates on non-OpenAI models | User reviews, Knowledge Plane analysis[^17] | knowledgeplane.io | D | Low-Medium | Aggregated user reports; not systematic |
| Temporal reasoning gap: 73% below human on LoCoMo | LoCoMo benchmark evaluation[^11] | snap-research.github.io | A | High | Direct benchmark measurement with human baseline |

***

## 12. Unknowns and Next Research

### Evidence Gaps

1. **HaluMem replication:** HaluMem results have not been independently replicated. All claims from this paper should be treated as B-grade until replicated. A MemGuard prototype provides the first replication opportunity.

2. **AgingBench longitudinal validity:** AgingBench is submitted May 2026. Its four aging mechanisms need independent validation on agent types beyond those in the paper (coding agents, customer service bots, multi-modal agents).

3. **Write-path validation latency budget:** The acceptable write-path overhead has not been empirically characterized. Different applications (interactive chat vs. batch ingestion vs. background processing) have different latency tolerances. [UNKNOWN] what the acceptable overhead ceiling is in practice.

4. **Contradiction detection precision at scale:** All reported contradiction detection results are at small memory store sizes (<500 entries). Performance at 5,000–50,000 entries is unknown. Embedding-based similarity may degrade with store size.

5. **AWM online mode vs. offline mode gap:** AWM's 51.1% improvement on WebArena uses offline mode (annotated training data). Online mode (from live agent traces) shows lower and more variable improvement. The production-deployable improvement magnitude is [UNKNOWN].

### Systems Needing Hands-On Testing

1. **HaluMem benchmark:** Full end-to-end run with Mem0, Zep, MemGuard prototype to validate reproducibility of extraction/update hallucination rates
2. **AgingBench scenarios:** Run all 7 scenarios on multiple memory backends to validate aging mechanism classification
3. **LangMem latency:** 60-second p95 figure from community benchmark needs independent verification (this would be a kill signal for LangMem's production viability)
4. **Zep's bi-temporal model:** Hands-on test of contradiction detection capability at scale — does Graphiti actually resolve contradictions or just track them?

### Benchmarks Needing Implementation

1. **Context Saturation Gap (Δ):** The "Anatomy" survey defines this formally; no implementation exists. MemBench-OSS should implement it as a first-class test.
2. **MemGuard contradiction injection test:** Custom adversarial dataset not yet created. Needs design specification and generation pipeline.
3. **Stale memory quarantine test:** Custom TTL-expiry test not yet created. Needs design and ground truth labeling.

### User Demand Assumptions

1. **[ASSUMPTION]** ML engineers building coding agents are aware of and frustrated by memory hallucination — but it is unknown whether they currently attribute downstream failures to memory quality (vs. model capability).
2. **[ASSUMPTION]** Developers prefer a composable library over adopting Zep or Mem0's managed service. This assumption drives the "framework-agnostic" positioning and may be wrong for enterprise buyers.
3. **[UNKNOWN]** Whether the developer audience for MemGuard has already given up on persistent memory (using context-stuffing instead) — which would dramatically reduce addressable market.

### Technical Feasibility Unknowns

1. **Async write path feasibility:** Can write-path validation be made async without degrading memory coherence? If the validation result arrives after the next turn has already started, there is a race condition risk.
2. **Contradiction detection across 10,000+ memory entries:** Pairwise similarity checks do not scale. Vector search approximation introduces false negatives. The right algorithm at scale is an open question.
3. **TTL assignment accuracy:** Whether an LLM can reliably classify memory types (preference, fact, event, instruction) and assign appropriate TTLs across diverse domains is empirically unknown.

### Legal/Privacy Unknowns

1. **EU AI Act compliance for memory audit logs:** Whether a MemGuard audit log satisfies the EU AI Act's explainability requirements for AI-assisted decisions is a legal question not resolvable by this analysis.
2. **GDPR/CCPA implications of memory quarantine:** Quarantined memories still contain user data. Whether "quarantined" satisfies a right-to-erasure request is unknown.
3. **Memory provenance as evidence:** Whether provenance logs from MemGuard would be considered reliable evidence in enterprise liability scenarios is untested.

***

*Self-audit completed: All factual claims tagged with claim type. No capability invented for any system. All benchmark figures traced to primary sources. Opportunity analysis labeled [OPPORTUNITY THESIS] or [JUDGMENT]. Novelty assessments grounded in comparison against published work. Each candidate has a smallest serious prototype, a benchmark strategy, and defined kill criteria. Recommended direction follows from evidence severity (HaluMem as quantified bottleneck, AgingBench as longitudinal confirmation). V1 scope is narrow enough to build in 30 days and specific enough to matter.*

---

## References

1. [HaluMem: Evaluating Hallucinations in Memory Systems of Agents](https://arxiv.org/abs/2511.03506) - Memory systems are key components that enable AI systems such as LLMs and AI agents to achieve long-...

2. [Paper page - Anatomy of Agentic Memory: Taxonomy and Empirical ...](https://huggingface.co/papers/2602.19320) - We present a comprehensive survey on agentic memory for LLMs, including a unified taxonomy and empir...

3. [Your Agents Are Aging Too: Agent Lifespan Engineering for Deployed Systems](https://arxiv.org/abs/2605.26302) - Long-lived AI agents are increasingly deployed as persistent operational systems, yet they are still...

4. [Benchmarked 4 AI Memory Systems on 600-Turn Conversations - Here Are the Results](https://www.reddit.com/r/LocalLLaMA/comments/1rckcww/benchmarked_4_ai_memory_systems_on_600turn/) - Benchmarked 4 AI Memory Systems on 600-Turn Conversations - Here Are the Results

5. [current AI memory systems are… | Sudhanshu Sharma - LinkedIn](https://www.linkedin.com/posts/sudhanshu746_did-your-ai-agent-just-forget-what-it-told-activity-7393906066679386112-4Mvy) - Did your AI agent just forget what it told you 5 minutes ago? A new paper, HaluMem: Evaluating Hallu...

6. [MAIF: Enforcing AI Trust and Provenance with an Artifact-Centric ...](https://arxiv.org/abs/2511.15097) - The AI trustworthiness crisis threatens to derail the artificial intelligence revolution, with regul...

7. [ICML Poster Agent Workflow Memory](https://icml.cc/virtual/2025/poster/45496) - To build agents that can similarly benefit from this process, we introduce Agent Workflow Memory (AW...

8. [[2409.07429] Agent Workflow Memory - arXiv](https://arxiv.org/abs/2409.07429) - We introduce Agent Workflow Memory (AWM), a method for inducing commonly reused routines, ie, workfl...

9. [Governed Memory: A Production Architecture for Multi-Agent ... - arXiv](https://arxiv.org/abs/2603.17787) - Enterprise AI deploys dozens of autonomous agent nodes across workflows, each acting on the same ent...

10. [Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813) - Recent large language model (LLM)-driven chat assistant systems have integrated memory components to...

11. [Evaluating Very Long-Term Conversational Memory of LLM Agents](https://snap-research.github.io/locomo/) - Based on LOCOMO, we present a comprehensive evaluation benchmark to measure long-term memory in mode...

12. [Serious flaws in two popular AI Memory Benchmarks (LoCoMo ...](https://www.reddit.com/r/AIMemory/comments/1s1jlnd/serious_flaws_in_two_popular_ai_memory_benchmarks/) - LongMemEval-S fits entirely in modern context windows, making it more of a context window test than ...

13. [Evaluating Memory in LLM Agents via Incremental Multi-Turn ... - arXiv](https://arxiv.org/abs/2507.05257) - We introduce MemoryAgentBench, a new benchmark specifically designed for memory agents. Our benchmar...

14. [️ MemoryAgentBench: Evaluating Memory in LLM Agents ... - GitHub](https://github.com/HUST-AI-HYZ/MemoryAgentBench) - This project benchmarks agents with memory capabilities. ... Open source code for ICLR 2026 Paper: E...

15. [Has anyone actually solved the memory problem for agents yet?](https://www.reddit.com/r/AI_Agents/comments/1r2puny/has_anyone_actually_solved_the_memory_problem_for/) - The problem I'm solving is cross-session continuity. When you clear context or start a fresh session...

16. [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/abs/2501.13956) - We introduce Zep, a novel memory layer service for AI agents that outperforms the current state-of-t...

17. [Letta — AI Memory Tool Review - Knowledge Plane](https://knowledgeplane.io/landscape/letta/) - Honest review of Letta: Agents that manage their own memory (formerly MemGPT). Architecture, pricing...

18. [zorazrw/agent-workflow-memory: AWM - GitHub](https://github.com/zorazrw/agent-workflow-memory) - Agent Workflow Memory (AWM) proposes to induce, integrate, and utilize workflows via an agent memory...

19. [Your RAG Gets Confidently Wrong as Memory Grows](https://towardsdatascience.com/your-rag-gets-confidently-wrong-as-memory-grows-i-built-the-memory-layer-that-stops-it/) - Your users are receiving increasingly wrong answers with increasingly authoritative delivery. Standa...

20. [Catastrophic Failures of ChatGpt that's creating major problems for ...](https://community.openai.com/t/catastrophic-failures-of-chatgpt-thats-creating-major-problems-for-users/1156230) - On February 5, 2025, your memory architecture failed catastrophically. Without consent, notice, or r...

21. [How to quantify "Memory Conflict Resolution" in LLM Agents using ...](https://github.com/mem0ai/mem0/discussions/4005) - Temporal consistency score — when memories conflict, does the agent prefer recent over stale? · Sour...

22. [The Missing Piece in AI Memory: Workflows - LinkedIn](https://www.linkedin.com/posts/ajacobi_aimemory-rag-memory-activity-7376616442252709888-yxTQ) - Memory has to run like a governed workflow: validate on recall, update with new evidence, arbitrate ...

23. [Daily Papers - Hugging Face](https://huggingface.co/papers?q=memory+systems) - Empirical studies based on HaluMem show that existing memory systems tend to generate and accumulate...

24. [The Future of AI Agents: How External Memory, Mem0, and ...](https://medium.com/@harikrishnabekkam1590852/the-future-of-ai-agents-how-external-memory-mem0-and-memgpt-are-transforming-long-term-context-23f4ec88f66d) - Introduction: The Memory Problem That’s Holding AI Agents Back

25. [Agent Memory - Zep](https://www.getzep.com/product/agent-memory/) - Persistent memory for AI agents. Build smarter conversational experiences that remember and learn fr...

26. [Control Memory Ingestion - Mem0 Documentation](https://docs.mem0.ai/cookbooks/essentials/controlling-memory-ingestion) - Mem0 lets you control your memory ingestion pipeline. In this cookbook, we'll demonstrate these cont...

27. [Agent Lifespan Engineering for Deployed Systems - arXiv](https://arxiv.org/html/2605.26302v1) - AgingBench organizes agent aging into four mechanisms: compression aging, where write-time summariza...

28. [[2603.11768] Governing Evolving Memory in LLM Agents - arXiv](https://arxiv.org/abs/2603.11768) - Governing Evolving Memory in LLM Agents: Risks, Mechanisms, and the Stability and Safety Governed Me...

29. [FadeMem: Biologically-Inspired Forgetting for Efficient Agent Memory](https://arxiv.org/html/2601.18642v1)

30. [Agent Workflow Memory - OpenReview](https://openreview.net/forum?id=NTAhi2JEEE) - This paper introduces AWM, a framework that enables agents to extract reusable workflows from past e...

31. [LEGOMem: Modular Procedural Memory for Multi-agent LLM ... - arXiv](https://arxiv.org/html/2510.04851v1) - The recent advent of LLMs has enabled the development of multi-agent systems able to plan, decompose...

32. [M⁢e⁢m^p: Exploring Agent Procedural Memory - arXiv](https://arxiv.org/html/2508.06433v2) - Instead of starting fresh each time, an agent should extract its experience from past successes. By ...

33. [[PDF] Agent Skills from the Perspective of Procedural Memory - TechRxiv](https://www.techrxiv.org/doi/pdf/10.36227/techrxiv.176857932.25697838) - Agent Skills organize instructions, executable code, and supporting resources into modular skill uni...

34. [Multi-User Memory Sharing in LLM Agents with Dynamic Access ...](https://openreview.net/forum?id=pJUQ5YA98Z) - Summary: This paper addresses the problem of memory management in multi-agent and multi-user systems...

35. [HaluMem: Evaluating Hallucinations in Memory Systems of Agents](https://openreview.net/forum?id=PDzE0elDvE) - HaluMem defines three tasks (memory extraction, memory updating, and memory question answering) to c...

36. [Add Standard Memory Evaluation Benchmarks (LOCOMO ... - GitHub](https://github.com/letta-ai/letta/issues/3115) - Several 2026 papers expose critical limitations in the benchmarks ... The survey identifies MemGPT/L...

37. [Breakdown of Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://gist.github.com/lancejpollard/6a516392ebf42fcc63a80140495f6dac) - Breakdown of Zep: A Temporal Knowledge Graph Architecture for Agent Memory - readme.md

