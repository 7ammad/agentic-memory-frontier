# Report 3: Top Player System Archaeology — Agent Memory Landscape 2026

> **Research Date:** May 27, 2026
> **Evidence Protocol:** Every material claim is grounded in a sourced artifact. Labels used throughout: [VERIFIED FACT], [AUTHOR/VENDOR CLAIM], [USER-REPORTED ISSUE], [INFERENCE], [JUDGMENT], [UNKNOWN]. Source-quality grades: A = official docs / repo / paper; B = official blog / arXiv preprint with code; C = product page / roadmap / community; D = Reddit / HN / secondary review.

---

## 1. Executive Summary

**The 15 Strongest Evidence-Grounded Findings**

1. **Hybrid retrieval (vector + keyword) is the dominant write-then-retrieve pattern.** LongMemEval-S benchmarks show BM25+vector hybrid achieves ~95.2% R@5, versus 86.2% BM25-only — confirming neither alone is adequate [VERIFIED FACT, A].

2. **Memory hallucination is a production-grade crisis, not an edge case.** HaluMem (arXiv:2511.03506, ICLR 2025) shows memory extraction recall stays below 60%, and end-to-end QA accuracy tops out near 56% because hallucinations accumulate during extraction *and* updating, then cascade into retrieval [VERIFIED FACT, A].

3. **Temporal reasoning is the hardest retrieval category on every benchmark.** LoCoMo, LongMemEval, and MemoryAgentBench all show temporal-reasoning questions produce the largest accuracy gap compared to human performance (reported as 73% gap on LoCoMo) [VERIFIED FACT, A].

4. **Multi-agent memory consistency is formally unsolved.** A March 2026 position paper (arXiv:2603.10062) frames this as a computer-architecture problem and identifies two missing protocols: cache-sharing and memory-access-control. No existing production framework (LangGraph, CrewAI, AutoGen) implements formal consistency models [VERIFIED FACT, A].

5. **Memory poisoning is a present, not hypothetical, risk.** Multiple security researchers confirm that incorrect or adversarially injected information in long-lived agent memory persists, influences future decisions, and is invisible to traditional monitoring layers [VERIFIED FACT, B].

6. **Zep deprecated its Community Edition (self-hosted open-source) in April 2025.** Free self-hosting is now only available as enterprise BYOC. Graphiti (the temporal knowledge-graph engine) remains Apache 2.0 open source [VERIFIED FACT, A].

7. **Mem0 is the most widely adopted open-source memory framework by download and API volume**, with 56,000+ GitHub stars, 186 million API calls in Q3 2025, and exclusive AWS Agent SDK integration [AUTHOR/VENDOR CLAIM, B]. Graph memory is paywalled at $249/month Pro tier [VERIFIED FACT, C].

8. **All four major commercial assistants (ChatGPT, Claude, Gemini, Microsoft Copilot) launched explicit memory features in 2024–2025**, converging on: explicit saves + automatic extraction, user visibility/deletion controls, temporary/incognito mode, and default-on with opt-out [VERIFIED FACT, A].

9. **LangGraph's BaseStore is the most composable open memory primitive for framework builders.** Semantic search was added in April 2026; MongoDB, Postgres, and Redis stores are available. It does not implement memory policies, only storage/retrieval primitives [VERIFIED FACT, A].

10. **ChatGPT memory generates persistent and recurring user complaints** across unreliable saves, stale recall, excessive writes, and complete memory loss after model updates — documented in OpenAI forums with hundreds of corroborating replies [USER-REPORTED ISSUE, C].

11. **Memory evaluation is a fragmented landscape with no universal standard.** A December 2025 survey (arXiv:2512.13564) explicitly states the field "has become increasingly fragmented" and existing terminologies "obscure conceptual clarity" [VERIFIED FACT, A].

12. **No production memory system exposes a documented, structured provenance model.** Security literature and governance researchers identify provenance as missing in all major frameworks [JUDGMENT based on VERIFIED FACT].

13. **Supermemory's "#1 on LongMemEval" claim uses pass@8 (oracle), not single-agent accuracy.** LinkedIn analysis identified this benchmark framing as pass@8 over 14–18 LLM calls per query, not production accuracy [USER-REPORTED ISSUE, D]. The claim is [AUTHOR/VENDOR CLAIM] pending independent replication.

14. **The Zep/Graphiti temporal knowledge graph architecture (nodes, edges, time-stamped episodes) is the closest production implementation of structured temporal memory**, but users report disconnected nodes, blank entities, and ingestion latency issues at scale [USER-REPORTED ISSUE, C].

15. **Framework lock-in is becoming acute.** AI agent ecosystem fragmentation is worsening in early 2026, with memory formats, session-state representations, and retrieval semantics all diverging across vendors [VERIFIED FACT, B].

---

## 2. System Inclusion Criteria

**Definition:** For this report, a "memory system" is any system that provides at least one of the following capabilities in a documented, deployable manner:

| Category | Definition | Distinction |
|----------|------------|-------------|
| **Agent memory system** | Persists facts, preferences, or events across agent sessions | Not just session state; survives session termination |
| **RAG / vector store** | Retrieves relevant text chunks by embedding similarity | Included only when used as a memory substrate, not standalone document search |
| **Graph memory** | Stores entities and relationships as nodes/edges for structured retrieval | Temporal graphs (Graphiti) are distinct from static GraphRAG |
| **Checkpointing / state persistence** | Serializes agent execution state to resume interrupted workflows | Distinct from long-term memory; session-scoped by design |
| **User personalization memory** | Stores explicit user preferences or facts for personalization | Distinguished from general knowledge retrieval |
| **Long-context management** | Compresses or manages context window to simulate extended memory | MemGPT/Letta paging model is the canonical example |
| **Commercial assistant memory** | User-facing memory in consumer/enterprise AI products | Implementation details largely opaque to external verification |
| **Framework-level memory abstraction** | A storage + retrieval API that other systems build on | LangGraph BaseStore, Semantic Kernel VectorStoreTextSearch |

**Exclusions:** Systems included only if they expose documented memory *primitives* beyond a pure retrieval index. Pure vector databases without memory policy (Qdrant, Weaviate, Milvus standalone) are substrates, not memory systems; they are referenced where they serve as storage backends.

---

## 3. System Register

