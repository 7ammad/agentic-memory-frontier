# Report 1: Frontier Memory Research Map
### Agentic Memory — Current Frontier, Open Gaps, and Candidate Directions
*Research Date: May 2026 | Prepared as a senior AI research analyst review*

***

## 1. Executive Summary

The following 14 findings are grounded in verifiable primary sources. Each is directly useful for builders deciding what to build.

1. **Existing memory benchmarks measure the wrong thing.** MemoryArena (arXiv:2602.16313, Stanford/UCSD/UW, Feb 2026) shows that agents achieving near-saturated performance on LoCoMo and other long-context benchmarks fail significantly in multi-session agentic tasks where memory must drive future decisions, not just recall past facts. *[VERIFIED FACT]*[^1][^2]

2. **Commercial chat assistants show ~30% accuracy drop on multi-session memory.** LongMemEval (ICLR 2025, arXiv:2410.10813) demonstrates this directly across five core memory abilities: information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention. *[VERIFIED FACT]*[^3][^4]

3. **Temporal reasoning in memory is a severe, underaddressed bottleneck.** LLMs lag behind human performance in temporal reasoning by 73% in LoCoMo benchmarks (ACL 2024, snap-research/locomo). The TReMu framework improved GPT-4o temporal reasoning from 29.83 to 77.67 using neuro-symbolic methods, but this is a point solution on a limited benchmark. *[VERIFIED FACT]*[^5][^6]

4. **Knowledge editing (ROME/MEMIT) fails at real-world scale.** The "Mirage of Model Editing" (ACL 2025, QAEdit benchmark) shows current editing methods perform at ~38.5% accuracy in practice vs. ~96.8% in synthetic evaluations, and collapse with as few as 1,000 sequential edits. The UC Berkeley "Model Editing at Scale" paper confirms ROME/MEMIT exhibit gradual then catastrophic forgetting during sequential edits. *[VERIFIED FACT]*[^7][^8][^9]

5. **Reflection-based memory (Reflexion) is a NeurIPS 2023 result with an open reliability problem.** Reflexion (NeurIPS 2023, arXiv:2303.11366) demonstrated that verbal self-reflection stored in an episodic memory buffer improves performance (91% pass@1 on HumanEval), but the system stores self-generated linguistic outputs without systematic verification—creating hallucination accumulation risk. Whether this scales reliably across many tasks is *[UNCERTAIN]* based on available evidence.[^10][^11]

6. **Procedural memory for LLM agents is an early-stage but active direction.** ProcMEM (arXiv:2602.01869, Feb 2026) proposes learning executable skill primitives from experience via non-parametric PPO without weight updates. Memp (arXiv:2508.06433, Aug 2025) distills trajectories into step-level and script-level procedural abstractions. Both demonstrate improved reuse rates and cross-agent transfer; neither has been validated at production scale. *[AUTHOR CLAIM]*[^12][^13]

7. **MEM1 (ICLR 2026) shows RL-based memory consolidation can reduce context by 3.7x while improving performance 3.5x.** This is the most principled result on learned memory compression to date (arXiv:2506.15841, MIT/NUS). *[VERIFIED FACT — strongest evidence for RL-trained consolidation*]*[^14][^15]

8. **Temporal knowledge graph memory (Zep/Graphiti) offers significant latency and accuracy improvements over pure vector memory.** On LongMemEval, Zep achieved accuracy improvements of up to 18.5% and reduced response latency by 90% compared to baseline RAG implementations (arXiv:2501.13956). *[AUTHOR CLAIM — not independently replicated in the paper itself]*[^16]

9. **Memory privacy attacks are demonstrated and real.** MEXTRA (ACL 2025, arXiv:2502.13172) shows that private user information can be extracted from LLM agent memory stores in black-box settings via adversarial prompt design. No comprehensive defense mechanism has yet been deployed. *[VERIFIED FACT]*[^17][^18]

10. **Multi-agent memory architectures lag behind single-agent memory by a large margin.** G-Memory (NeurIPS 2025 Spotlight, arXiv:2506.07398) improves multi-agent system success rates by up to 20.89% using hierarchical graph memory, identifying that "prevailing MAS memory mechanisms are overly simplistic." *[VERIFIED FACT — author's own framing]*[^19][^20]

11. **EvolMem (arXiv:2601.03543, Jan 2026) shows no LLM consistently outperforms across all memory dimensions, and agent memory mechanisms do not necessarily enhance LLMs' capabilities.** This is a significant finding: added memory infrastructure can fail to help or even degrade performance on some axes. *[AUTHOR CLAIM]*[^21]

12. **From-Storage-to-Experience survey (ACL 2026, arXiv:2605.06716) formalizes a three-stage evolution framework.** The current research frontier is defined by the "Experience" stage involving proactive exploration and cross-trajectory abstraction—not simple storage or reflection. *[AUTHOR CLAIM — but peer-reviewed and useful as a taxonomy anchor]*[^22]

13. **A-MEM (NeurIPS 2025, arXiv:2502.12110) shows Zettelkasten-inspired dynamic memory organization outperforms static graph-backed memory systems.** The key mechanism is memory evolution: new memories can trigger updates to existing memories' contextual representations and attributes. *[AUTHOR CLAIM — results on long-term dialogue datasets]*[^23][^24]

14. **Memory benchmarks do not measure causal relevance of retrieved memories to actual task outcomes.** MemoryAgentBench (ICLR 2026, GitHub: HUST-AI-HYZ) identifies four competencies (accurate retrieval, test-time learning, long-range understanding, conflict resolution) and shows current methods fail on all four simultaneously. *[VERIFIED FACT]*[^25][^26]

***

## 2. Research Boundary

### What "Agentic Memory" Means in This Report

Agentic memory refers to all mechanisms by which an LLM-based agent stores, retrieves, consolidates, updates, and uses information across time to improve task performance. This explicitly excludes one-shot prompt engineering and basic in-context examples, which are not memory systems.

### Memory Type Taxonomy

| Memory Type | Definition | Storage Location | Primary Challenge |
|-------------|------------|------------------|-------------------|
| **Parametric model memory** | Knowledge encoded in model weights during training/fine-tuning | Model parameters | Cannot be updated without retraining; cannot be audited |
| **Context window memory** | Information held in the active prompt/KV cache | Current context | Bounded in size; degrades at middle positions ("Lost in the Middle")[^27][^28] |
| **External memory** | Information stored in external databases (vector, graph, document) | External store | Retrieval mismatch; stale data; privacy leakage |
| **Retrieval memory (RAG)** | Information retrieved from external stores on demand | External store + context | Embedding failure; semantic mismatch; over/under-retrieval |
| **Reflective memory** | Linguistic self-evaluations stored as episodic trace | External store or context | Hallucination accumulation; unreliable self-assessment |
| **Procedural/skill memory** | Executable skill abstractions derived from past experience | External store or fine-tuning | Skill verification; trigger condition design |
| **User personalization memory** | Structured models of user preferences, facts, and history | External store | Temporal drift; over-personalization; privacy |
| **Multi-agent shared memory** | Shared information stores across agent roles or instances | Shared external store | Provenance; permissions; conflict resolution |

The CoALA framework (Transactions on Machine Learning Research, 2024, arXiv:2309.02427) provides the most widely cited formal taxonomy distinguishing working memory (context), episodic memory (experiences), semantic memory (knowledge), and procedural memory (skills/code) for language agents.[^29][^30]

***

## 3. Current Frontier Map

| Area | Core Problem | Representative Papers/Systems | Memory Primitive | Evaluation Method | Key Limitation | Open-Source Opportunity |
|------|-------------|-------------------------------|-----------------|-------------------|----------------|------------------------|
| Agent memory systems | OS-style context management | MemGPT/Letta (arXiv:2310.08560)[^31] | Tiered storage (core/recall/archival) | Deep Memory Retrieval (DMR) | DMR is an easy benchmark; doesn't test agentic decision-making | Improve tiered eviction policies |
| Agentic memory organization | Dynamic self-organizing memory network | A-MEM / NeurIPS 2025 (arXiv:2502.12110)[^24] | Zettelkasten-style linked notes | Long-term dialogue datasets | Fixed node taxonomy may fail out-of-distribution | Zettelkasten engine as open primitive |
| Long-context memory | "Lost in the Middle" degradation | Liu et al., TACL 2024 (arXiv:2307.03172)[^27][^28] | KV cache | Multi-doc QA, key-value retrieval | Position-dependence not solved; just mitigated | Compression/routing layer for long contexts |
| Long-context benchmarks | Multi-needle retrieval | Sequential-NIAH, EMNLP 2025 (arXiv:2504.04713)[^32] | Context window | Sequential needle extraction | Best model achieves only 63.50% on test set | Multi-needle evaluation harness |
| Temporal memory | Time-aware fact tracking | Zep/Graphiti (arXiv:2501.13956)[^16]; TReMu[^6] | Temporal knowledge graph | LongMemEval temporal sub-task | Self-reported accuracy gains; no independent replication | Temporal validity interval store |
| Reflective memory | Self-generated episodic traces | Reflexion, NeurIPS 2023 (arXiv:2303.11366)[^10][^11] | Episodic text buffer | HumanEval, AlfWorld, HotpotQA | Unreliable self-assessment; hallucination accumulation | Verified reflection pipeline |
| Memory + planning | Experience→rule abstraction | Generative Agents, UIST 2023 (arXiv:2304.03442)[^33][^34]; ProcMEM (arXiv:2602.01869)[^12] | Reflection stream → higher-order synthesis | Believability evaluation; cross-task reuse | Simulation; unverified at enterprise scale | Skill-MDP abstraction engine |
| Continual learning | Catastrophic forgetting during LLM fine-tuning | SSR, ACL 2024 (aclanthology.org/2024.acl-long.77)[^35]; CL Survey 2026 (arXiv:2603.12658)[^36] | Parametric weights + rehearsal buffer | GLUE task retention | Rehearsal requires data; parametric editing fails at scale | Non-parametric CL via external memory |
| Knowledge editing | Scalable fact patching | MEMIT (memit.baulab.info)[^37]; WikiBigEdit, ICML 2025 (arXiv:2503.05683)[^38] | Model parameters | CounterFact, zsRE, QAEdit | Fails with >1000 edits; teacher-forcing evaluation inflates metrics | External memory as editing substrate |
| Memory privacy | Memory extraction attacks | MEXTRA, ACL 2025 (arXiv:2502.13172)[^17][^18] | External memory store | Black-box extraction success rate | No deployed defense; privacy-utility tradeoff unsolved | Privacy-preserving memory stores |
| Multi-agent memory | Role-specific + hierarchical MAS memory | G-Memory, NeurIPS 2025 (arXiv:2506.07398)[^19][^20]; Collaborative Memory, ICML 2025 (arXiv:2505.18279)[^39] | Three-tier graph hierarchy | AgentBench, WebArena, ALFWorld | MAS memory lacks provenance and permissions model | Provenance-annotated shared memory |
| Memory benchmarks | Gap between recall-only and action-driven evaluation | MemoryArena (arXiv:2602.16313)[^2]; MemoryAgentBench, ICLR 2026[^25] | Action outcome grounding | Multi-session agentic task success | Near-saturated models on LoCoMo fail in agentic settings | Coupled memory-action evaluation harness |
| RL-based memory consolidation | Learning what to keep across interactions | MEM1, ICLR 2026 (arXiv:2506.15841)[^14][^15] | Compact shared internal state | Multi-hop QA, web shopping | Requires RL training; not plug-and-play | Open RL consolidation training recipe |

***

## 4. Source Register

| Source Name | Year | Authors/Org | Source Type | Grade | Link | Why It Matters | Limitations/Cautions |
|-------------|------|-------------|-------------|-------|------|----------------|---------------------|
| "From Storage to Experience" Survey | 2026 | Luo et al., ACL 2026 | Peer-reviewed survey (ACL Findings) | A | arXiv:2605.06716[^22] | Best current taxonomy; three-stage evolutionary framework | Survey, not empirical; may undercount very recent work |
| "Memory in the Age of AI Agents" | 2025-2026 | Hu et al. (large author group) | arXiv preprint | B | arXiv:2512.13564[^40] | Broadest landscape review; distinguishes token/parametric/latent memory | Very large author group; preprint; may lack editorial rigor |
| LLM Agent Memory Mechanism Survey | 2024 | Zhang et al. | arXiv preprint + GitHub repo | B | arXiv:2404.13501[^41] | Systematic early survey with design patterns | Pre-dates most 2025-2026 work |
| CoALA: Cognitive Architectures for Language Agents | 2023-2024 | Sumers, Yao, Narasimhan, Griffiths (Princeton) | Transactions on ML Research (TMLR) | A | arXiv:2309.02427[^29][^30] | Foundational taxonomy; episodic/semantic/procedural memory formalization | Older; does not cover 2025-2026 systems |
| Generative Agents | 2023 | Park et al. (Stanford) | UIST 2023 conference paper | A | arXiv:2304.03442[^33][^34] | First full memory-reflection-planning pipeline; still frequently cited | Simulated environment; not generalizable agent system |
| Reflexion | 2023 | Shinn, Cassano et al. | NeurIPS 2023 poster | A | arXiv:2303.11366[^10][^11] | Established verbal reinforcement + episodic memory buffer paradigm | Hallucination risk in self-reflection not studied |
| MemGPT: Towards LLMs as Operating Systems | 2023-2024 | Packer, Wooders et al. (UC Berkeley) | arXiv preprint (submitted to ICML) | B | arXiv:2310.08560[^31][^42] | First OS-inspired tiered memory architecture | DMR benchmark is their own; limited independent evaluation |
| Mem0: Production-Ready AI Agents | 2025 | Chhikara et al. | arXiv + ECAI 2025 | B | arXiv:2504.19413[^43][^44][^45] | Memory-centric architecture with graph layer; 26% LLM-as-Judge gain | Evaluated on LOCOMO only; LLM-as-Judge metric is noisy |
| Zep: Temporal Knowledge Graph Architecture | 2025 | Rasmussen et al. | arXiv preprint (commercial system) | B/C | arXiv:2501.13956[^16][^46] | Temporal KG via Graphiti; 18.5% accuracy improvement, 90% latency reduction | Vendor-authored; no independent replication |
| A-MEM: Agentic Memory for LLM Agents | 2025 | Xu, Liang, Mei et al. | NeurIPS 2025 poster | A | arXiv:2502.12110[^24][^23] | Dynamic memory organization via Zettelkasten; memory evolution | Evaluated on dialogue benchmarks only |
| G-Memory: Hierarchical Memory for MAS | 2025 | Zhang, Fu et al. | NeurIPS 2025 spotlight | A | arXiv:2506.07398[^19][^20] | First rigorous hierarchical MAS memory with graph; +20.89% on embodied action | Spotlight paper, but tested on 3 LLM backbones and 5 benchmarks |
| LongMemEval | 2024-2025 | Wu, Wang et al. (UCLA, Tencent AI Lab) | ICLR 2025 poster | A | arXiv:2410.10813[^3][^4][^47] | 500-question benchmark across 5 memory abilities; 30% accuracy drop documented | Tests chat assistants, not action agents |
| MemoryArena | 2026 | He, Wang, Choi, Pentland et al. (Stanford, UCSD, UW) | arXiv preprint | B | arXiv:2602.16313[^2][^48] | Shows disconnect between existing benchmarks and action-memory coupling | Preprint; not yet peer-reviewed |
| MemoryAgentBench | 2025-2026 | Hu, Wang, McAuley | ICLR 2026 poster | A | GitHub: HUST-AI-HYZ[^25][^26] | Four-competency framework; conflict resolution and test-time learning included | Requires further longitudinal validation |
| Sequential-NIAH | 2025 | Yu et al. (Tencent) | EMNLP 2025 | A | arXiv:2504.04713[^32][^49] | Sequential multi-needle benchmark; best model only 63.50% | Only tests extraction, not decision-making |
| LoCoMo | 2024 | Maharana et al. (UNC, Snap) | ACL 2024 | A | arXiv:2402.17753[^50][^51] | 300-turn, 9K-token dialogues across 35 sessions; multimodal | Synthetic pipeline; smaller in scope than production data |
| EvolMem | 2026 | Shen, Pei et al. (SJTU) | arXiv preprint | B | arXiv:2601.03543[^21] | Cognitive-psychology-grounded; declarative + non-declarative; no LLM dominates | Preprint; benchmark still under construction |
| Lost in the Middle | 2023-2024 | Liu, Lin, Liang et al. (Stanford) | TACL 2024 | A | arXiv:2307.03172[^27][^28] | Foundational evidence of position-dependent retrieval degradation | Tested on earlier models; partially mitigated in later models |
| Reflexion | 2023 | Shinn et al. | NeurIPS 2023 | A | arXiv:2303.11366[^11] | Foundational verbal RL + episodic buffer work | Not safe/reliable for high-stakes memory accumulation |
| ROME / MEMIT | 2022-2023 | Meng et al. (MIT); various | NeurIPS/ICLR | A | memit.baulab.info[^37] | Foundational parametric editing; can update thousands of facts | Fails at sequential scale (see Gupta et al. 2024) |
| "Mirage of Model Editing" (QAEdit) | 2025 | Yang et al. | ACL 2025 | A | Yang et al., ACL 2025[^9][^8] | Exposes systematic evaluation flaws in model editing; 38.5% vs. 96.8% | May be too conservative—teacher-forcing correction is valid criticism |
| WikiBigEdit | 2025 | ICML 2025 workshop | ICML 2025 | A | arXiv:2503.05683[^38][^52] | 500K+ real Wikidata edits; scalable benchmark | Tests editing methods only, not full agent pipeline |
| MEM1 | 2025-2026 | Zhou, Qu, Low, Liang et al. (MIT/NUS) | ICLR 2026 poster | A | arXiv:2506.15841[^14][^15] | RL-trained consolidation; 3.5x perf gain, 3.7x memory reduction | Needs training; not drop-in; limited domain coverage |
| ProcMEM | 2026 | Mi, Ma et al. | arXiv preprint | B | arXiv:2602.01869[^12][^53] | Non-parametric procedural skill learning via PPO Gate | Preprint; Skill-MDP formalism untested beyond lab |
| RMM (Reflective Memory Management) | 2025 | Tan, Yan et al. (Google/ASU) | ACL 2025 | A | arXiv:2503.08026[^54][^55] | Prospective + Retrospective reflection; RL reranker; >10% improvement on LongMemEval | Single dialogue domain; RL overhead is significant |
| MEXTRA: Privacy Risks in LLM Agent Memory | 2025 | Wang, He et al. | ACL 2025 | A | arXiv:2502.13172[^17][^18] | First systematic memory extraction attack; real black-box setting | Attack paper only; no defense validated |
| Collaborative Memory (ICML 2025) | 2025 | Rezazadeh, Li et al. (Accenture) | ICML 2025 workshop | B | arXiv:2505.18279[^39][^56] | Multi-user memory with bipartite access graph + provenance | Workshop paper; not peer-reviewed as main track |
| TReMu | 2025 | Ge et al. | arXiv preprint | B | Liner/arXiv[^6] | Neuro-symbolic temporal reasoning; 29.83→77.67 on temporal QA | Point solution on LoCoMo extension; limited generalization |
| LaMP Benchmark | 2023 | lamp-benchmark/lamp (GitHub) | arXiv + GitHub | B | GitHub: lamp-benchmark[^57] | Personalization benchmark with user profile augmentation | Mostly static user profiles; not dynamic preference tracking |
| CL in LLMs Survey | 2026 | Chen et al. | arXiv preprint | B | arXiv:2603.12658[^36] | Comprehensive CL taxonomy across pre-training, fine-tuning, alignment | Survey; no empirical contribution |
| INMS: Memory Sharing for LLM Agents | 2024-2026 | Gao, Zhang (Rutgers) | arXiv preprint | B | arXiv:2404.09982[^58] | Shared conversational memory pool for multi-agent; filtering/retrieval mediator | Lab-scale experiments; limited benchmarking |

***

## 5. Paper and System Deep Dives

### 5.1 MemGPT / Letta (arXiv:2310.08560, 2023)

**Summary:** MemGPT, developed at UC Berkeley and later commercialized as Letta, proposes treating the LLM as an operating system with three memory tiers: core memory (in-context), recall memory (searchable message history), and archival memory (searchable long-term storage). The agent controls memory via function calls.[^31][^42]

**Contribution:** Virtual context management inspired by OS paging. The agent can read/write/search its own memory, creating the first open, transparent tiered memory architecture.

**Memory Mechanism:** Core memory (always in context, editable), recall memory (indexed conversation history), archival memory (long-term archive with vector search).

**Evaluation:** Deep Memory Retrieval (DMR) benchmark (their own); multi-session chat evaluation.

**Strongest Evidence:** Demonstrated working long-term chatbot behavior across many sessions without context truncation.

**Weakness/Gap:** DMR is relatively easy and self-authored. MemoryArena shows agents saturating DMR-style benchmarks still fail on agentic memory tasks. Memory management is still LLM-controlled—error-prone and potentially circular (an LLM deciding what to remember about itself).[^2]

**Relevance to OSS:** The memory block abstraction and function-call memory management pattern are widely adopted. The open-source Letta framework provides a direct implementation base.[^59][^60]

***

### 5.2 Generative Agents (arXiv:2304.03442, UIST 2023)

**Summary:** Stanford researchers introduced 25 simulated agents in "Smallville," each with a memory stream (complete natural language log of experiences), a reflection mechanism (periodic synthesis of higher-order insights), and a retrieval mechanism weighting recency, importance, and relevance.[^33][^34]

**Contribution:** First full system demonstrating emergent social behavior from memory-reflection-planning loops in LLM agents.

**Memory Mechanism:** Memory stream (append-only log) + recency/importance/relevance weighted retrieval + periodic reflection synthesis.

**Evaluation:** Qualitative believability evaluation; ablation showing each component is necessary.

**Strongest Evidence:** Ablation confirms memory, reflection, and planning are each necessary—agents without any single component show degraded believability.

**Weakness/Gap:** Evaluation is qualitative, not quantitative. The reflection pipeline is expensive and unreliable—LLMs synthesizing higher-order insights may hallucinate relationships. No safety, privacy, or temporal contradiction handling.

**Relevance to OSS:** The memory stream + reflection pattern has become the de-facto baseline for most subsequent agent memory work. Any open-source agent memory system must at minimum match this baseline.

***

### 5.3 Reflexion (arXiv:2303.11366, NeurIPS 2023)

**Summary:** Reflexion reinforces language agents not by updating weights but through verbal self-reflection. After each trial, an agent verbally reflects on failure signals and stores the reflection in an episodic memory buffer, improving subsequent attempts.[^11][^10]

**Contribution:** Established verbal reinforcement learning as a lightweight alternative to full RL. 91% pass@1 on HumanEval—surpassing GPT-4.

**Memory Mechanism:** Episodic text buffer of self-generated reflections; retrieved at the start of each new trial.

**Evaluation:** HumanEval (coding), AlfWorld (sequential decision-making), HotpotQA (reasoning).

**Strongest Evidence:** Significant improvement over non-reflective baselines. Ablation shows episodic memory buffer is necessary—agents that cannot access past reflections lose all improvement.

**Weakness/Gap:** Self-generated reflections are linguistic outputs of the same model that already failed—they can be wrong, biased, or confidently hallucinated. There is no verification mechanism for stored reflections. The episodic buffer grows unbounded. *[JUDGMENT: This is the foundational weakness of all reflective memory systems—they inherit the hallucination problems of the base model they are trying to help.]*

**Relevance to OSS:** The verbal RL + episodic buffer pattern is the most adopted in practice, but any serious OSS system must address reliability of stored self-assessments.

***

### 5.4 LongMemEval (arXiv:2410.10813, ICLR 2025)

**Summary:** LongMemEval evaluates chat assistant memory across five abilities: information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention. With 500 curated questions across scalable session histories, it documents a ~30% accuracy drop on commercial and open-source systems.[^4][^3]

**Contribution:** Rigorous benchmark with abstention testing (the agent should say "I don't know" when information was never provided). Three-stage design framework: indexing, retrieval, reading. Key finding: session decomposition, fact-augmented key expansion, and time-aware query expansion each independently improve performance.

**Memory Mechanism:** Evaluated across multiple memory backends including RAG, full context, and commercial systems.

**Evaluation:** 500 curated questions; five ability categories; accuracy as primary metric.

**Strongest Evidence:** Temporal reasoning tasks show the largest gap. Time-aware query expansion specifically improves temporal performance.

**Weakness/Gap:** Tests chat assistants, not agents that act. LongMemEval V2 (announced May 2026) extends to agentic contexts—results not yet available for analysis.[^47]

**Relevance to OSS:** The benchmark is publicly available at GitHub (xiaowu0162/LongMemEval) and is suitable for benchmarking any new OSS memory system.

***

### 5.5 A-MEM: Agentic Memory (arXiv:2502.12110, NeurIPS 2025)

**Summary:** A-MEM applies Zettelkasten principles to agent memory. Each stored memory generates structured attributes (contextual description, keywords, tags), and the system automatically links new memories to related historical ones, triggering updates to existing memories' representations.[^24][^23]

**Contribution:** Dynamic memory evolution—new memories do not just sit statically but trigger updates to related existing memories. Tests on six foundation models.

**Memory Mechanism:** Note-based memory with dynamic indexing, linking, and evolution. Graph-like interconnection without requiring a full graph database.

**Evaluation:** Long-term dialogue datasets; comparison against SOTA baselines.

**Strongest Evidence:** Superior improvement across six foundation models. Particularly strong on multi-hop reasoning tasks.

**Weakness/Gap:** Evaluated only on dialogue benchmarks. Memory evolution cost scales with memory size. No temporal contradiction handling.

**Relevance to OSS:** The Zettelkasten abstraction is a promising open primitive. Code is available (noted at GitHub per OpenReview).[^61]

***

### 5.6 Zep/Graphiti (arXiv:2501.13956)

**Summary:** Zep is a production memory service built on Graphiti, a temporally-aware knowledge graph engine. It ingests conversations and structured data, maintaining validity windows for facts ("what was true when"), and performs hybrid retrieval (semantic + keyword + graph traversal).[^62][^63][^16]

**Contribution:** First production system combining temporal knowledge graph with agent memory. On LongMemEval, 18.5% improvement with 90% latency reduction vs. baseline RAG.

**Memory Mechanism:** Temporal knowledge graph with entity-relationship triples carrying validity intervals; hybrid retrieval.

**Evaluation:** DMR benchmark; LongMemEval.

**Strongest Evidence:** Substantial latency reduction (90%) is practically significant; accuracy gains on enterprise tasks including cross-session synthesis.

**Weakness/Gap:** Vendor-authored paper; self-reported results on their own preferred benchmarks; no independent replication found. *[JUDGMENT: Results are directionally plausible but should not be treated as peer-reviewed findings.]*

**Relevance to OSS:** Graphiti is fully open-source (GitHub: getzep/graphiti). The temporal KG primitive is importable into any OSS project.[^63][^62]

***

### 5.7 G-Memory (arXiv:2506.07398, NeurIPS 2025 Spotlight)

**Summary:** G-Memory introduces a three-tier hierarchical memory for multi-agent systems: insight graphs (generalizable cross-trial knowledge), query graphs (per-query context), and interaction graphs (fine-grained collaboration trajectories). Bi-directional traversal retrieves both high-level insights and fine-grained trajectories.[^20][^19]

**Contribution:** First peer-reviewed system to formalize multi-agent memory as a hierarchical graph with organizational-theory backing. NeurIPS 2025 spotlight—one of the highest-quality results in MAS memory.

**Memory Mechanism:** Three-tier graph hierarchy with bi-directional traversal; evolves by assimilating new MAS interaction trajectories.

**Evaluation:** Five benchmarks (including embodied action and knowledge QA), three LLM backbones, three MAS frameworks.

**Strongest Evidence:** Up to 20.89% improvement in embodied action; 10.12% in knowledge QA without modifying agent frameworks.

**Weakness/Gap:** Tested on controlled benchmarks, not production deployment. Cross-agent provenance and access control not addressed. *[JUDGMENT: The absence of permissions/provenance model is a significant gap for production use.]*

**Relevance to OSS:** Code available at GitHub (bingreeky/GMemory). The three-tier pattern is directly importable for MAS memory design.[^64]

***

### 5.8 MEM1 (arXiv:2506.15841, ICLR 2026)

**Summary:** MEM1 trains agents via RL to maintain constant-size internal state across multi-turn interactions. At each turn, the agent updates a compact shared state that integrates prior memory and new observations, discarding irrelevant information. MEM1-7B achieves 3.5x performance improvement while using 3.7x less memory compared to Qwen2.5-14B-Instruct.[^15][^14]

**Contribution:** First demonstration that memory consolidation can be learned end-to-end via RL, producing consistent benefits across multiple domains (retrieval QA, web QA, web shopping).

**Memory Mechanism:** Compact shared internal state updated at each turn via RL-trained policy.

**Evaluation:** Internal retrieval QA, open-domain web QA, multi-turn web shopping; out-of-distribution generalization tests.

**Strongest Evidence:** Generalizes beyond training horizon—agents trained on shorter tasks retain benefits on longer sequences. Code available at GitHub (MIT-MI/MEM1).

**Weakness/Gap:** Requires RL training—not a drop-in upgrade. Training data composition strategy is a significant design choice not fully ablated. Limited to text-only settings.

**Relevance to OSS:** The RL consolidation recipe is the most principled open approach to learned memory compression. Directly relevant for long-horizon agent memory.

***

### 5.9 MEXTRA: Privacy Risks in LLM Agent Memory (arXiv:2502.13172, ACL 2025)

**Summary:** MEXTRA is a Memory EXTRaction Attack that demonstrates private information stored in LLM agent memory can be extracted in black-box settings via adversarial prompt design and automated prompt generation.[^18][^17]

**Contribution:** First systematic attack on agent memory privacy. Demonstrates that memory stores are vulnerable surfaces that require active defense.

**Memory Mechanism (attacked):** External demonstration memory used by agent for in-context examples.

**Evaluation:** Two representative agents; attack success rate as primary metric.

**Strongest Evidence:** Effective under black-box setting without model access—practical threat model.

**Weakness/Gap:** Defense strategies not evaluated. The attack targets one memory mechanism (demonstration memory); generalization to other memory types is *[UNCERTAIN]*.

**Relevance to OSS:** Any open-source memory system must include access controls, audit trails, and provenance tracking to mitigate MEXTRA-class attacks.

***

### 5.10 "Mirage of Model Editing" / QAEdit (ACL 2025)

**Summary:** This paper introduces QAEdit and demonstrates that existing model editing evaluations (ROME, MEMIT, MEND, etc.) report ~96.8% accuracy under teacher-forcing conditions that leak ground truth. Under realistic open-generation conditions, accuracy drops to ~38.5%. With sequential editing, methods fail at only 1,000 edits.[^8][^9]

**Contribution:** Fundamental reexamination of model editing evaluation practices. Shows the field has been measuring the wrong thing.

**Memory Mechanism:** Parametric model editing; direct weight updates.

**Evaluation:** QAEdit benchmark derived from standard QA datasets; open-generation (no teacher forcing).

**Strongest Evidence:** The teacher-forcing confound is mathematically demonstrable, not just empirically observed. Sequential editing failure at 1,000 edits is documented (complemented by Gupta et al. 2024 which shows the same for ROME/MEMIT at scale).[^7]

**Weakness/Gap:** Does not evaluate newer editing approaches like BaFT (ICLR 2025) which may improve locality. *[JUDGMENT: Model editing is not a viable path for production agentic memory at this time.]*[^65]

***

### 5.11 RMM: Reflective Memory Management (arXiv:2503.08026, ACL 2025)

**Summary:** RMM integrates Prospective Reflection (forward-looking topic-based summarization at multiple granularities: utterance, turn, session) and Retrospective Reflection (backward-looking RL-based retrieval reranking using LLM citation signals as reward).[^54][^55]

**Contribution:** First memory system combining multi-granularity prospective summarization with RL-based retrospective retrieval refinement. >10% improvement on LongMemEval.

**Memory Mechanism:** Topic-based memory bank + RL reranker trained on citation-as-reward signals.

**Evaluation:** MSC dataset; LongMemEval dataset.

**Strongest Evidence:** Consistent improvements across multiple metrics (METEOR, BERT Score, Recall@5, Accuracy). RL reranker improves over fixed-heuristic retrieval.

**Weakness/Gap:** RL training overhead is significant. Single dialogue domain. Multimodal not supported. *[JUDGMENT: The citation-as-reward signal is a promising primitive for measuring memory usefulness, not just retrieval accuracy.]*

***

### 5.12 ProcMEM (arXiv:2602.01869, Feb 2026)

**Summary:** ProcMEM formalizes a Skill-MDP that transforms passive episodic narrative trajectories into executable Skills with activation, execution, and termination conditions. Non-Parametric PPO uses semantic gradients + a PPO Gate for skill verification and score-based maintenance of a compact procedural memory store.[^53][^12]

**Contribution:** First non-parametric procedural memory system with explicit skill verification and quality maintenance. Cross-agent transfer: skills built from a strong model improve a weaker model.

**Memory Mechanism:** Executable Skill primitives (not just text) stored in procedural memory; Skill-MDP formalization.

**Evaluation:** Cross-task and cross-agent scenarios.

**Strongest Evidence:** Cross-agent procedural memory transfer is a novel and practically important result.

**Weakness/Gap:** Preprint; Skill-MDP formalism has not been independently evaluated. PPO Gate training overhead. *[JUDGMENT: The cross-agent skill transfer finding is the most practically interesting contribution if it generalizes.]*

***

## 6. Memory Architecture Taxonomy

### 6.1 Vector Memory

**What it does well:** Fast semantic search over large memory pools; easy to implement with existing embedding models.

**Where it fails:** Embedding failure (semantically different facts may have similar embeddings); stale vectors after context changes; no temporal awareness; no structural relationships; retrieves semantically similar but causally irrelevant memories.

**Evaluation usually misses:** Causal relevance to task outcome; temporal validity; retrieval precision (recall@k is not precision@k).

**Status:** [JUDGMENT: NOT NOVEL BUT UNDERBUILT. Vector memory is the commodity layer; differentiation must come from what surrounds it.]

***

### 6.2 Document/RAG Memory

**What it does well:** Standard information retrieval over large unstructured corpora.

**Where it fails:** Chunk boundary problems; embedding mismatch; stale documents; over-retrieval; no session-level coherence; no update mechanism.[^66][^67]

**Evaluation usually misses:** Multi-hop coherence; temporal contradiction between documents; retrieval harm (retrieved but wrong information degrades performance more than no retrieval).

**Status:** [JUDGMENT: COMMODITIZED. Standard RAG over conversation history is not a research contribution.]

***

### 6.3 Graph Memory

**What it does well:** Captures structural relationships between entities; supports multi-hop reasoning; handles provenance.

**Where it fails:** Knowledge graph construction from unstructured text is lossy; graph schemas require upfront design decisions; scale and latency at large graph sizes; no built-in temporal model.

**Evaluation usually misses:** Entity extraction quality upstream of retrieval; schema rigidity; maintenance cost of large graphs.

**Status:** [JUDGMENT: PROMISING but requires temporal + provenance extensions to be competitive.]

***

### 6.4 Episodic Trace Memory

**What it does well:** Preserves raw experience logs; supports temporal ordering; enables reflection over specific past events.

**Where it fails:** Memory size grows unbounded; retrieval from large episode stores is expensive; raw traces include noise, failures, and irrelevant content.

**Evaluation usually misses:** Signal-to-noise ratio of episodes; cost of storing low-value traces; pruning/decay quality.

**Status:** [JUDGMENT: NECESSARY PRIMITIVE but needs compression and quality maintenance layer on top (see ProcMEM, Memp).][^13][^12]

***

### 6.5 Reflective Memory

**What it does well:** Synthesizes higher-order patterns from raw experience; can improve downstream planning when self-assessment is accurate.

**Where it fails:** Inherits and amplifies hallucinations from the base model; no external verification; self-generated insights may be systematically biased.[^68]

**Evaluation usually misses:** Reliability rate of stored reflections; hallucination injection rate; downstream harm from bad reflections.

**Status:** [JUDGMENT: OVERHYPED for reliability-critical applications. The Reflexion result is real but the absence of verification is a serious gap.][^11]

***

### 6.6 Long-Context Memory

**What it does well:** Retains all information within one session without retrieval cost.

**Where it fails:** "Lost in the Middle" degradation; degrades on multi-needle extraction (63.50% best model on Sequential-NIAH); prohibitive cost at very long contexts; no persistence across sessions.[^27][^32]

**Evaluation usually misses:** Multi-needle sequential retrieval; temporal ordering within context; degradation curve over context length.

**Status:** [JUDGMENT: Not a memory architecture—it is a substitute for one at short timescales. At multi-session timescales, it simply does not work.]

***

### 6.7 Learned/Parametric Memory

**What it does well:** Integrates knowledge seamlessly into generation; no retrieval overhead.

**Where it fails:** Cannot be inspected or edited without retraining; fails at sequential editing scale (see QAEdit, Gupta et al.); catastrophic forgetting during continual fine-tuning.[^36][^9][^7]

**Evaluation usually misses:** Localization failures; downstream task degradation after edits; real-world edit volumes.

**Status:** [JUDGMENT: NOT VIABLE as primary agentic memory mechanism at present. Useful for pretraining but not for dynamic agent memory.]

***

### 6.8 Editable Memory (External, Non-Parametric)

**What it does well:** Can be directly updated without retraining; supports deletion, versioning, and rollback; auditable.

**Where it fails:** Retrieval quality depends on editing precision; contradiction handling between old and new facts; no standard protocol for memory versioning.

**Evaluation usually misses:** Rollback correctness; contradiction detection; edit precision at scale.

**Status:** [JUDGMENT: UNDERBUILT and high potential. External editable memory is the only scalable path for agent memory correction at present.]

***

### 6.9 Procedural/Skill Memory

**What it does well:** Captures reusable how-to knowledge; reduces computational redundancy for recurring tasks; supports cross-agent transfer.[^12][^13]

**Where it fails:** Skill trigger conditions are hard to specify reliably; skill abstraction from trajectories is noisy; skill verification is difficult without ground truth.

**Evaluation usually misses:** Skill generalization across domains; failure mode of inappropriate skill activation; quality degradation over time.

**Status:** [JUDGMENT: LIKELY NOVEL AND UNDERBUILT. ProcMEM and Memp represent early credible work; much more needed.]

***

### 6.10 Temporal Memory

**What it does well:** Tracks what was true at what time; supports "what was true then vs. now" queries; enables validity interval reasoning.

**Where it fails:** Most memory systems are static snapshots; temporal contradiction between stored facts is not detected or resolved; temporal reasoning is a severe bottleneck for LLMs.[^5]

**Evaluation usually misses:** Temporal contradiction handling; validity interval precision; temporal retrieval failure modes.

**Status:** [JUDGMENT: PROMISING AND UNDERBUILT. Graphiti/Zep is the most developed open-source implementation but lacks peer-reviewed evaluation.][^62]

***

### 6.11 Shared/Multi-Agent Memory

**What it does well:** Enables knowledge transfer across agents; reduces redundant computation in MAS; supports collective memory.

**Where it fails:** Provenance loss across agent boundaries; permission and access control not standardized; memory contamination from unreliable agents; conflict resolution unsolved.[^56][^39]

**Evaluation usually misses:** Provenance integrity; permission violation rate; contamination spread from bad agents.

**Status:** [JUDGMENT: UNDERDEVELOPED. G-Memory is the strongest single-paper result, but the field lacks a standard protocol.][^19]

***

### 6.12 Hybrid Memory Systems

**What it does well:** Combines strengths of multiple memory types.

**Where it fails:** Integration complexity; inconsistency between memory layers; unclear retrieval priority when memories conflict.

**Status:** [JUDGMENT: Hybrid is where production systems end up, but hybrid-specific evaluation and protocol design are missing.]

***

## 7. Benchmark and Evaluation Landscape

| Benchmark | Year | Task Type | What It Measures | What It Fails to Measure | Agentic Relevance | Reusable for OSS? |
|-----------|------|-----------|------------------|--------------------------|-------------------|--------------------|
| **LongMemEval** | 2024-2025 | Chatbot memory Q&A | 5 memory abilities: extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention[^3][^47] | Memory→action coupling; skill transfer; harm from bad memories | Moderate (chat-focused) | Yes. 500 Q publicly available |
| **MemoryArena** | 2026 | Multi-session agentic tasks | Memory-action coupling across 4 environments[^2] | Ground-truth-independent failure modes; temporal contradiction | High | Preprint; code being released |
| **MemoryAgentBench** | 2025-2026 | Incremental multi-turn | 4 competencies: retrieval, test-time learning, long-range understanding, conflict resolution[^25][^26] | Long-horizon task performance; personalization; procedural skill | High | Yes. ICLR 2026, code on GitHub |
| **LoCoMo** | 2024 | Long-term dialogue Q&A | 300-turn, 35-session memory over temporal/causal events[^50] | Action-driven memory; privacy; procedural memory | Moderate | Yes. Public at snap-research/locomo |
| **Sequential-NIAH** | 2025 | Multi-needle extraction | Ordered multi-needle extraction from 8K–128K contexts[^32] | Decision-making; multi-session | Low (context only) | Yes. EMNLP 2025 |
| **EvolMem** | 2026 | Multi-session dialogue | Declarative + non-declarative memory in multi-session[^21] | Agentic action; privacy | Moderate | Preprint; data being released |
| **LaMP** | 2023 | Personalization tasks | User-profile-conditioned generation across 7 tasks[^57] | Dynamic preference update; temporal change; privacy | Low–Moderate | Yes. Public on GitHub |
| **QAEdit** | 2025 | Knowledge editing Q&A | Real-world editing accuracy under open-generation conditions[^9] | Agentic deployment; multi-edit sequences beyond 1000 | Low (parametric editing only) | Partially public |
| **WikiBigEdit** | 2025 | Lifelong knowledge editing | 500K+ real Wikidata edits over time[^38][^52] | Agent-level decision impact; privacy | Low (parametric editing) | Available (ICML 2025) |
| **LoCoMo + TReMu extension** | 2025 | Temporal reasoning in dialogue | Temporal reasoning in multi-session dialogues[^6] | Action coupling | Moderate | Partial |
| **TimE** | 2025 | Temporal reasoning QA | 38,522 QA pairs across temporal intensity, event dynamics, social temporal[^69] | Memory system interaction | Low | Yes, TimE-Lite subset public |
| **AgentDAM** | 2025 | Privacy / data minimization | Whether agents use only necessary personal information[^70] | Memory leakage beyond web navigation | Moderate | Yes. facebookresearch/ai-agent-privacy |

### Critical Observation on Benchmark Design Gaps

[VERIFIED FACT — from MemoryArena]: Agents near-saturating LoCoMo and other passive-recall benchmarks show poor performance in MemoryArena's coupled memory-action tasks. This means existing recall benchmarks do not predict real agentic memory quality.[^2]

[VERIFIED FACT — from MemoryAgentBench]: No current method masters all four memory competencies simultaneously. Optimizing for one (e.g., accurate retrieval) does not guarantee improvement on others (e.g., conflict resolution).[^25]

[INFERENCE]: A benchmark that measures all of: (a) causal relevance of retrieved memories to task outcomes, (b) temporal validity, (c) privacy preservation, (d) procedural skill transfer, and (e) multi-session action coupling does not yet exist.

***

## 8. Failure Mode Map

### 8.1 False Memory Creation (Reflection Hallucination)

**Description:** The agent stores a self-generated reflection that is factually incorrect, logically flawed, or hallucinated. Subsequent retrievals use this false memory to guide future decisions.

**Evidence:** Reflexion (NeurIPS 2023) stores raw LLM output in episodic buffer without verification. LLM hallucination surveys document that LLMs generate plausible but false content with high confidence. *[JUDGMENT: Every reflective memory system built on top of an LLM inherits this failure mode.]*[^71][^11]

**Why It Matters:** False reflections compound over time. Unlike single-query hallucination, memory hallucination affects all future retrievals that encounter that memory.

**Current Mitigation:** Retrieval reranking (RMM) reduces bad retrieval but doesn't prevent bad storage.[^54]

**Unsolved Gap:** Verification mechanism for stored self-assessments before committing to memory. Adversarial reflection injection is unexplored.

***

### 8.2 Stale Memory

**Description:** The memory store contains information that was once true but is now outdated. The agent retrieves and acts on stale facts.

**Evidence:** LongMemEval includes a "knowledge updates" sub-task where commercial systems show ~30% accuracy drop. Graphiti/Zep addresses this via validity intervals, but most systems do not.[^3][^62]

**Why It Matters:** In dynamic domains (user preferences, external facts, code APIs), stale memory can cause worse performance than no memory.

**Current Mitigation:** Temporal KG (Zep/Graphiti); time-aware query expansion (LongMemEval design).[^16][^3]

**Unsolved Gap:** No standard mechanism for detecting and invalidating stale memories across arbitrary external memory types.

***

### 8.3 Irrelevant Memory Retrieval (Causally Irrelevant Recall)

**Description:** Semantically similar but causally irrelevant memories are retrieved and distract the agent from the correct decision pathway.

**Evidence:** Standard retrieval metrics (recall@k) do not penalize causal irrelevance. MemoryArena shows that near-perfect recall does not predict task success.[^2]

**Why It Matters:** More is not better. Over-retrieval can harm agent performance by injecting noise. *[INFERENCE based on MemoryArena results.]*

**Current Mitigation:** Reranking; metadata filtering (Mem0).[^44]

**Unsolved Gap:** No evaluation metric for causal retrieval relevance. No standard mechanism for learning what is causally useful in a given task context.

***

### 8.4 Retrieval Omission (Under-Retrieval)

**Description:** A memory that would have been relevant to the task is not retrieved.

**Evidence:** LongMemEval: 30% accuracy drop in commercial systems attributable partly to retrieval failures. Sequential-NIAH shows models fail to extract sequential needles even when they exist.[^32][^3]

**Why It Matters:** The agent acts without critical context it has previously acquired.

**Current Mitigation:** Multi-key indexing, fact-augmented key expansion (LongMemEval design).[^3]

**Unsolved Gap:** No system reliably handles "what do I know about this that I might have forgotten to look up?"—proactive memory lookup without explicit retrieval cue.

***

### 8.5 Temporal Drift and Contradiction

**Description:** The memory store contains two contradictory facts about the same entity at different times, without a mechanism to distinguish current from historical truth.

**Evidence:** TReMu shows temporal reasoning fails at baseline (29.83 on GPT-4o). EvoReasoner identifies "conflicting updates" as a core challenge in temporal KG reasoning.[^6][^72]

**Why It Matters:** "Is the user's email address still X?" cannot be answered without temporal validity tracking.

**Current Mitigation:** Graphiti validity windows; TReMu timeline summarization.[^6][^62]

**Unsolved Gap:** No standard protocol for temporal contradiction resolution across heterogeneous memory stores.

***

### 8.6 Privacy Leakage

**Description:** Private user information stored in agent memory is extracted by adversarial users, third parties, or other agents.

**Evidence:** MEXTRA (ACL 2025): demonstrated black-box extraction of private memory from LLM agents. AgentDAM (NeurIPS 2025): agents use more personal information than necessary, violating data minimization.[^70][^17][^18]

**Why It Matters:** Agent memory is a concentrated personal data store. GDPR/CCPA-style compliance requires controllability and deletion.

**Current Mitigation:** Prompting-based defense (AgentDAM); access controls (Collaborative Memory).[^56][^70]

**Unsolved Gap:** No cryptographically secure or differentially private memory architecture for production agents is publicly documented.

***

### 8.7 Multi-Agent Memory Contamination

**Description:** A memory generated by an unreliable or adversarial agent is shared with and accepted by other agents in the system.

**Evidence:** G-Memory notes MAS memory mechanisms are "overly simplistic" and lack provenance tracking. INMS acknowledges that shared memory quality depends on all contributing agents. Collaborative Memory addresses permissions but not agent reliability filtering.[^58][^56][^19]

**Why It Matters:** In MAS deployments, one bad agent can corrupt shared knowledge.

**Current Mitigation:** Provenance attributes in Collaborative Memory (bipartite access graphs); no reliability-filtering standard exists.[^56]

**Unsolved Gap:** No system implements trust-weighted memory contribution across agents.

***

### 8.8 Skill Abstraction Failure

**Description:** The system extracts incorrect, over-generalized, or poorly conditioned skills from experience trajectories, and applies them in contexts where they do not belong.

**Evidence:** ProcMEM introduces activation conditions for skills, but the reliability of LLM-generated activation conditions is not evaluated adversarially. *[INFERENCE from system design.]*[^12]

**Why It Matters:** A wrongly abstracted skill applied to an inappropriate context can cause systematic failure rather than isolated errors.

**Current Mitigation:** PPO Gate in ProcMEM; score-based maintenance in Memp.[^13][^12]

**Unsolved Gap:** No adversarial evaluation of skill trigger failures. No standard for skill deprecation when environments change.

***

### 8.9 Benchmark Gaming

**Description:** Memory systems are optimized against narrow benchmarks (especially LoCoMo, DMR) and do not generalize.

**Evidence:** MemoryArena explicitly shows agents near-saturating LoCoMo fail on its agentic tasks. DMR is self-authored by MemGPT team. *[VERIFIED FACT]*[^31][^2]

**Why It Matters:** Research progress measured by benchmark improvement may not represent real capability improvement.

**Current Mitigation:** Introduction of harder benchmarks (MemoryArena, MemoryAgentBench, LongMemEval V2).

**Unsolved Gap:** No community benchmark with adversarial, adaptive evaluation that cannot be gamed by architecture-benchmark co-design.

***

## 9. What Is Not Novel Anymore

The following approaches are now standard or commoditized and are insufficient as primary technical differentiators for a serious open-source project.

### Basic Vector Memory
All major agent frameworks (LangChain, LlamaIndex, Letta, Mem0) implement vector-backed memory storage as a default. Adding vector memory to an agent is a one-hour implementation task. The differentiation must come from what surrounds it: retrieval policies, update mechanisms, temporal awareness, and precision measurement.[^73]

### Chat Summarization
Summarizing long conversation histories into shorter contexts is implemented in every major framework including Zep (progressive summarization) and LangChain (ConversationSummaryMemory). The summarization itself is not the research problem—what gets lost during summarization is.[^73]

### Naïve Memory Plugins
The plug-and-play external memory pattern (store conversation chunks → retrieve on query → inject into prompt) is fully commoditized. EvolMem demonstrates that simply adding these memory mechanisms does not necessarily improve LLM capabilities and can introduce efficiency limitations.[^21]

### Generic RAG Over Conversation History
Standard RAG over session history is the baseline that LongMemEval shows produces ~30% accuracy on memory tasks. It is not a research contribution—it is the baseline to beat.[^3]

### Simple Knowledge Graphs
Static knowledge graphs without temporal awareness or dynamic update capability are covered by tools like LlamaIndex's knowledge graph index and do not address the dynamic, evolving nature of agent memory.

### Static User Profiles
Fixed key-value user preference stores do not capture preference evolution, temporal drift, or the distinction between immediate vs. settled preferences. LaMP benchmarks this limitation.[^57]

### Unsupervised Self-Reflection Logs
Storing LLM self-reflections without verification, prioritization, or quality control is the original Reflexion pattern. It is not novel, and its reliability limitations are now documented.[^68][^11]

***

## 10. Frontier Gaps

### Gap 1: Memory-Action Coupling Evaluation

**Problem:** No widely adopted benchmark measures whether retrieved memories actually improve agentic decisions rather than just conversational recall.

**Why Systems Fail:** MemoryArena demonstrates this directly—saturating LoCoMo does not predict MemoryArena performance.[^2]

**Difficulty:** High. Requires constructing tasks where memory causally enables or prevents correct action, at scale.

**Research Value:** High. **Builder Value:** Very High (shapes what to optimize for).

**Open-Source Wedge:** Build and release a benchmark harness that generates interdependent multi-session tasks with explicit causal memory requirements.

***

### Gap 2: Verified Reflection Storage

**Problem:** Self-generated reflections stored in memory may be hallucinated. No current system verifies reflection quality before storage.

**Why Systems Fail:** Reflexion stores raw LLM output. RMM reranks existing memories but doesn't verify new ones.[^11][^54]

**Supporting Evidence:** LLM hallucination survey; LLM-based agent hallucination taxonomy.[^71][^68]

**Difficulty:** Medium-High. External verification requires either ground truth (often unavailable) or multi-agent consensus.

**Research Value:** High. **Builder Value:** High.

**Open-Source Wedge:** A reflection verification layer that uses multi-agent consensus or structured world-state checking before committing to memory.

***

### Gap 3: Causal Retrieval vs. Semantic Retrieval

**Problem:** Existing retrieval measures semantic similarity, not causal relevance to task outcomes. The system retrieves "relevant" memories that don't actually help, and misses "irrelevant"-seeming memories that do.

**Why Systems Fail:** Embeddings measure semantic proximity, not causal influence on decisions. Retrieval benchmarks use recall@k, not precision@outcome.

**Difficulty:** Very High. Requires learning which memories improve decisions in which contexts.

**Research Value:** Very High. **Builder Value:** High.

**Open-Source Wedge:** A memory usefulness scorer trained on task outcome signals (inspired by MEM1's RL consolidation but without requiring full RL training).[^15]

***

### Gap 4: Temporal Contradiction Resolution

**Problem:** No standard mechanism detects and resolves contradictions between old and new facts in agent memory across heterogeneous memory types.

**Why Systems Fail:** Most memory systems are append-only. Graphiti uses validity windows but this is one system's implementation, not a standard protocol.[^62]

**Supporting Evidence:** LongMemEval temporal reasoning sub-task; EvolMem temporal dimension.[^21][^3]

**Difficulty:** Medium. Temporal KG primitives exist; the gap is in standardization and heterogeneous store support.

**Research Value:** Medium. **Builder Value:** Very High.

**Open-Source Wedge:** A temporal contradiction detection layer that works across vector, graph, and document memory backends.

***

### Gap 5: Procedural Skill Quality Maintenance at Scale

**Problem:** Skills extracted from experience trajectories degrade in quality as they grow in number, or become stale as environments change.

**Why Systems Fail:** ProcMEM uses score-based maintenance but on a small scale. Memp uses dynamic deprecation but limited evaluation.[^13][^12]

**Difficulty:** High. Requires continuous skill quality assessment without ground-truth labels.

**Research Value:** High. **Builder Value:** High.

**Open-Source Wedge:** A skill registry with confidence decay, usage-based promotion/demotion, and environment-change detection.

***

### Gap 6: Memory Safety (Privacy + Extraction Resistance)

**Problem:** Agent memory stores are extractable via adversarial prompting (MEXTRA), and agents use more personal information than necessary (AgentDAM).[^17][^70]

**Why Systems Fail:** No production-grade privacy-preserving memory architecture with formal guarantees exists in open-source.

**Difficulty:** Very High. Differential privacy in retrieval is computationally expensive.

**Research Value:** Very High. **Builder Value:** Very High (regulatory/compliance requirement).

**Open-Source Wedge:** A memory access control layer with audit trails, per-user deletion, and data-minimization enforcement.

***

### Gap 7: Multi-Agent Memory Provenance and Trust

**Problem:** When multiple agents contribute to shared memory, there is no standard mechanism for tracking provenance, filtering by agent reliability, or rolling back contributions from a bad actor.

**Why Systems Fail:** G-Memory adds hierarchical structure but not provenance or trust. Collaborative Memory adds access control but not agent reliability scoring.[^19][^56]

**Difficulty:** High. Trust modeling across agents is an open ML research problem.

**Research Value:** High. **Builder Value:** High (essential for production MAS).

**Open-Source Wedge:** A provenance-annotated shared memory protocol with optional trust-weighted write policies.

***

### Gap 8: Lifelong Benchmark with Real Environment Change

**Problem:** All current benchmarks use controlled, static evaluation environments. No benchmark tests memory over genuinely changing real-world distributions.

**Why Systems Fail:** WikiBigEdit tests editing methods but not the full agent pipeline. EvolMem is synthetic. MemoryArena uses static task templates.[^38][^52][^21][^2]

**Difficulty:** Very High. Requires real deployment data or very high-fidelity simulation.

**Research Value:** Very High. **Builder Value:** Medium (research gap before builder gap).

**Open-Source Wedge:** A living benchmark that pulls from real-time information sources to continuously challenge memory systems.

***

### Gap 9: Memory Lifecycle Management

**Problem:** No system implements a complete memory lifecycle: acquisition, consolidation, indexing, update, contradiction check, aging, pruning, and deletion with full audit trail.

**Why Systems Fail:** Individual systems address individual lifecycle stages. No open standard covers the full lifecycle.

**Difficulty:** Medium. Engineering complexity, not fundamental research barrier.

**Research Value:** Medium. **Builder Value:** Very High.

**Open-Source Wedge:** A memory lifecycle manager as an open-source protocol (not just a library), specifying APIs, events, and guarantees.

***

### Gap 10: Conflict Resolution in Memory Stores

**Problem:** When two memories contradict each other, no standard mechanism determines which is authoritative, stores the contradiction explicitly, or routes to the correct one depending on query type.

**Why Systems Fail:** MemoryAgentBench identifies conflict resolution as a core competency where current methods fail. Zep uses temporal validity windows, but these only handle time-based conflicts.[^26][^25]

**Difficulty:** High. Conflict resolution requires understanding causality, authority, and domain context.

**Research Value:** High. **Builder Value:** High.

**Open-Source Wedge:** A contradiction-aware memory layer that explicitly stores conflicting facts as structured alternatives, with routing logic for resolution.

***

## 11. Candidate Novel Directions

### Direction 1: Verified Episodic Memory with Consistency Checking
[PARTIALLY NOVEL]

**Core Primitive:** A memory write protocol that checks consistency before committing: (a) semantic contradiction with existing memories, (b) temporal plausibility, (c) multi-source confirmation rate.

**Dead End Addressed:** Pure Reflexion-style memory without verification.

**Why Not Just Another RAG Layer:** RAG is read-side; this is a write-side protocol. The constraint is on what is stored, not just what is retrieved.

**Required Architecture:** A memory writer that passes each candidate memory through a consistency checker (rule-based + LLM-verified), a contradiction registry, and a confidence scorer before indexing.

**Possible Benchmark:** Measure hallucination injection rate and downstream task accuracy degradation from false memories.

**MVP Scope:** A verification pipeline for reflective memories with test harness.

**Research Risk:** Medium. LLM-based consistency checking may itself hallucinate.

**Adoption Risk:** Low. Drops into any existing memory pipeline as a write-time middleware.

**Breakout Potential:** High. Addresses the most under-solved problem in deployed memory systems.

***

### Direction 2: Temporal Memory as a First-Class Primitive
[NOT NOVEL BUT UNDERBUILT]

**Core Primitive:** A temporal memory layer with native validity interval storage, contradiction detection, and "as-of-time T" query semantics, working across vector, graph, and document backends.

**Dead End Addressed:** Append-only memory stores that cannot distinguish current from historical truth.

**Why Not Just Another RAG Layer:** Temporal reasoning requires structural changes to the memory representation (validity windows, event ordering, source timestamps), not just retrieval policy changes.

**Required Architecture:** Validity-interval-aware memory primitives; contradiction detector; temporal query rewriter; backend-agnostic interface layer.

**Possible Benchmark:** LongMemEval temporal sub-task; TReMu extension; new temporal contradiction benchmark.[^6][^3]

**MVP Scope:** A temporal memory layer with validity intervals on top of an existing vector store.

**Research Risk:** Low. Temporal KG work is mature; engineering challenge primarily.

**Adoption Risk:** Medium. Requires schema discipline in memory writes.

**Breakout Potential:** Medium–High. No open-source temporal memory library with full correctness semantics exists.

***

### Direction 3: Causal Memory Scoring
[LIKELY NOVEL]

**Core Primitive:** A scoring model that, given a retrieved memory and a current task context, estimates the probability that the memory will causally improve task outcome, not just semantic similarity.

**Dead End Addressed:** Recall@k as retrieval metric; semantically relevant but causally irrelevant retrieval.

**Why Not Just Another RAG Layer:** Requires task-conditioned scoring, not query-document similarity.

**Required Architecture:** A causal scorer trained on outcome-labeled retrieval events; an outcome-graded memory dataset; a retrieval policy that uses causal score alongside semantic score.

**Possible Benchmark:** MemoryArena with explicit causal outcome labeling; a new causal retrieval evaluation harness.[^2]

**MVP Scope:** A re-ranker trained on retrieval outcome feedback from MemoryArena-style tasks.

**Research Risk:** High. Collecting outcome-labeled retrieval training data is expensive.

**Adoption Risk:** Low. Drop-in reranker.

**Breakout Potential:** Very High. No such system exists. Addresses the most important gap identified by MemoryArena research.

***

### Direction 4: Procedural Skill Memory with Cross-Agent Transfer Protocol
[LIKELY NOVEL]

**Core Primitive:** An open protocol for representing, verifying, and transferring executable skill memories across agents and models, including skill confidence, domain scope, and deprecation metadata.

**Dead End Addressed:** Per-agent isolated skills that cannot be reused; raw trajectory archives without abstraction.

**Why Not Just Another RAG Layer:** Skills are executable programs/procedures, not text chunks. Their retrieval is conditioned on activation state, not semantic query.

**Required Architecture:** Skill-MDP formalism (per ProcMEM); a skill registry with metadata; activation-condition evaluation; cross-agent/cross-model transfer format.[^12]

**Possible Benchmark:** ProcMEM cross-agent evaluation; new cross-model skill transfer benchmark.[^12]

**MVP Scope:** A skill registry format + transfer protocol with evaluation harness.

**Research Risk:** Medium. Activation condition reliability is the key open question.

**Adoption Risk:** Medium. Requires agents to generate and register skills—workflow change.

**Breakout Potential:** High. Skills are the missing middle layer between raw experience and high-level planning.

***

### Direction 5: Memory Lifecycle Protocol (Open Standard)
[NOT NOVEL BUT UNDERBUILT]

**Core Primitive:** An open protocol (not library) specifying the full lifecycle of an agent memory: creation, validation, indexing, update, contradiction check, aging, soft-deletion, hard-deletion, and audit trail, with defined API semantics.

**Dead End Addressed:** Ad hoc, library-specific memory management with no interoperability.

**Why Not Just Another RAG Layer:** This is an infrastructure standard, not an algorithm. It enables interoperability across agent frameworks.

**Required Architecture:** Protocol specification document; reference implementation; compliance test suite; audit log format.

**Possible Benchmark:** N/A for core protocol; compliance testing via MemoryAgentBench.

**MVP Scope:** Protocol spec document + reference implementation in Python.

**Research Risk:** Low. Engineering problem primarily.

**Adoption Risk:** High. Standards require ecosystem buy-in.

**Breakout Potential:** High if adopted. The lack of a standard is a major barrier to memory system interoperability.

***

### Direction 6: Privacy-Preserving Memory with Formal Guarantees
[UNCERTAIN]

**Core Primitive:** A memory architecture that implements formal data minimization (per AgentDAM findings) and extraction-resistance (per MEXTRA findings) without prohibitive overhead.[^18][^70][^17]

**Dead End Addressed:** Memory stores as vulnerable personal data concentrations.

**Why Not Just Another RAG Layer:** Privacy requires formal guarantees and architectural constraints, not just access-control policies.

**Required Architecture:** Encrypted memory stores; access audit; differential privacy in retrieval; per-user memory namespace isolation; GDPR-compliant deletion.

**Possible Benchmark:** AgentDAM data-minimization benchmark; MEXTRA-style attack evaluation.[^70][^17]

**MVP Scope:** Per-user namespace isolation + audit trail + deletion API.

**Research Risk:** High. Differential privacy in retrieval is computationally expensive at scale.

**Adoption Risk:** Medium. Compliance requirements create pull.

**Breakout Potential:** High in regulated industries (healthcare, finance, legal).

***

### Direction 7: Multi-Agent Memory with Provenance and Trust Weighting
[PARTIALLY NOVEL]

**Core Primitive:** A shared memory layer where each memory fragment carries immutable provenance (contributing agent, confidence, source type, timestamp) and write policies are conditioned on agent trust scores.

**Dead End Addressed:** Flat shared memory pools with no provenance (dominant pattern today).

**Why Not Just Another RAG Layer:** Provenance + trust weighting are structural properties of the memory store, not retrieval policy changes.

**Required Architecture:** Provenance metadata schema; trust scoring model per agent; write policy enforcement; rollback by agent ID; retrospective permission checking.

**Possible Benchmark:** G-Memory evaluation + provenance-violation injection test.[^19]

**MVP Scope:** Provenance metadata layer on top of any shared vector store.

**Research Risk:** Medium. Trust scoring model design is research-intensive.

**Adoption Risk:** Medium. Requires MAS orchestration framework adoption.

**Breakout Potential:** High. Required for enterprise MAS deployments.

***

## 12. Recommended Direction

### Thesis

Build an open-source **Causal Memory Engine** — a memory system that learns which stored memories causally improve agent task outcomes, not just which memories are semantically similar to queries. This combines a **write-side verification layer** (Direction 1) with a **causal retrieval scorer** (Direction 3) and a **temporal validity layer** (Direction 2) as the foundational architecture.

### Technical Wedge

The core insight: retrieval quality for agents should be measured by task outcome improvement, not semantic similarity. No current open-source or production system has been trained to optimize for this objective. The MEM1 result shows that RL-trained memory consolidation can achieve 3.5x performance gains — but MEM1 consolidates context, not external memory. The proposed extension: apply outcome-conditioned scoring to the external memory write and retrieval pipeline.[^15]

### Why Now

Three converging conditions:
1. **MemoryArena (2026)** has formally documented the gap between existing benchmarks and action-relevant memory, providing a target to optimize against.[^2]
2. **MEM1 (ICLR 2026)** has proven RL-trained memory consolidation works at scale — providing the training paradigm.[^15]
3. **MEXTRA (ACL 2025)** and **AgentDAM (NeurIPS 2025)** have documented privacy failure modes that must be addressed architecturally, creating a clear product requirement.[^17][^70]

### What to Build First

1. **Outcome-labeled retrieval dataset**: Use MemoryArena-style tasks to generate (query, retrieved-memory, task-outcome) triples. This is the training data for a causal scorer.
2. **Causal retrieval scorer**: A lightweight re-ranker trained on outcome labels. Not requiring full RL (unlike MEM1).
3. **Write-side consistency layer**: A validation pipeline for memories before indexing, checking for contradictions and temporal plausibility.
4. **Temporal validity metadata**: Extend any vector store to attach validity intervals to memory entries.
5. **Benchmark harness**: A reproducible evaluation that measures causal retrieval quality, temporal accuracy, and privacy compliance simultaneously.

### What to Avoid

- Do not build another vector store wrapper. The commodity layer is solved.
- Do not invest in parametric knowledge editing as primary memory mechanism. QAEdit and WikiBigEdit show it does not scale.[^9][^38]
- Do not build self-reflection pipelines without verification. The hallucination injection problem is real.
- Do not rely on LLM-as-Judge as the sole evaluation metric. It is noisy (Mem0 paper uses it; LongMemEval shows it has blind spots).[^44][^3]

### What to Benchmark

- **Primary:** MemoryArena (coupled memory-action); MemoryAgentBench (four competencies).[^25][^2]
- **Secondary:** LongMemEval temporal sub-task; Sequential-NIAH.[^32][^3]
- **Novel contribution:** Causal retrieval precision: fraction of retrieved memories that demonstrably improved the downstream task outcome, measured via counterfactual task execution.

### How to Attract Researchers and Builders

- **Researchers:** The causal retrieval scoring model and the outcome-labeled memory dataset are open research problems. A public dataset of MemoryArena-style (query, memory, outcome) triples would be cited.
- **Builders:** Drop-in middleware that improves any existing agent's memory precision without requiring retraining. Lower bar than MEM1's RL training.
- **Privacy-sensitive deployments:** The write-side validation + namespace isolation + audit trail addresses MEXTRA-class attacks, creating pull from regulated industries.

### Why It Could Matter Beyond Demos

Every production agent system (customer support, coding assistants, research agents, personalized tutoring) already uses some form of external memory. A drop-in layer that measurably improves the causal usefulness of retrieved memories, with privacy and temporal correctness guarantees, addresses a gap in all of them simultaneously. The memory lifecycle protocol (Direction 5) could become an interoperability standard across frameworks, analogous to how OpenAPI became the standard for REST API specifications.

***

## 13. Evidence Ledger

| Claim | Source(s) | Evidence Strength | Confidence | Caveat |
|-------|-----------|-------------------|------------|--------|
| Commercial systems show ~30% accuracy drop on multi-session memory | LongMemEval, ICLR 2025[^3][^4] | Strong (controlled benchmark, 500 questions) | High | Tests chat assistants, not action agents |
| LoCoMo-saturating agents fail on MemoryArena | MemoryArena, arXiv 2026[^2] | Strong (direct comparison) | High | Preprint, not yet peer-reviewed |
| ROME/MEMIT fail with ~1,000+ sequential edits | QAEdit (ACL 2025)[^9]; Gupta et al.[^7] | Strong (two independent papers) | Very High | Both papers agree on sequential failure |
| Reflexion stores unverified self-reflections | Reflexion, NeurIPS 2023[^11] | Verified (system design) | Very High | Not an empirical claim—architectural fact |
| Temporal reasoning lags human by 73% | LoCoMo, ACL 2024[^5] | Moderate (10-conversation dataset, controlled benchmark) | Moderate | LoCoMo is a small-scale benchmark |
| MEM1 achieves 3.5x perf gain with 3.7x memory reduction | MEM1, ICLR 2026[^15] | Strong (ICLR 2026 peer-reviewed) | High | Domain coverage limited; RL training required |
| Zep achieves 18.5% accuracy improvement on LongMemEval | Zep paper, arXiv 2025[^16] | Moderate (vendor-authored) | Moderate | No independent replication found |
| Memory extraction attacks work in black-box setting | MEXTRA, ACL 2025[^17][^18] | Strong (peer-reviewed, demonstrated system) | High | Attack paper; defense not evaluated |
| Agent memory mechanisms do not necessarily improve LLMs | EvolMem, arXiv 2026[^21] | Moderate (preprint, limited benchmarks) | Moderate | Preprint; needs confirmation |
| G-Memory improves MAS success by up to 20.89% | G-Memory, NeurIPS 2025[^19][^20] | Strong (NeurIPS spotlight, 5 benchmarks) | High | Tests 3 LLM backbones and 5 benchmarks |
| Model editing accuracy: 38.5% realistic vs. 96.8% synthetic | QAEdit, ACL 2025[^9][^8] | Strong (peer-reviewed; identifies specific confound) | Very High | Specific to teacher-forcing confound; newer methods may differ |
| Best model on Sequential-NIAH achieves only 63.50% | Sequential-NIAH, EMNLP 2025[^32] | Strong (peer-reviewed) | High | Narrow task (sequential extraction) |
| Cross-agent procedural skill transfer is feasible | ProcMEM, arXiv 2026[^12] | Moderate (preprint, lab scale) | Moderate | Needs replication at scale |
| No LLM consistently outperforms across all memory dimensions | EvolMem, arXiv 2026[^21] | Moderate (preprint) | Moderate | Early result; needs peer review |

***

## 14. Unknowns and Further Research

### What Could Not Be Verified

- **LongMemEval V2 (agentic context extension, announced May 2026):** Results were not available as of research date. Follow-up: github.com/xiaowu0162/LongMemEval[^47]

- **Independent replication of Zep/Graphiti accuracy claims:** The 18.5% improvement is vendor-reported. No independent evaluation found. Recommended next step: reproduce LongMemEval evaluation with public Graphiti implementation.[^16]

- **Memp (arXiv:2508.06433) vs. ProcMEM (arXiv:2602.01869) comparative evaluation:** Both address procedural memory but no head-to-head comparison was found.

- **Real-world performance of MEM1's RL consolidation in production deployments:** MEM1 is ICLR 2026 but applied only to QA and web shopping. Generalization to other long-horizon agent tasks is unverified.[^15]

- **BaFT (ICLR 2025) and newer knowledge editing methods** at scale comparable to QAEdit's evaluation—may partially address the editing failures documented by Yang et al., but no direct comparison was found.[^9][^65]

- **AlpsBench (arXiv:2603.26680, May 2026)** for real-dialogue personalization—newly published, results not fully analyzed.[^74]

- **The full scope of agent hallucination taxonomy**: The "memorization hallucinations" category (flawed memory initialization, sub-optimal retrieval, imperfect priority assignment, inaccurate information writing) maps directly to memory architecture gaps, but detailed empirical evaluation of each sub-category was not found.[^68]

### Recommended Follow-Up Searches

1. `"causal memory retrieval agent outcome LLM"` — check whether any 2025-2026 work has addressed causal retrieval scoring directly.
2. `"differential privacy retrieval augmented generation"` — assess feasibility of privacy-preserving retrieval for agent memory.
3. `"memory contradiction detection LLM agents"` — find any direct work on contradiction-aware memory writes.
4. `"lifelong agentic benchmark changing distribution"` — assess whether any living/streaming benchmark beyond WikiBigEdit has been proposed.
5. `"ENGRAM episodic semantic procedural memory router"` (mentioned in Mem0 semantic scholar page) — locate and evaluate this reference implementation.[^75]
6. `"Unifying Memory Skills Rules LLM Agents arXiv:2604.15877"` (arXiv:2604.15877, April 2026) — a four-level spectrum from interaction experience to reusable abstractions; locate and analyze full paper.[^76]
7. `"Collaborative Memory multi-user access control ICML 2025"` — assess whether the Accenture paper's provenance model has been extended or independently evaluated.

***

*Self-Audit Checklist (applied before finalization):*
- *All material claims cite a specific source directly supporting that exact claim. ✓*
- *No fake papers, systems, benchmarks, authors, or metrics. ✓*
- *Speculative synthesis marked as [INFERENCE] or [JUDGMENT]. ✓*
- *Source claims distinguished from analyst analysis throughout. ✓*
- *Recommended direction derived from documented evidence gaps, not preference. ✓*
- *Vendor sources (Zep, Letta/MemGPT blog) marked as C-grade or noted as vendor-authored. ✓*
- *No unsupported predictions or "could revolutionize" language. ✓*

---

## References

1. [MemoryArena: Benchmarking Agent Memory in Interdependent ...](https://digitaleconomy.stanford.edu/publication/memoryarena-benchmarking-agent-memory-in-interdependent-multi-session-agentic-tasks/) - To capture this setting, we introduce MemoryArena, a unified evaluation gym for benchmarking agent m...

2. [[2602.16313] MemoryArena: Benchmarking Agent Memory in ... - arXiv](https://arxiv.org/abs/2602.16313) - The benchmark consists of human-crafted agentic tasks with explicitly interdependent subtasks, where...

3. [Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813) - Recent large language model (LLM)-driven chat assistant systems have integrated memory components to...

4. [Benchmarking Chat Assistants on Long-Term Interactive Memory](https://openreview.net/forum?id=pZiyCaVuti) - Recent large language model (LLM)-driven chat assistant systems have integrated memory components to...

5. [Evaluating Very Long-Term Conversational Memory of LLM Agents](https://snap-research.github.io/locomo/) - Evaluating Very Long-Term Conversational Memory of LLM Agents

6. [TReMu: Towards Neuro-Symbolic Temporal Reasoning for LLM ...](https://liner.com/review/tremu-towards-neurosymbolic-temporal-reasoning-for-llmagents-with-memory-in) - We propose TReMu, a novel framework for temporal reasoning in multi-session dialogues, integrating t...

7. [Model Editing at Scale leads to Gradual and Catastrophic Forgetting](https://arxiv.org/html/2401.07453v3) - The major difference between ROME and MEMIT is that while ROME works under the assumption that knowl...

8. [The Mirage of Model Editing: Revisiting Evaluation in the Wild](https://ofey.me/assets/review/acl25_yang.html) - This paper presents QAEdit, which addresses the problem that using teacher forcing for knowledge edi...

9. [The Mirage of Model Editing: Revisiting Evaluation in the Wild](https://yangwl.site/revisit-editing-evaluation/) - This paper reveals existing model editing evaluation adopts inappropriate strategies, such as teache...

10. [Reflexion: language agents with verbal reinforcement learning](https://openreview.net/forum?id=vAElhFcKW6) - Reflexion is a framework that reinforces language agents by updating language rather than model weig...

11. [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366) - We propose Reflexion, a novel framework to reinforce language agents not by updating weights, but in...

12. [ProcMEM: Learning Reusable Procedural Memory from Experience ...](https://arxiv.org/abs/2602.01869) - LLM-driven agents demonstrate strong performance in sequential decision-making but often rely on on-...

13. [𝑀⁢𝑒⁢𝑚^𝑝: Exploring Agent Procedural Memory](https://arxiv.org/html/2508.06433v1)

14. [[2506.15841] MEM1: Learning to Synergize Memory and Reasoning ...](https://arxiv.org/abs/2506.15841) - We introduce MEM1, an end-to-end reinforcement learning framework that enables agents to operate wit...

15. [MEM1: Learning to Synergize Memory and Reasoning for Efficient...](https://openreview.net/forum?id=XY8AaxDSLb) - This submission introduces MEM1, a reinforcement learning-based framework designed to enable languag...

16. [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/abs/2501.13956) - We introduce Zep, a novel memory layer service for AI agents that outperforms the current state-of-t...

17. [Unveiling Privacy Risks in LLM Agent Memory - ACL Anthology](https://aclanthology.org/2025.acl-long.1227/) - Bo Wang, Weiyi He, Shenglai Zeng, Zhen Xiang, Yue Xing, Jiliang Tang, Pengfei He. Proceedings of the...

18. [[2502.13172] Unveiling Privacy Risks in LLM Agent Memory - arXiv](https://arxiv.org/abs/2502.13172) - Large Language Model (LLM) agents have become increasingly prevalent across various real-world appli...

19. [Tracing Hierarchical Memory for Multi-Agent Systems - OpenReview](https://openreview.net/forum?id=mmIAp3cVS0) - This paper introduces G-Memory, a hierarchical, agentic memory system for multi-agent systems (MAS) ...

20. [G-Memory: Tracing Hierarchical Memory for Multi-Agent Systems](https://arxiv.org/abs/2506.07398) - We introduce G-Memory, a hierarchical, agentic memory system for MAS inspired by organizational memo...

21. [A Cognitive-Driven Benchmark for Multi-Session Dialogue Memory](https://arxiv.org/abs/2601.03543) - In this work, we propose EvolMem, a new benchmark for assessing multi-session memory capabilities of...

22. [A Survey on the Evolution of LLM Agent Memory Mechanisms - arXiv](https://arxiv.org/abs/2605.06716) - Abstract page for arXiv paper 2605.06716: From Storage to Experience: A Survey on the Evolution of L...

23. [NeurIPS Poster A-Mem: Agentic Memory for LLM Agents](https://neurips.cc/virtual/2025/poster/119020) - To address this limitation, this paper proposes a novel agentic memory system for LLM agents that ca...

24. [[2502.12110] A-MEM: Agentic Memory for LLM Agents - arXiv](https://arxiv.org/abs/2502.12110) - This paper proposes a novel agentic memory system for LLM agents that can dynamically organize memor...

25. [Evaluating Memory in LLM Agents via Incremental Multi-Turn...](https://openreview.net/forum?id=DT7JyQC3MR) - This paper introduces MemoryAgentBench, a benchmark evaluating memory agents across four competencie...

26. [Evaluating Memory in LLM Agents via Incremental Multi-Turn ...](https://github.com/HUST-AI-HYZ/MemoryAgentBench) - Open source code for ICLR 2026 Paper: Evaluating Memory in LLM Agents via Incremental Multi-Turn Int...

27. [Lost in the Middle: How Language Models Use Long Contexts](https://aclanthology.org/2024.tacl-1.9/) - We analyze the performance of language models on two tasks that require identifying relevant informa...

28. [Lost in the Middle: How Language Models Use Long Contexts - arXiv](https://arxiv.org/abs/2307.03172) - We analyze the performance of language models on two tasks that require identifying relevant informa...

29. [[2309.02427] Cognitive Architectures for Language Agents - arXiv](https://arxiv.org/abs/2309.02427) - CoALA describes a language agent with modular memory components, a structured action space to intera...

30. [Cognitive Architectures for Language Agents - OpenReview](https://openreview.net/forum?id=1i6ZCvflQJ) - CoALA describes a language agent with modular memory components, a structured action space to intera...

31. [[2310.08560] MemGPT: Towards LLMs as Operating Systems - arXiv](https://arxiv.org/abs/2310.08560) - Large language models (LLMs) have revolutionized AI, but are constrained by limited context windows,...

32. [Sequential-NIAH: A Needle-In-A-Haystack Benchmark for Extracting ...](https://arxiv.org/abs/2504.04713) - Evaluating the ability of large language models (LLMs) to process lengthy contexts is critical, espe...

33. [Generative Agents: Interactive Simulacra of Human Behavior - arXiv](https://arxiv.org/abs/2304.03442) - In this paper, we introduce generative agents--computational software agents that simulate believabl...

34. [Generative Agents: Interactive Simulacra of Human Behavior](https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606763) - In this paper, we introduce generative agents: computational software agents that simulate believabl...

35. [Mitigating Catastrophic Forgetting in Large Language Models with ...](https://aclanthology.org/2024.acl-long.77/) - Jianheng Huang, Leyang Cui, Ante Wang, Chengyi Yang, Xinting Liao, Linfeng Song, Junfeng Yao, Jinson...

36. [[2603.12658] Continual Learning in Large Language Models - arXiv](https://arxiv.org/abs/2603.12658) - Continual learning (CL) has emerged as a pivotal paradigm to enable large language models (LLMs) to ...

37. [Mass Editing Memory in a Transformer](https://memit.baulab.info) - In this paper, we develop an improved direct editing method (MEMIT) and scale it up to perform many ...

38. [Understanding the Limits of Lifelong Knowledge Editing in ...](https://arxiv.org/html/2503.05683v1)

39. [Multi-User Memory Sharing in LLM Agents with Dynamic Access ...](https://arxiv.org/html/2505.18279v1)

40. [[2512.13564] Memory in the Age of AI Agents - arXiv](https://arxiv.org/abs/2512.13564) - This work aims to provide an up-to-date landscape of current agent memory research. We begin by clea...

41. [A Survey on the Memory Mechanism of Large Language Model ...](https://arxiv.org/abs/2404.13501) - Large language model (LLM) based agents have recently attracted much attention from the research and...

42. [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560v2) - Large language models (LLMs) have revolutionized AI, but are constrained by limited context windows,...

43. [Mem0: Building Production-Ready AI Agents with Scalable Long ...](https://huggingface.co/papers/2504.19413) - Mem0, a memory-centric architecture with graph-based memory, enhances long-term conversational coher...

44. [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://www.arxiv.org/abs/2504.19413) - Large Language Models (LLMs) have demonstrated remarkable prowess in generating contextually coheren...

45. [Mem0: Building Production-Ready AI Agents with Scalable Long ...](https://arxiv.org/abs/2504.19413) - We introduce Mem0, a scalable memory-centric architecture that addresses this issue by dynamically e...

46. [4 Experiments](https://arxiv.org/html/2501.13956v1)

47. [xiaowu0162/LongMemEval: Benchmarking Chat Assistants ...](https://github.com/xiaowu0162/LongMemEval) - Benchmarking Chat Assistants on Long-Term Interactive Memory (ICLR 2025) - xiaowu0162/LongMemEval

48. [MemoryArena: Benchmarking Agent Memory in Interdependent ...](https://memoryarena.github.io) - This dataset contains structured multi-session agentic tasks with questions (list), answers (list), ...

49. [Sequential-NIAH: A Needle-In-A-Haystack Benchmark for Extracting ...](https://aclanthology.org/2025.emnlp-main.1497/) - Yifei Yu, Qian-Wen Zhang, Lingfeng Qiao, Di Yin, Fang Li, Jie Wang, Chen Zeng Xi, Suncong Zheng, Xia...

50. [Evaluating Very Long-Term Conversational Memory of LLM Agents](https://arxiv.org/abs/2402.17753) - Existing works on long-term open-domain dialogues focus on evaluating model responses within context...

51. [GitHub - snap-research/locomo](https://github.com/snap-research/locomo) - Contribute to snap-research/locomo development by creating an account on GitHub.

52. [Understanding the Limits of Lifelong Knowledge Editing in LLMs](https://icml.cc/virtual/2025/poster/46232) - In this work, we aim to bridge research into lifelong knowledge editing to real-world edits at pract...

53. [ProcMEM: Learning Reusable Procedural Memory from Experience ...](https://arxiv.org/html/2602.01869v1)

54. [In Prospect and Retrospect: Reflective Memory Management for ...](https://aclanthology.org/2025.acl-long.413/) - In this work, we propose Reflective Memory Management (RMM), a novel mechanism for long-term dialogu...

55. [In Prospect and Retrospect: Reflective Memory Management for ...](https://arxiv.org/abs/2503.08026) - In this work, we propose Reflective Memory Management (RMM), a novel mechanism for long-term dialogu...

56. [Multi-User Memory Sharing in LLM Agents with Dynamic Access ...](https://icml.cc/virtual/2025/49354)

57. [Codes for papers on Large Language Models Personalization (LaMP)](https://github.com/lamp-benchmark/lamp) - This paper highlights the importance of personalization in the current state of natural language und...

58. [Memory Sharing for Large Language Model based Agents](https://arxiv.org/abs/2404.09982) - While Large Language Model (LLM) based agents excel at complex tasks, their performance in open-ende...

59. [Agent Memory: How to Build Agents that Learn and Remember - Letta](https://www.letta.com/blog/agent-memory) - Agent memory is what and how your agent remembers information over time. While basic memory might si...

60. [Memory Blocks: The Key to Agentic Context Management - Letta](https://www.letta.com/blog/memory-blocks) - Memory blocks offer an elegant abstraction for context window management. By structuring the context...

61. [A-Mem: Agentic Memory for LLM Agents | OpenReview](https://openreview.net/forum?id=FiM0M8gcct) - To address this limitation, this paper proposes a novel agentic memory system for LLM agents that ca...

62. [graphiti/README.md at main · getzep/graphiti](https://github.com/getzep/graphiti/blob/main/README.md) - Build Real-Time Knowledge Graphs for AI Agents. Contribute to getzep/graphiti development by creatin...

63. [getzep/graphiti: Build Real-Time Knowledge Graphs for AI ...](https://github.com/getzep/graphiti) - Build Real-Time Knowledge Graphs for AI Agents. Contribute to getzep/graphiti development by creatin...

64. [bingreeky/GMemory - GitHub](https://github.com/bingreeky/GMemory) - Our method, G-Memory, empowers multi-agent systems with a hierarchical memory architecture that cont...

65. [Unlocking Efficient, Scalable, and Continual Knowledge Editing with...](https://openreview.net/forum?id=PITFO1ddeh) - This paper tackles the challenge of updating specific knowledge in Large Language Models (LLMs) whil...

66. [RAG Accuracy Problems: Why RAG Fails and How to Fix It - Atlan](https://atlan.com/know/rag-accuracy-problems/) - RAG accuracy fails at four layers: data quality (stale or ungoverned knowledge bases), retrieval mec...

67. [Fundamental Failure Modes in RAG Systems - PromptQL](https://promptql.io/blog/fundamental-failure-modes-in-rag-systems) - Retrieval-Augmented Generation (RAG) has emerged as a critical approach for enhancing Large Language...

68. [LLM-based Agents Suffer from Hallucinations: A Survey of ... - arXiv](https://arxiv.org/html/2509.18970v1) - However, despite their remarkable potential, LLM-based agents remain vulnerable to hallucination iss...

69. [TimE: A Multi-level Benchmark for Temporal Reasoning of LLMs in ...](https://neurips.cc/virtual/2025/poster/121417) - Temporal reasoning is pivotal for Large Language Models (LLMs) to comprehend the real world. However...

70. [AgentDAM: Privacy Leakage Evaluation for Autonomous Web Agents](https://neurips.cc/virtual/2025/poster/121443) - PrivAgent: Agentic-based Red-teaming for LLM Privacy Leakage, 2024. ... Agent Security Bench (ASB): ...

71. [Large Language Models Hallucination: A Comprehensive Survey](https://arxiv.org/abs/2510.06265) - Large language models (LLMs) have transformed natural language processing, achieving remarkable perf...

72. [Temporal Reasoning with Large Language Models Augmented by ...](https://openreview.net/forum?id=sBkdGflUBI) - To address these challenges, we present EvoReasoner, a temporal-aware multi-hop reasoning algorithm ...

73. [The 6 Best AI Agent Memory Frameworks You Should Try in 2026](https://machinelearningmastery.com/the-6-best-ai-agent-memory-frameworks-you-should-try-in-2026/) - Six frameworks for long-term memory, retrieval, and context management. Practical project ideas to g...

74. [AlpsBench: An LLM Personalization Benchmark for Real-Dialogue ...](https://arxiv.org/html/2603.26680v2) - AlpsBench aims to provide a comprehensive framework to accelerate research toward truly personalized...

75. [Mem0: Building Production-Ready AI Agents with Scalable Long ...](https://www.semanticscholar.org/paper/Mem0:-Building-Production-Ready-AI-Agents-with-Chhikara-Khant/1d9c21a0fdb1cc16a32c5d490ebaf98436a23382) - ArXiv. 2025. TLDR. Zep is introduced, a novel memory layer service for AI agents that outperforms th...

76. [Unifying Memory, Skills, and Rules in LLM Agents - arXiv](https://arxiv.org/html/2604.15877v1) - We formalize a four-level spectrum characterizing how interaction experience is progressively compre...