| System | Organization | Type | Grade | Memory Type | Maturity Signal | Evidence Limits |
|--------|-------------|------|-------|-------------|-----------------|-----------------|
| **MemGPT / Letta** | UC Berkeley → Letta Inc | OSS + commercial | A | Hierarchical virtual context (in-context + archival) | arXiv Oct 2023; 16.4K+ stars; Letta Cloud platform | Commercial platform partially opaque |
| **Graphiti** | Zep Inc | OSS (Apache 2.0) | A | Temporal KG (episodes, nodes, edges, bi-temporal) | 20K stars Nov 2025; MCP Server 1.0 | Contradiction resolution algorithm undocumented |
| **Zep Cloud** | Zep Inc | Commercial SaaS | A | Temporal KG via Graphiti + vector | SOC 2 Type II; CE deprecated Apr 2025 | CE defunct; internal KG dedup logic undocumented |
| **Mem0** | Mem0 Inc (YC) | OSS + commercial | A | Hybrid vector + graph (graph = Pro paywall) | 56K+ stars; $24M raised; 186M API calls Q3 2025 | Graph memory paywalled; dedup opacity |
| **LangGraph BaseStore** | LangChain Inc | OSS | A | Key-value + semantic search (Apr 2026) | Production LangGraph Platform; MongoDB/Postgres | No memory policy — primitive only |
| **LangMem** | LangChain Inc | OSS | A | Episodic + semantic + procedural extraction | Official docs; MongoDB integration | Limited independent adoption evidence |
| **Letta Context Repos** | Letta Inc | OSS + commercial | B | Git-backed versioned memory for coding agents | Feb 2026 launch post | New; limited production evidence |
| **Supermemory** | Supermemory Inc | OSS + commercial | B | Fact extraction + hybrid search + user profiles | Claims #1 LongMemEval — methodology disputed | Benchmark self-reported; no 3rd-party replication |
| **CrewAI Memory** | CrewAI Inc | OSS (MIT) | A | Short-term + long-term (ChromaDB RAG) + entity | Active repo; documented bugs | Chroma dependency fragile; no native graph |
| **AutoGen Memory** | Microsoft | OSS (MIT) | A | Pluggable memory component (v0.4+) | GitHub Issue #4264 tracks first-class memory | Memory maturity unclear; version fragmentation |
| **LlamaIndex Agent Memory** | LlamaIndex Inc | OSS | A | Vector memory + composable memory | Improved memory blog May 2025 | No temporal model; session-scoped default |
| **Semantic Kernel Memory** | Microsoft | OSS (MIT) | A | TextMemoryPlugin + VectorStoreTextSearch | Official MS docs; function-calling gap acknowledged | TextMemoryPlugin historically limited |
| **Haystack Memory** | deepset | OSS (Apache 2.0) | A | InMemoryChatMessageStore (experimental, session-only) | Haystack 2.0 architecture; active issues | No long-term memory primitive |
| **Cognee** | topoteretes | OSS | B | KG + vector control plane | Graphiti integration; Redis integration | Limited production adoption signal |
| **ChatGPT Memory** | OpenAI | Commercial (closed) | A | Saved memories + full conversation history (Apr 2025) | GA Plus users; recurring complaints | Internal architecture undocumented |
| **Claude Memory** | Anthropic | Commercial (closed) | A | Project-scoped memory; explicit saves | GA Pro/Max Oct 2025; Teams Sep 2025 | Architecture opaque; no API for primitives |
| **Gemini Memory** | Google | Commercial (closed) | A | Automatic past-chat + explicit user profile | Rolled out Aug 2025; Enterprise docs | Privacy model vague; 24h disconnect delay |
| **Microsoft Copilot Memory** | Microsoft | Commercial (closed) | A | Explicit preference capture; Entra ID work profile | GA July 2025; admin Graph API controls | No cross-app memory; Copilot Chat only |
| **OpenAI Assistants API** | OpenAI | Commercial API | A | Thread-scoped history + file search vector store | 10K file hard limit confirmed | No cross-thread long-term memory API |

---

## 4. System Deep Dives

### 4.1 MemGPT / Letta

**What it is:** MemGPT (arXiv:2310.08560, UC Berkeley, Oct 2023) introduced "virtual context management" — an OS-inspired paging model giving LLMs the illusion of unbounded context via hierarchical memory tiers [VERIFIED FACT, A]. The project renamed to Letta in 2024 and became a commercial platform with an Agent Development Environment (ADE) for visual debugging [VERIFIED FACT, A].

**Memory primitive:** Three tiers — (1) in-context working memory (main context), (2) archival storage (external database, vector-searchable), (3) recall/conversation history. The agent itself decides what to page in/out via function calls [VERIFIED FACT, A].

**Memory write mechanism:** LLM-driven — the agent generates function calls (`archival_memory_insert`, `core_memory_replace`) to write to external storage [VERIFIED FACT, A].

**Memory retrieval mechanism:** Keyword search and embedding-based semantic search against archival storage [VERIFIED FACT, A].

**Update/delete/forget:** `core_memory_replace` overwrites working memory block content. Archival entries can be searched and deleted via function call [VERIFIED FACT, A].

**Temporal handling:** Timestamps attached to archival entries. No formal temporal contradiction resolution — recency is inferred, not enforced [INFERENCE].

**Provenance handling:** No documented provenance model. Source of archival entries is not tracked by default [INFERENCE].

**Privacy/trust model:** Data stored in user-controlled databases. Letta Cloud stores agent state [AUTHOR/VENDOR CLAIM, C].

**Multi-agent support:** Conversations feature (Jan 2026) enables shared agent memory across concurrent agents [AUTHOR/VENDOR CLAIM, B]. No formal consistency model documented [INFERENCE].

**Evaluation support:** LongMemEval score reported at ~83.2%. Context Repositories (Feb 2026) add git-based versioning for coding agent memory [VERIFIED FACT, B].

**Deployment model:** Self-hosted (OSS) or Letta Cloud (commercial) [VERIFIED FACT, A].

**Strongest capability:** The OS-paging metaphor for unbounded context is architecturally rigorous and well-benchmarked. Git-backed memory for coding agents is a differentiated feature (Feb 2026) [VERIFIED FACT, B].

**Weakest area:** LLM-driven function calls for memory management are non-deterministic and expensive — every archival insert/replace requires a full LLM inference [INFERENCE from architecture].

**Evidence confidence:** High for MemGPT architecture (arXiv paper). Medium for Letta platform features (official blog, not independent benchmarks).

---

### 4.2 Graphiti (Zep)

**What it is:** Graphiti is the temporal knowledge graph engine powering Zep Cloud, released as Apache 2.0 open source. It is the most rigorously designed temporal memory primitive in production, distinct from static GraphRAG in that time is a first-class data model property [VERIFIED FACT, A].

**Memory primitive:** Episodes (time-stamped inputs) are ingested; an LLM extracts entities and relationships as nodes and edges. Bi-temporal edges carry `valid_from` and `valid_to` fields [VERIFIED FACT, A].

**Memory write mechanism:** `add_episode()` ingests text/messages; LLM extracts entity nodes and edge relationships; deterministic deduplication added (Nov 2025 MCP 1.0) to reduce LLM call overhead [VERIFIED FACT, B].

**Memory retrieval mechanism:** Hybrid: semantic vector search + graph traversal. Cypher queries for structured access [VERIFIED FACT, A].

**Update/delete/forget:** Entity nodes and edges are updated or superseded; temporal validity windows tracked (valid_from / valid_to fields on edges) [VERIFIED FACT, B]. Edge invalidation mechanics are not fully documented publicly [UNKNOWN].

**Temporal handling:** Bi-temporal graph: both event time and ingestion time tracked. This is Graphiti's primary claimed differentiator over static GraphRAG [AUTHOR/VENDOR CLAIM, B].

**Provenance handling:** Episodes record source; node/edge origins traceable via graph traversal [VERIFIED FACT, B]. Whether provenance is queryable in production API is [UNKNOWN].

**Privacy/trust model (Zep Cloud):** SOC 2 Type II certified; HIPAA BAA available on enterprise. BYOC (AWS VPC) for data residency [VERIFIED FACT, A].

**Multi-agent support:** Graph can be shared across agents in same project; no documented consistency model for concurrent writes [INFERENCE].

**User complaints / issues:**
- "Long ingestion process" at scale (GitHub Issue #356, Apr 2025) [USER-REPORTED ISSUE, C]
- Neo4j backend breakage after version update (GitHub Issue #1063, Nov 2025) [USER-REPORTED ISSUE, C]
- Graphiti MCP server returning blank disconnected nodes (GitHub Issue #800, Aug 2025) [USER-REPORTED ISSUE, C]

**Evidence confidence:** High for CE deprecation (official announcement). Medium for Graphiti temporal model (official blog + community implementations). Low for internal deduplication algorithm specifics.

---

### 4.3 Mem0

**What it is:** Mem0 (mem0ai/mem0) is a self-described "universal memory layer for AI agents" launched January 2024, backed by YC and Peak XV with $24M raised as of October 2025 [VERIFIED FACT, B]. It is model-agnostic and framework-agnostic [AUTHOR/VENDOR CLAIM, B].

**Memory primitive:** Vector embeddings (via configurable vector DB: Qdrant, Pinecone, pgvector, etc.) + optional graph layer (Neo4j, Memgraph, Neptune Analytics, Kuzu, Apache AGE) [VERIFIED FACT, A].

**Memory write mechanism:** `memory.add(messages, user_id)` → LLM extracts facts → stored as text + embedding in vector DB + (optionally) nodes/edges in graph DB [VERIFIED FACT, A].

**Memory retrieval mechanism:** `memory.search(query, user_id)` → vector similarity search + optional graph context retrieval. Graph results returned in `relations` array [VERIFIED FACT, A].

**Update/delete/forget:** `memory.update(memory_id, data)`, `memory.delete(memory_id)`, `memory.delete_all(user_id)`. Contradicting facts reportedly handled by LLM-generated conflict resolution at write time [AUTHOR/VENDOR CLAIM, B]. Specific merge/invalidation algorithm not publicly documented [UNKNOWN].

**Temporal handling:** Timestamps on memory entries; recency is a retrieval signal. No explicit temporal graph model equivalent to Graphiti's bi-temporal edges [INFERENCE].

**Provenance handling:** No documented provenance model at the API level [INFERENCE based on public docs review].

**Privacy/trust model:** Cloud API processes messages through LLMs for extraction. GDPR compliance claimed on pricing page [AUTHOR/VENDOR CLAIM, C]. Enterprise self-hosting at custom pricing [VERIFIED FACT, C].

**Multi-agent support:** Multiple agents can write to and read from a shared `project` namespace [AUTHOR/VENDOR CLAIM, B]. No consistency model documented [INFERENCE].

**Deployment model:** Cloud API (free tier: 10K memories, 1K retrievals/month; Pro $19–$249/month) + open-source self-hosted [VERIFIED FACT, A]. Graph memory gated to $249/month Pro [VERIFIED FACT, C].

**Strongest capability:** Breadth of vector DB and graph DB backend support; large developer adoption; AWS SDK exclusive integration [VERIFIED FACT, B].

**Weakest area:** Memory add latency (~20 seconds reported in GitHub issue on self-hosted, caused by LLM extraction call) [USER-REPORTED ISSUE, C]. Graph memory behind paywall limits open-source utility [VERIFIED FACT, C].

**User complaints / issues:**
- Memory creation errors with `agent_id` / `assistant_id` parameter confusion (GitHub Issue #3256) [USER-REPORTED ISSUE, C]
- Memory add taking ~20 seconds due to LLM call latency (GitHub Issue #2813) [USER-REPORTED ISSUE, C]
- CrewAI + mem0 integration: memory cannot be saved (GitHub Issue #3152) [USER-REPORTED ISSUE, C]

---

### 4.4 LangGraph Memory (BaseStore + LangMem)

**What it is:** LangGraph's BaseStore is a key-value + (as of April 2026) semantic search primitive for persistent cross-thread memory [VERIFIED FACT, A]. LangMem is a higher-level toolkit that uses BaseStore to extract and manage episodic, semantic, and procedural memories [VERIFIED FACT, A].

**Memory primitive:** JSON documents stored by namespace + key. Embeddings indexed for semantic search. TTL indexes for automatic expiry (MongoDB integration supports native TTL) [VERIFIED FACT, A].

**Memory write mechanism:** Developer-controlled: agent calls `store.put(namespace, key, value)`. LangMem adds LLM-driven extraction to automate writes [VERIFIED FACT, A].

**Memory retrieval mechanism:** `store.search(namespace, query)` with semantic similarity (April 2026 update). Simple `store.get(namespace, key)` for deterministic retrieval [VERIFIED FACT, A].

**Update/delete/forget:** `store.put()` overwrites by key. `store.delete()` for explicit deletion. TTL-based expiry via MongoDB TTL indexes [VERIFIED FACT, A].

**Multi-agent support:** Multiple agents in same graph can share BaseStore namespaces [VERIFIED FACT, A]. No formal consistency model — concurrent writes can silently overwrite [INFERENCE from architecture].

**Strongest capability:** Most composable memory primitive in the open-source ecosystem; pluggable backends; non-opinionated design enables framework builders to layer policy on top [JUDGMENT].

**Weakest area:** BaseStore is a storage primitive with no memory policy. Deciding what to write, when to update, and how to resolve conflicts is entirely delegated to the developer [VERIFIED FACT from architecture docs].

**User complaints:** Users needed semantic search before the April 2026 release; long-term store was initially filtering-only [VERIFIED FACT, A — cited in official release notes].

---

### 4.5 CrewAI Memory

**What it is:** CrewAI is a multi-agent task orchestration framework. Memory comprises: short-term (in-session RAG), long-term (ChromaDB-persisted), entity memory (named entity extraction), and user memory (Mem0 integration) [VERIFIED FACT, A].

**Memory write mechanism:** Automatic — enabled via `memory=True` flag on Crew object [VERIFIED FACT, A].

**Update/delete/forget:** `crewai reset_memories` resets all memory types. No selective per-entity deletion documented [USER-REPORTED ISSUE, C].

**Multi-agent support:** Agents within a crew share memory stores. Independent crew isolation requires manual `os.chdir()` workarounds [USER-REPORTED ISSUE, C].

**Strongest capability:** Zero-configuration `memory=True` flag for fast onboarding [VERIFIED FACT, A].

**Weakest area:** ChromaDB dependency is fragile (version-breaking bugs on `memory=True` with v0.83.0); no multi-crew memory isolation without workarounds; RAG search returns shallow results vs. knowledge source [USER-REPORTED ISSUE, C].

**User complaints / issues:**
- RAG Memory Storage Issue with default config (GitHub Issue #1669, Nov 2024) [USER-REPORTED ISSUE, C]
- No flexible crew-specific memory reset (community forum, Sep 2024) [USER-REPORTED ISSUE, C]
- PDF RAG search misses statistics; knowledge source more reliable (community forum, Dec 2024) [USER-REPORTED ISSUE, C]
- CrewAI + Mem0 memory save failure (GitHub Issue #3152, Jul 2025) [USER-REPORTED ISSUE, C]

---

### 4.6 Commercial Assistants (ChatGPT, Claude, Gemini, Copilot)

All four commercial assistants launched memory features within a 12-month window (late 2024 – late 2025). They converge on the same user-facing UX: explicit saves, automatic extraction (except Copilot), user-visible list, per-memory deletion, and temporary/incognito mode.

**ChatGPT Memory (OpenAI):**
- Full conversation history referencing launched April 2025 [VERIFIED FACT, A]
- Architecture reverse-engineered only — system prompt injection of memories [INFERENCE]
- High-frequency complaints: memory unreliability after model updates, stale recall, excessive writes [USER-REPORTED ISSUE, C]
- Users report memories described as "recommendations, not rules" in behavior [USER-REPORTED ISSUE, C]

**Claude Memory (Anthropic):**
- GA Pro/Max: October 2025; Teams/Enterprise: September 2025 [VERIFIED FACT, A]
- Project-scoped only — memories do not persist across projects [VERIFIED FACT, A]
- Import from ChatGPT/Gemini via copy-paste supported [VERIFIED FACT, A]
- Internal architecture: [UNKNOWN]

**Gemini Memory (Google):**
- Consumer automatic past-chat learning: August 2025 [VERIFIED FACT, A]
- Enterprise: connected apps (Outlook, OneDrive) + automatic style/location inference [VERIFIED FACT, A]
- Source disconnect takes up to 24 hours to take effect [VERIFIED FACT, A]

**Microsoft Copilot Memory:**
- GA July 2025 [VERIFIED FACT, A]
- **Key distinction:** Explicit user instruction ONLY — no automatic extraction from conversations [VERIFIED FACT, A]
- Entra ID work profile auto-populated from AAD properties [VERIFIED FACT, A]
- Admin control via Graph API Enhanced Personalization resource [VERIFIED FACT, A]
- Data stored inferred to be in user mailbox (community admin analysis) [INFERENCE, D]

---

### 4.7 Haystack Memory

**What it is:** Haystack 2.0 (deepset) is a RAG pipeline framework. It does not have a long-term memory system in the agent-memory sense. It provides session-scoped `InMemoryChatMessageStore` (experimental) only [VERIFIED FACT, A].

**Key architectural fact:** ConversationSummaryMemory existed in Haystack 1.0 but was not ported to Haystack 2.0. Developers seeking summary memory in v2 find no native component [VERIFIED FACT, C].

**Strongest capability:** Best-in-class RAG pipeline composition for document-grounded retrieval; graph-based pipeline architecture in v2.0 [VERIFIED FACT, A].

**Weakest area:** No long-term agent memory primitive; session memory only; no update/delete/forget policy [VERIFIED FACT from docs].

---

### 4.8 Semantic Kernel Memory

**What it is:** Microsoft's Semantic Kernel provides `TextMemoryPlugin` (text embedding + recall) and `VectorStoreTextSearch` for enterprise .NET and Python development [VERIFIED FACT, A].

**Memory write/retrieve:** `TextMemoryPlugin.save(text, key, collection)` / `TextMemoryPlugin.recall(ask, collection, relevance, limit)` — cosine similarity search [VERIFIED FACT, A].

**Key acknowledged gap:** `TextMemoryPlugin` methods were not designed for function-calling (intended for prompt injection). SK team acknowledged this gap and redesigned toward VectorStoreTextSearch [USER-REPORTED ISSUE, A — confirmed in GitHub Discussion #8074].

**Evidence confidence:** High for API (official Microsoft docs). Temporal and provenance gaps are [INFERENCE].

---

## 5. Convergence Map

### 5.1 Vector Memory — **Fully Commodity**

Supported by: Mem0, LangGraph BaseStore, LlamaIndex, Semantic Kernel, CrewAI, Supermemory, AutoGen, Letta archival storage, Zep (alongside graph).

Every system above supports embedding + vector similarity search. The substrate is not differentiating. Embedding APIs became cheap and ubiquitous in 2022–2024; ChromaDB/Qdrant/pgvector provided accessible backends.

**Still matters in execution:** Embedding quality, chunking strategy, hybrid retrieval weighting, re-ranking.

---

### 5.2 Summary / Conversation Compression — **Largely Commodity**

Any LLM can summarize; the differentiation is in what gets preserved and discarded. Haystack v1 had `ConversationSummaryMemory`; not ported to v2. This is now a solved problem at the infrastructure level but an unsolved problem at the quality level (what to forget).

---

### 5.3 Explicit User Profile / Fact Memory — **Approaching Commodity**

All four major commercial assistants and most developer frameworks support this. Fails to solve: temporal staleness (stored fact may no longer be true), provenance (which conversation generated this fact), privacy (user may not want certain facts stored).

---

### 5.4 Temporal Knowledge Graph Memory — **Not Commodity — Actively Differentiating**

Systems: Graphiti (Zep), Mem0 with graph backend (partial — Pro paywall), Cognee (Graphiti integration).

Graphiti is the most complete public implementation of bi-temporal graph memory. Few competitors implement proper bi-temporal graphs. Static GraphRAG (Microsoft 2024) does not handle time-varying facts.

**Why it became needed:** Static RAG/vector memory cannot answer "what was true at time T" or handle updating facts (e.g., "budget was $50K, now $80K").

**Fails to solve:** Formal consistency models for concurrent agent writes; query latency vs. simple vector search; contradiction resolution algorithm is undocumented in all implementations.

---

### 5.5 Checkpointing / State Persistence — **Commodity for Single-Thread**

**IMPORTANT DISTINCTION:** This is **agent state**, not **long-term memory**. A checkpointer stores the full execution state for one thread; it is scoped to a session and does not persist semantic facts cross-session. LangGraph checkpointers are the canonical implementation.

Not sufficient for long-term memory use cases.

---

### 5.6 Hybrid Memory Stacks — **Becoming Standard Design Pattern**

Mem0 (vector + graph), Graphiti (graph + vector), LangGraph + LangMem (key-value + semantic search), Letta (in-context + archival), Supermemory (RAG + memory in single query).

Execution quality varies widely. Increased architectural complexity and write-path coordination cost are real trade-offs.

---

### 5.7 Hosted Memory APIs — **Commodity at API Level**

Mem0 Cloud, Zep Cloud, Supermemory API, all four commercial assistants. Removing infrastructure burden is now baseline. Differentiation is in reliability, latency SLAs, privacy guarantees, and enterprise features.

---

## 6. Commodity Layer

| Capability | Why Commodity | What Still Matters in Execution |
|-----------|---------------|--------------------------------|
| Vector search over conversation history | Embedding APIs + vector DBs ubiquitous since 2022 | Embedding quality, chunking strategy, hybrid retrieval weighting |
| Embeddings + metadata filters | Off-the-shelf since 2022 | Filter expressiveness; cross-collection namespacing |
| Conversation summarization | LLM capability, not architectural differentiation | What to preserve; forgetting vs. compression fidelity |
| Long-term user facts/preferences | All four major commercial assistants converged by 2025 | Reliability, staleness detection, conflict handling |
| Namespace/project memory | Basic multi-tenancy need met by all frameworks | Isolation guarantees; cross-namespace leakage prevention |
| RAG over documents | Canonical LLM application pattern since 2022 | Chunking, retrieval precision, reranking quality |
| Basic graph relationships | GraphRAG popularized by Microsoft (2024) | Temporal graph vs. static graph; update semantics |
| State checkpointing | LangGraph made this accessible to Python developers | Multi-thread coordination; state schema evolution |
| Simple delete/update APIs | Developer expectation from day one | Cascade deletion; referential integrity in graph backends |
| Memory as hosted API | Hosting removes friction; four major players offer it | Latency SLAs; data residency; lock-in terms |

---

## 7. Hand-Wave Layer

### 7.1 "Learns over time" / "Self-improving agents"

**Examples:** Mem0 — "self-improving memory layer" [AUTHOR/VENDOR CLAIM, B]. Supermemory — "forgets expired information" [AUTHOR/VENDOR CLAIM, B]. Letta — "learn and self-improve over time" [AUTHOR/VENDOR CLAIM, B].

**What is missing:** No system provides documented, audited evidence that stored memories improve agent task performance on an independent benchmark over time. "Learns" typically means "accumulates stored facts via LLM extraction." No published time-series benchmark results showing measurable performance improvement as memory accumulates, on held-out tasks, with ablations.

---

### 7.2 "Personalized AI"

**Examples:** ChatGPT, Claude, Gemini, Copilot all use this framing [AUTHOR/VENDOR CLAIM, A-level sources for feature existence; claim of *quality* is vendor framing].

**What is missing:** No published user study or benchmark validating that memory-enabled responses are measurably more accurate or preferred. User complaints of stale or wrong memories directly contradict the claim [USER-REPORTED ISSUE, C].

---

### 7.3 "Knowledge graph memory" / "Temporal awareness"

**What is partially verified:** Graphiti implements bi-temporal edges with valid_from/valid_to and episode ingestion [VERIFIED FACT, B]. This is structurally sound.

**What is missing:** Published benchmark results specifically testing temporal reasoning accuracy on temporal KG vs. flat vector memory. How temporal contradictions are resolved when two episodes conflict for the same time period. Whether agents actually query time-scoped facts in production or simply retrieve most-recent nodes.

---

### 7.4 "Safe memory" / "Trustworthy memory"

**Examples:** Anthropic — "rigorous testing on sensitive areas of memory" before release [AUTHOR/VENDOR CLAIM, B]. Gemini — "privacy at its core" [AUTHOR/VENDOR CLAIM, A].

**What is missing:** Memory poisoning is documented as a present threat by multiple independent security researchers [VERIFIED FACT, B]. No memory system publishes a threat model for memory poisoning, adversarial injection, or hallucinated memory propagation. HaluMem shows QA accuracy tops at 56% due to hallucinations in extraction/updating — a trustworthiness failure [VERIFIED FACT, A].

---

### 7.5 "Multi-agent memory"

**What is partially verified:** Multiple agents can read/write to a shared store in Mem0 and LangGraph [VERIFIED FACT, B].

**What is missing:** arXiv:2603.10062 (Mar 2026) explicitly frames multi-agent memory consistency as an unsolved problem, identifying two missing protocols: cache-sharing and memory-access-control [VERIFIED FACT, A]. No production framework has published a solution.

---

### 7.6 "Automatic memory consolidation"

**Examples:** Supermemory — "handles knowledge updates and contradictions" [AUTHOR/VENDOR CLAIM, B]. Mem0 — LLM-driven conflict resolution at write time [AUTHOR/VENDOR CLAIM, B].

**What is missing:** Published algorithm or methodology for contradiction detection and resolution. Developer community consensus is that existing systems "assume: retrieve everything relevant and let the model reconcile contradictions" — a known failure mode [USER-REPORTED ISSUE, D].

---

### 7.7 "#1 on LongMemEval" (Supermemory)

**Claim:** Supermemory claims "#1 on LongMemEval, LoCoMo, and ConvoMem" [AUTHOR/VENDOR CLAIM, C].

**Critical analysis:** LinkedIn technical analysis (Mar 2026) identifies the methodology as pass@8 (oracle metric — correct if *any* of 8 parallel agents answers correctly), not single-agent accuracy. The architecture uses 14–18+ LLM calls per query. **No independent third-party replication found.** MemoryBench is Supermemory-built and self-evaluated [INFERENCE from source].

**Evidence needed:** Independent replication using standard QA accuracy (not pass@8) on LongMemEval-M with single-agent, production-comparable inference budget.

---

## 8. User Complaint Map

| Pain Point | Evidence Source | Frequency | Affected Systems | Severity | Status |
|-----------|----------------|-----------|-----------------|----------|--------|
| Wrong/stale memory retrieved | OpenAI forums (hundreds of replies); Graphiti GitHub | High (multi-thread) | ChatGPT, Graphiti, CrewAI, Mem0 | Critical | **Unsolved** |
| Excessive/unwanted memory writes | Reddit r/ChatGPT; GitHub mem0 | Medium | ChatGPT, Mem0 | High | **Partially solved** — opt-out exists |
| Memory loss after model update | Reddit r/OpenAI (40+ votes, May 2025); OpenAI community | High (model update events) | ChatGPT | High | **Unsolved** |
| Setup complexity | mem0 GitHub #2813; CrewAI GitHub #1669 | Medium | Mem0 self-hosted, CrewAI, Graphiti | High | **Partially solved** via cloud APIs |
| Retrieval irrelevance / no policy | r/MachineLearning developer consensus | High | All vector-memory systems | Critical | **Unsolved** |
| LLM extraction latency on write | mem0 GitHub #2813 (~20s write latency) | Medium | Mem0, Graphiti, LangMem | High | **Partial mitigation** (async, faster models) |
| Lack of observability / debugging | arXiv:2603.07670; Penligent audit post | High (industry-wide) | All systems | Critical | **Unsolved** |
| Context pollution from irrelevant memories | arXiv:2601.11653 ACC paper | High (research consensus) | All retrieve-then-inject systems | Critical | **Research-stage only** |
| Privacy / unclear deletion semantics | Gemini 24h disconnect delay; OpenAI conversation history | Medium | ChatGPT, Gemini, Copilot | High | **Partially addressed** |
| Unclear memory provenance | LinkedIn governance post; arXiv cognitive memory | High (research/enterprise) | All systems | Critical | **Unsolved** |
| Vendor lock-in | Zep CE deprecation; AI ecosystem fragmentation Apr 2026 | Growing | Zep, ChatGPT, Copilot, Mem0 Cloud | High | **Active problem** |
| Hallucinated memories from extraction | HaluMem arXiv:2511.03506; <60% extraction recall | High (research evidence) | All LLM-extraction-based systems | Critical | **Unsolved** |

---

## 9. Architecture Comparison Matrix

| System | Storage Substrate | Retrieval Model | Write Policy | Update Policy | Forgetting/Deletion | Temporal Awareness | Provenance | Explainability | Multi-Agent | Eval Tools | Lock-In Risk |
|--------|------------------|-----------------|-------------|--------------|--------------------|--------------------|------------|----------------|-------------|-----------|-------------|
| **Letta** | Pluggable archival DB + in-context | Vector + keyword | LLM function-call driven | `core_memory_replace` | Explicit function call | Timestamps; no formal model | None | Partial (in-context) | Multi-agent via Conversations (2026) | LongMemEval 83.2% | Medium |
| **Graphiti** | Neo4j / Postgres bi-temporal KG + vector | Hybrid graph + vector | Episode → LLM extraction | Node/edge update with time window | Edge invalidation (valid_from/valid_to) | **Best-in-class** (bi-temporal) | Episode source tracked | Graph traversal | Shared graph (no consistency model) | HaluMem ~55% QA | **High** (CE deprecated) |
| **Mem0** | Qdrant/pgvector + Neo4j graph (Pro) | Vector + optional graph | Automatic LLM extraction | LLM conflict resolution (vendor claim) | `delete(id)`, `delete_all(user_id)` | Timestamps; no temporal graph (OSS) | None | None | Shared project namespace | MemoryBench integrations | **High** (cloud entanglement) |
| **LangGraph BaseStore** | Postgres, MongoDB, Redis, In-Memory | Semantic search (Apr 2026) + key-value | Developer-defined | Key overwrite via `store.put()` | `store.delete()`; TTL via MongoDB | None (developer-implemented) | None | None | Shared namespace (no consistency model) | None built-in | Low (swappable backends) |
| **LangMem** | LangGraph BaseStore | Semantic via BaseStore | LLM extraction + developer hooks | Overwrite by key | Inherited from BaseStore | None | None | None | Inherited from BaseStore | None published | Medium |
| **CrewAI** | ChromaDB (default) | Vector similarity | Automatic on `memory=True` | Upsert in Chroma | `crewai reset_memories` (all-or-nothing) | None | None | None | Within-crew only | None | Medium |
| **Semantic Kernel** | Pluggable IMemoryStore | Cosine similarity | `TextMemoryPlugin.save()` | Key-based overwrite | Explicit delete | None | None | None | None native | None | Low |
| **LlamaIndex** | VectorStoreIndex (pluggable) | Semantic vector | Developer-controlled | Overwrite | Delete by ID | None | None | None | None | None | Medium |
| **Haystack** | InMemoryChatMessageStore (session) | Full retrieval (no semantic in store) | `ChatMessageWriter` component | N/A (session-scoped) | `delete_messages()` | None (session only) | None | None | None | None | Low |
| **ChatGPT** | Opaque (OpenAI servers) | Unknown (injected to context) | Automatic + explicit | User-edit | Per-memory + bulk delete | Timestamps (visible to user) | None (source not shown) | None | N/A | None public | **Critical** (closed) |
| **Claude** | Opaque (Anthropic) | Unknown | Automatic + explicit | User-edit | Per-memory; incognito | None documented | None | None | N/A | None public | **Critical** (closed) |
| **Gemini** | Opaque (Google) | Unknown | Automatic (past chat) + explicit | User/admin | "Keep Activity" controls; 24h delay | Inferred recency | None | None | N/A | None public | **Critical** (closed) |
| **Copilot** | Opaque (Microsoft, likely user mailbox) | Unknown | **Explicit only** (no auto-extraction) | User-edit | Per-memory; admin Graph API | None | None | None | N/A | None public | **Critical** (closed) |

---

## 10. What Top Players Avoid Saying

### How memories are selected for storage [JUDGMENT + INFERENCE]

No system publishes a selection algorithm. Mem0 and LangMem indicate LLM-based extraction, but the prompts, criteria, and quality thresholds are undocumented. ChatGPT, Claude, and Gemini give no technical detail whatsoever. [INFERENCE]: all commercial systems use proprietary extraction prompts that users cannot inspect or audit.

### How bad memories are corrected [JUDGMENT + INFERENCE]

All systems allow manual user deletion. None document an automated bad-memory detection mechanism. HaluMem shows hallucinations accumulate during extraction; no system has published a remediation path for memories that were incorrectly extracted from the start. Governance researchers identify the absence of "remediation loops" as a critical gap.

### How temporal contradiction is handled [JUDGMENT]

Graphiti tracks time-valid edges but the contradiction resolution algorithm is undocumented publicly. All other systems silently coexist with contradictory memories — retrieval may surface both, and the LLM is expected to reconcile them at query time. [INFERENCE]: this is the single most common silent failure mode.

### How privacy is enforced [JUDGMENT]

Commercial assistants provide user-facing deletion controls but none document retention behavior after deletion, backup policies, or third-party LLM exposure during memory extraction. Gemini's 24-hour delay on source disconnection is the only publicly documented retention edge case. For developer tools using cloud APIs (Mem0 Cloud, Zep Cloud), messages are processed through vendor inference infrastructure. The specific LLM call chain for extraction is not published.

### How memory quality is measured [JUDGMENT + VERIFIED GAP]

The field acknowledges fragmented evaluation with no universal standard (arXiv:2512.13564). Production systems do not expose internal memory quality metrics. Supermemory's MemoryBench allows self-evaluation but is self-built and self-reported. HaluMem's operation-level approach is the most rigorous available, but no production system has adopted it for continuous quality monitoring.

### How hallucinated reflections are prevented [VERIFIED GAP]

HaluMem demonstrates extraction recall below 60% and hallucinations cascade into QA. No system publishes an anti-hallucination constraint on the memory write path. The ACC paper (arXiv:2601.11653) proposes bounded internal state to prevent poisoning, but is not implemented in any surveyed production framework.

### How memory poisoning is mitigated [VERIFIED GAP]

Multiple security papers document that adversarially injected or incorrect memories persist and influence agent behavior. No production memory system publishes a threat model or mitigation strategy for memory poisoning. This is treated as an open research problem.

### How multi-agent conflicts are resolved [VERIFIED GAP]

arXiv:2603.10062 (Mar 2026) formalizes this as an unsolved computer-architecture problem. No production framework documents a consistency protocol for concurrent multi-agent memory writes. Shared namespaces can silently overwrite each other's memories.

### How costs scale [JUDGMENT + INFERENCE]

LLM-extraction-based memory systems (Mem0, Graphiti, LangMem) execute at least one LLM call per memory write. At high throughput, this becomes the dominant cost driver. None publish per-memory token cost estimates or tier-based extraction policies. Supermemory's claimed architecture uses 14–18 LLM calls per query — cost at scale is undisclosed.

### How users inspect/audit memory [VERIFIED GAP]

User-facing: ChatGPT, Claude, Gemini, Copilot provide a memory list UI with delete controls. Developer-facing: no system provides a structured audit log of (memory_id, source_conversation_id, extraction_timestamp, extraction_confidence, last_retrieved_at, retrieval_count). Penligent (Mar 2026) identifies this as a critical white-box auditing gap.

---

## 11. Differentiation Opportunities

### 11.1 Operation-Level Memory Evaluation Suite

**Primitive:** A benchmark and evaluation harness that tests extraction accuracy, update accuracy, temporal reasoning, and QA separately — following HaluMem methodology.

**Why current systems do not solve it:** MemoryBench is self-built by Supermemory. HaluMem is a research dataset, not an integrated evaluation tool. No system tests all four operation stages independently in CI/CD.

**Evidence:** HaluMem arXiv:2511.03506; LongMemEval; MemBench ACL 2025. Field explicitly lacks a universal standard (arXiv:2512.13564).

**Technical difficulty:** Medium. Requires: multi-session dialogue datasets with labeled ground-truth facts; operation-level instrumentation hooks; automatic scoring (GPT-4o-class judge validated at 95.7% human agreement by HaluMem).

**Adoption wedge:** Published benchmark + open leaderboard creates organic community adoption. Developer teams need regression tests before deploying memory changes.

**Risk:** Benchmark Goodhart's Law — systems optimize for the benchmark rather than real-world quality.

---

### 11.2 Temporal Memory with Formal Conflict Resolution

**Primitive:** A bi-temporal memory store with a documented, auditable algorithm for resolving contradicting facts across time (e.g., "budget was $50K until March 2025, then $80K").

**Why current systems do not solve it:** Graphiti implements bi-temporal edges but does not publish its contradiction-resolution algorithm. All other systems are flat-vector-only or delegate reconciliation to the LLM at query time.

**Evidence:** ACC paper notes "contradiction handling" as an open engineering reality; survey arXiv:2512.13564 identifies temporal reasoning as a frontier.

**Technical difficulty:** High. Requires: formal temporal data model; deterministic conflict-detection rule engine; user-inspectable merge audit log.

**Adoption wedge:** Enterprise use cases with regulatory requirements (finance, healthcare, legal) where stale facts create liability.

**Risk:** Over-engineering for most developer use cases. The temporal model must be opt-in with sensible defaults.

---

### 11.3 Structured Memory Provenance API

**Primitive:** Every memory entry carries a structured provenance record: `{source_type, source_id, extraction_timestamp, extracted_by_model, confidence_score, last_modified, modified_by}`.

**Why current systems do not solve it:** No system (open or commercial) exposes a queryable provenance API. The governance gap is documented by multiple independent researchers.

**Evidence:** arXiv:2512.12856 proposes provenance fields for privacy-aware agents; W3C Verifiable Credentials cited as relevant standard; Penligent audit framing identifies provenance as a critical audit requirement.

**Technical difficulty:** Medium-Low for the data model; Medium for integration with existing LLM extraction pipelines. Provenance fields are metadata — they do not require changing retrieval semantics.

**Adoption wedge:** Compliance-focused enterprise deployments (GDPR Article 22 rights, AI Act transparency requirements); security researchers.

**Risk:** Provenance metadata increases storage cost by ~30-50% per memory entry [INFERENCE]. Requires tooling to make provenance useful (memory diff views, source-conversation replays).

---

### 11.4 Memory Observability Layer (Trace + Audit)

**Primitive:** An OpenTelemetry-compatible trace layer emitting structured spans for every memory operation: write (with input/output), retrieval (with query + top-K results + scores), injection (what entered context), and agent decision (did the agent use the retrieved memory).

**Why current systems do not solve it:** LangSmith traces LLM calls and tool use but has no dedicated memory operation traces. No memory system emits standardized telemetry. Penligent's audit post identifies exactly this as a white-box auditing gap.

**Technical difficulty:** Low-Medium. OpenTelemetry SDK exists; the challenge is standardizing the memory-operation span schema and instrumenting existing libraries.

**Adoption wedge:** Developers debugging memory failures ("why did the agent recall the wrong thing?") and enterprise compliance officers.

**Risk:** Adds latency overhead (~1-5ms per operation for trace emission). Performance-sensitive applications may disable.

---

### 11.5 Privacy-First Memory with Consent Model

**Primitive:** A memory system where: (a) each memory entry carries a consent tag (user-consented vs. auto-extracted), (b) extraction uses differential-privacy techniques for sensitivity, (c) deletion is verifiable and cryptographically provable.

**Why current systems do not solve it:** Commercial assistants provide deletion UIs but opaque backend retention. Developer tools have no consent model. No system implements differential privacy for memory extraction.

**Evidence:** arXiv:2512.12856 proposes consent metadata; GDPR compliance claimed by Mem0 but unverified; AI Act transparency requirements create regulatory pressure.

**Technical difficulty:** High. Differential privacy for LLM extraction is an active research area. Cryptographic provable deletion requires storage backend cooperation.

**Adoption wedge:** European enterprise deployments (GDPR); healthcare and legal verticals; privacy-forward consumer applications.

**Risk:** Meaningful DP protection may significantly degrade memory utility. The privacy-utility tradeoff needs published analysis before adoption.

---

### 11.6 Multi-Agent Memory Consistency Protocol

**Primitive:** A formal consistency model for concurrent agent memory writes: at minimum, optimistic-locking with conflict detection and a merge-or-reject policy; ideally, a published specification implementable by any memory backend.

**Why current systems do not solve it:** arXiv:2603.10062 (Mar 2026) frames this as formally unsolved. All current shared-store implementations allow silent overwrites. No framework has published a memory consistency specification.

**Technical difficulty:** High. CRDT-based approaches may work for fact-level conflicts; temporal graph edges with last-write-wins are insufficient for complex multi-agent scenarios.

**Adoption wedge:** Enterprise multi-agent deployments (sales + support + analyst agents sharing customer context); compliance frameworks requiring auditability of who changed what.

**Risk:** Protocol complexity may deter adoption. Must be simple enough to implement without deep distributed-systems knowledge.

---

### 11.7 Memory Format Portability Standard

**Primitive:** An open memory interchange format (JSON-LD or similar) specifying: memory_id, content, memory_type (episodic/semantic/procedural), provenance, temporal_validity, permissions, and embedding reference.

**Why current systems do not solve it:** Memory formats are vendor-proprietary. Zep CE deprecation and closed commercial memory formats mean users cannot export and re-import memories across systems. Claude supports manual copy-paste import but not structured export.

**Evidence:** Behavioral lock-in via persistent agent context documented as a new switching-cost category; AI agent ecosystem fragmentation growing in early 2026.

**Technical difficulty:** Low (schema design) to Medium (community adoption and tooling).

**Adoption wedge:** Developer frustration with lock-in; enterprise multi-vendor strategies.

**Risk:** Network effects favor closed platforms. An open standard requires adoption by at least one major framework to gain traction (Model Context Protocol history is instructive).

---

### 11.8 Write-Path Hallucination Suppression

**Primitive:** A constrained memory extraction pipeline that: (a) uses structured output schemas (not free-text extraction), (b) applies a confidence threshold before storage, (c) provides a review queue for low-confidence extractions, (d) prevents unverified content from becoming persistent memory.

**Why current systems do not solve it:** HaluMem shows extraction recall below 60% is the primary QA failure cause. No production system publishes a confidence-gated write path. ACC paper proposes "separating artifact recall from state commitment" but is not implemented in production.

**Technical difficulty:** Medium. Structured output (JSON schema-constrained extraction) is available today. Confidence calibration requires a calibration dataset.

**Adoption wedge:** Any developer who has seen a wrong memory contaminate subsequent agent responses — a common, high-pain experience documented in multiple complaint threads.

**Risk:** Confidence gating may over-reject valid low-confidence memories, reducing recall. Needs tunable threshold with sensible defaults.

---

## 12. Evidence Ledger

| Claim | System(s) | Source Grade | Evidence Strength | Caveat |
|-------|-----------|-------------|-------------------|--------|
| Graphiti uses bi-temporal KG with valid_from/valid_to | Graphiti/Zep | A (official docs) | Strong | Contradiction resolution algorithm undocumented |
| Mem0 has 56K+ GitHub stars and $24M raised | Mem0 | B (TechCrunch / GitHub) | Strong | Verify at access time; counts change |
| Mem0 graph memory costs $249/mo (Pro) | Mem0 | C (pricing page) | Strong at time of access | Pricing can change |
| Zep CE deprecated April 2025 | Zep | A (official blog + CE GitHub) | Definitive | Check CE repo for any revival |
| LangGraph BaseStore semantic search added April 2026 | LangGraph | A (official release notes) | Definitive | API may evolve |
| HaluMem: extraction recall <60%; QA tops at 56% | All LLM-extraction systems | A (arXiv:2511.03506, ICLR 2025) | Strong | Dataset is multi-turn dialogue; domain generalizability unknown |
| ChatGPT full conversation history launched April 2025 | ChatGPT | A (OpenAI community post) | Strong | Feature available to Plus/Pro |
| Microsoft Copilot Memory GA July 2025; explicit-only writes | Copilot | A (MS Tech Community + Office365 IT Pros) | Definitive | Not automatic extraction |
| Claude memory GA Pro/Max Oct 2025; Teams Sep 2025 | Claude | A (Anthropic blog) | Definitive | Internal architecture unknown |
| Gemini Enterprise Memory: 24h disconnect delay | Gemini | A (cloud.google.com docs) | Strong | Admin controls subject to change |
| OpenAI Assistants vector store: 10K file hard limit | OpenAI Assistants | A (OpenAI community, staff-confirmed) | Strong | Platform limit may change |
| Supermemory "#1 on LongMemEval" = pass@8 over 14–18 LLM calls | Supermemory | D (LinkedIn technical analysis) | Weak | Not peer-reviewed; vendor has not publicly refuted |
| Multi-agent memory consistency is formally unsolved | All multi-agent systems | A (arXiv:2603.10062) | Strong | Paper identifies problem; no solution published |
| Memory poisoning is a present production threat | All agent memory systems | B (arXiv security papers) | Medium | Attack scenarios documented; prevalence in production unknown |
| Memory evaluation field is fragmented | Field-wide | A (arXiv:2512.13564; arXiv:2605.06716) | Strong | Surveys reflect field at submission time |
| Letta Context Repositories: git-backed memory (Feb 2026) | Letta | B (official blog) | Medium | New feature; no independent production evidence |
| CrewAI ChromaDB dependency fragile | CrewAI | C (GitHub Issue #1669) | Medium | Bug may be fixed in later releases |
| Memory hallucinations accumulate at extraction stage | All extraction-based | A (HaluMem arXiv:2511.03506) | Strong | Stage-level decomposition novel; needs replication |
| ACC (bounded internal state) prevents context pollution | Research proposal | B (arXiv:2601.11653) | Medium | Research paper; not production-validated |

---

## 13. Unknowns and Further Research

### Systems Not Fully Verified

- **AutoGen Memory (v0.4+):** GitHub Issue #4264 confirms memory as first-class was still in progress as of Nov 2024. Current v0.4 memory docs require hands-on testing to verify what shipped. [UNKNOWN] — current production memory API completeness.
- **Cognee:** Small but interesting (Apache 2.0, Graphiti integration). Limited production adoption signal. Claimed Redis integration is verified; broader production usage evidence is weak.
- **Mastra (research arm):** Claims 95% on LongMemEval via "Observational Memory" (Feb 2026). No hands-on testing performed; methodology not independently reviewed. [UNKNOWN — needs verification].

### Closed Commercial Features with Limited Evidence

- **ChatGPT memory internal architecture:** Reverse-engineered only. Which conversations are used as sources, deduplication logic, and retention schedules are [UNKNOWN].
- **Claude memory extraction algorithm:** Anthropic mentions only "rigorous testing on sensitive topics." No technical specification published.
- **Gemini Enterprise Memory:** Connected app indexing pipeline, refresh interval, and conflict resolution [UNKNOWN].
- **OpenAI Responses API memory:** Whether a structured long-term memory API exists beyond Assistant threads is [UNKNOWN at time of research].

### Stale Documentation Risks

- **Haystack 1.0 memory components (ConversationSummaryMemory, BufferMemory):** Not ported to Haystack 2.0. Developers may encounter outdated tutorials.
- **LangChain memory modules (v1 patterns):** Pre-LangGraph patterns (ConversationBufferMemory, ConversationSummaryMemory) are deprecated. The current canonical pattern is LangGraph BaseStore + LangMem. Hands-on testing needed to confirm migration paths.
- **AutoGen memory docs:** Version fragmentation between 0.2, 0.4, and 0.4.7+ documented by community. Hands-on testing required.

### Inaccessible Community Complaints

- Private Discord servers for Zep, Letta, and Mem0 may contain higher-signal complaint data than public GitHub issues. These were not accessed.
- Enterprise-level user feedback for Copilot, Claude, and Gemini Memory is not publicly available.

### Ambiguous Product Claims

- **Mem0's LLM-driven conflict resolution:** [AUTHOR/VENDOR CLAIM]. The specific algorithm (which LLM, which prompt, what merge policy) is not published. Hands-on testing with contradicting facts is required to verify behavior.
- **Supermemory's LongMemEval #1 claim:** Benchmark methodology contested. Independent replication with standard single-agent QA accuracy on LongMemEval-M is required.
- **Graphiti's "deterministic deduplication" (MCP 1.0, Nov 2025):** The deduplication algorithm (exact-match vs. fuzzy vs. LLM-assisted) is not detailed in public documentation.

### Areas Requiring Hands-On Testing

1. **Memory poison injection:** Test all major systems with adversarially crafted input designed to persist false memories. Measure propagation to subsequent agent outputs.
2. **Temporal contradiction resolution:** Inject contradicting facts ("X was true on Day 1, then changed on Day 5") into Graphiti, Mem0, and LangMem. Measure whether temporal queries return correct time-scoped results.
3. **Multi-agent write contention:** Simulate concurrent writes from two agents to shared Mem0 / LangGraph BaseStore namespace. Measure silent overwrite rate.
4. **HaluMem replication:** Run HaluMem evaluation against Mem0 (OSS), Graphiti, LangMem, and CrewAI memory to establish independent baseline.
5. **Supermemory single-agent accuracy:** Reproduce LongMemEval evaluation with single-agent, single-call inference to verify actual production-equivalent accuracy.
6. **Write latency profiling:** Benchmark Mem0 `add()` at 100, 1000, and 10000 operations with different extraction models (GPT-4o vs. GPT-4o-mini vs. local models).
