# Report 2: Benchmark and Evaluation Landscape for LLM and Agent Memory

> **Research date:** May 27, 2026 | **Protocol:** Hard anti-hallucination. Every material claim is grounded, tagged by epistemic status, and source-quality graded. No benchmark is cited without verified primary source inspection.

***

## 1. Executive Summary

The following 14 findings represent the strongest, source-grounded conclusions of this review.

1. **Most "memory" benchmarks are long-context retrieval benchmarks in disguise.** Needle-in-a-haystack (NIAH), RULER, InfiniteBench, LongBench, L-Eval, and BAMBOO all measure single-session in-context retrieval or document QA. They require no memory persistence, no update, no forgetting, and no multi-session state. [VERIFIED FACT][^1][^2]

2. **NIAH specifically does not reliably predict downstream task performance.** HELMET's study of 59 LCLMs found that synthetic tasks like NIAH "do not reliably predict downstream performance" and that open-source models "significantly lag behind closed ones when tasks require full-context reasoning" despite achieving near-perfect NIAH scores.[^3][^1]

3. **Context stuffing is now a trivially valid shortcut on most pre-2025 memory benchmarks.** LoCoMo and LongMemEval were designed for ~32K-token windows. With frontier models now supporting 128K–2M tokens, "a naive dump everything into context approach scores competitively" on those benchmarks. BEAM was specifically designed to close this gap by scaling to 10M-token dialogues.[^4][^5][^6]

4. **The only benchmarks that are genuinely hard to solve by context stuffing are those exceeding available context windows.** BEAM at 10M tokens, MemoryArena's interdependent multi-session agentic loops, and LifelongAgentBench's cross-session skill transfer tasks cannot be solved by dumping all history into context.[^7][^5][^8][^9][^10][^4]

5. **LongMemEval (2024) is the best-validated multi-ability memory benchmark at modest scale.** It tests five abilities—information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention—and showed a 30%–60% performance drop for long-context LLMs.[^11][^12][^13]

6. **Personalization benchmarks reveal severe deficits.** PERSONAMEM (COLM 2025) found that frontier models including GPT-4.1, o4-mini, and Gemini-2.0 achieve only ~50% accuracy when user profiles evolve over time. PrefEval found that preference following accuracy drops below 10% at merely 10 turns (~3K tokens) in zero-shot settings.[^14][^15][^16][^17]

7. **Knowledge-editing benchmarks (CounterFact, zsRE, MQuAKE) test parametric memory modification, not external agent memory.** They measure whether model weights can be patched, not whether an agent's retrieval store is updated correctly. MQuAKE specifically showed that even editors that recall edited facts accurately "fail catastrophically on multi-hop questions."[^18][^19]

8. **No single existing benchmark covers all four core memory competencies.** MemoryAgentBench (ICLR 2026) defines these as: accurate retrieval, test-time learning, long-range understanding, and conflict resolution. The paper explicitly states "no existing benchmarks cover all four competencies."[^20][^21]

9. **Agentic memory benchmarks that couple memorization with action represent the frontier.** MemoryArena (2026) showed that "agents with near-saturated performance on existing long-context memory benchmarks like LoCoMo perform poorly in our agentic setting." This directly exposes the gap between recall benchmarks and genuine agentic memory.[^8][^7]

10. **Temporal memory evaluation is systematically underdeveloped.** Existing benchmarks measure event ordering and static temporal fact retrieval, but no verified benchmark tests preference drift over time, stale-fact detection in agent memory stores, or temporal contradiction resolution across sessions in a rigorous, real-user-grounded way. [JUDGMENT]

11. **Privacy-sensitive memory evaluation is an emerging niche with only one verified dedicated benchmark.** CIMemories (Meta FAIR, Nov 2025) found that frontier models exhibit up to 69% attribute-level contextual integrity violations when recalling user memory across task contexts.[^22][^23]

12. **Long-horizon agent benchmarks (WebArena, OSWorld, SWE-bench, τ-bench, GAIA) do not directly test memory.** They test task completion, planning, and tool use. Memory may be incidentally required on a small subset of tasks, but it is not the primary evaluated capability. [JUDGMENT][^24][^25][^26][^27]

13. **Existing benchmarks are underscaled, often saturated, and frequently misaligned with semantic utility.** A 2026 survey on agentic memory systems found "existing benchmarks are underscaled and often saturated" and that "evaluation metrics are misaligned with semantic utility."[^28]

14. **A credible breakthrough benchmark must test memory at volumes where context stuffing is physically impossible, require memory to guide action (not just recall facts), and include temporal update, contradiction, forgetting, and privacy dimensions.** No single existing benchmark meets all these criteria simultaneously. [JUDGMENT]

***

## 2. Definition: What Counts as a Memory Benchmark?

The term "memory benchmark" is used loosely in the literature, covering at least eight distinct capabilities. This section establishes precise inclusion and exclusion criteria used throughout this report.

### Inclusion Criteria

A benchmark is included in this review if it tests one or more of the following:
- Retrieval or recall of information not present in the current prompt window
- Persistence of state across sessions, turns, or time
- Update, correction, or revision of stored knowledge
- Temporal ordering, validity, or staleness
- Selective forgetting or privacy-sensitive recall
- Personalization, user profile tracking, or preference inference
- Procedural or episodic memory reuse to guide future action

### Benchmark Type Taxonomy

| Type | Definition | Example | Memory Required? |
|------|-----------|---------|-----------------|
| **Long-context retrieval** | Retrieves facts from a long in-context document in the same session | NIAH, RULER | No — all facts present in context |
| **RAG benchmark** | Tests retrieval pipeline quality (precision, recall, faithfulness) | CRUD-RAG | No — tests retrieval mechanics, not persistence |
| **Agent memory benchmark** | Tests memory that persists across sessions and guides future action | MemoryArena, MemoryAgentBench | Yes |
| **Personalization benchmark** | Tests inference and tracking of user preferences over interactions | PERSONAMEM, PrefEval | Yes |
| **Temporal memory benchmark** | Tests time-aware recall, staleness detection, ordering | LongMemEval (temporal dim), ToT | Partial |
| **Memory editing benchmark** | Tests parametric weight modification and its ripple effects | CounterFact, MQuAKE | No — tests model weights, not agent stores |
| **Continual/lifelong learning** | Tests catastrophic forgetting avoidance, cross-task transfer | TRACE, LifelongAgentBench | Partial |
| **Long-horizon task benchmark** | Tests multi-step task completion, may incidentally require memory | WebArena, OSWorld, SWE-bench | Indirect/incidental |

### Exclusion

Benchmarks that **only** test single-session in-context retrieval are **excluded from the "agent memory" category** in this report, regardless of how they are marketed. This includes: NIAH, RULER, InfiniteBench, L-Eval, BAMBOO, and most LongBench sub-tasks in their standard form.

***

## 3. Benchmark Register

The following table summarizes every verified benchmark referenced in this report. Source-quality grades: **A** = peer-reviewed or official repo/leaderboard; **B** = arXiv preprint with code/data; **C** = official announcement without full methodology; **D** = secondary/commentary.

| Benchmark | Year | Authors/Org | Grade | Link | Type | Task Format | Dataset Type | Memory Type Tested | Metric | Code/Data? | Key Limitation |
|-----------|------|-------------|-------|------|------|-------------|-------------|-------------------|--------|------------|---------------|
| **NIAH** (Needle-in-a-Haystack) | 2023 | Greg Kamradt | B | [GitHub](https://github.com/gkamradt/LLMTest_NeedleInAHaystack) | Long-context retrieval | Single fact retrieval at varying positions/lengths | Synthetic (Paul Graham essays + injected needle) | Surface-level in-context retrieval | % recall | Yes | Tests only single-fact retrieval; no reasoning; gameable by literal match[^29][^30] |
| **RULER** | 2024 | Hsieh et al., NVIDIA | A | [arXiv:2404.06654](https://arxiv.org/abs/2404.06654) | Long-context retrieval | 13 tasks: multi-needle NIAH, variable tracking, aggregation | Synthetic | Single-session retrieval + multi-hop tracing | Accuracy | Yes (NVIDIA GitHub) | Still synthetic; doesn't test cross-session state; performance drop at 32K[^2][^31] |
| **LongBench** | 2023 | Bai et al., THUDM | A | [GitHub](https://github.com/THUDM/LongBench) | Long-context multi-task | 21 tasks: QA, summarization, code, few-shot | Mixed real/synthetic, bilingual | In-context long-document understanding | F1, ROUGE, accuracy | Yes | No multi-session; no persistent state; avg 6K–13K tokens[^32][^33] |
| **InfiniteBench** | 2024 | Zhang et al., OpenBMB | A | [GitHub](https://github.com/OpenBMB/InfiniteBench) | Long-context stress test | 12 tasks across 100K+ token contexts | Mixed synthetic (entity substitution) + real | Retrieval, QA, math, code over very long contexts | Accuracy | Yes | No memory persistence; purely single-session; entity substitution creates artificiality[^34][^35] |
| **L-Eval** | 2023 | An et al. | A | [OpenReview](https://openreview.net/forum?id=eUAr4HwU0X) | Long-context standardized eval | 20 sub-tasks, 508 docs, 3K–200K tokens | Mixed human-labeled | Single-session long document understanding | LIE evaluation + LLM judge | Yes | No memory across sessions; no temporal update[^36][^37] |
| **BAMBOO** | 2023 | Dong et al., RUCAIBox | B | [GitHub](https://github.com/RUCAIBox/BAMBOO) | Long-context multi-task | 10 datasets, 5 task types incl. hallucination detection | Mixed | Single-session QA, hallucination, sorting, code | F1, BLEU, accuracy | Yes | No persistent state; no personalization; contamination-avoidance focus[^38][^39] |
| **HELMET** | 2024 | Yen et al., Princeton | A | [arXiv:2410.02694](https://arxiv.org/abs/2410.02694) | Long-context comprehensive | 7 application-centric categories, up to 128K | Mixed real-world | Single-session full-context reasoning | Model-based evaluation | Yes | No multi-session; no temporal update; criticizes NIAH but remains single-session[^1][^3] |
| **Lost in the Middle** | 2023 | Liu et al., Stanford | A | [TACL 2023](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.tacl2023.pdf) | Long-context retrieval bias | Multi-document QA with varied position of relevant doc | Real-world (Wikipedia, NQ) | Positional attention bias in retrieval | QA accuracy by position | Yes | Diagnostic finding, not a standalone benchmark suite[^40][^41] |
| **NoLiMa** | 2025 | ICLR 2025 | A | [OpenReview](https://openreview.net/pdf?id=0OshX1hiSa) | Long-context associative retrieval | NIAH extension with minimal lexical overlap | Synthetic | Associative retrieval requiring latent inference | % accuracy | Yes | Still single-session; synthetic; 12 models tested[^42][^43][^44] |
| **Sequential-NIAH** | 2025 | Yu et al., EMNLP 2025 | A | [ACL Anthology](https://aclanthology.org/2025.emnlp-main.1497/) | Long-context sequential retrieval | Extract multiple ordered needles from 8K–128K contexts | Mixed synthetic/real temporal | Sequential and logical ordering of extracted items | Completeness + sequential consistency | Yes | Still single-session; best model scores only 63.5%[^45][^46] |
| **LongMemEval** | 2024 | Wu et al. | B | [arXiv:2410.10813](https://arxiv.org/abs/2410.10813) | Multi-session memory | 500 curated questions, 5 memory abilities | Human-curated, scalable chat histories | Info extraction, multi-session reasoning, temporal, knowledge updates, abstention | Accuracy (exact match + manual) | Yes | 500 questions is small; histories are simulated; no real user traces[^11][^12][^13] |
| **LoCoMo** | 2024 | Maharana et al., Snap Research / ACL 2024 | A | [GitHub](https://github.com/snap-research/locomo) | Very long-term conversational memory | QA, event summarization on 300-turn, 9K-token avg conversations | LLM+human pipeline, 10 conversations | Long-term conversational recall, multi-modal dialogue | Accuracy, ROUGE | Yes | Only 10 conversations; small scale; now easily saturated by long-context models[^47][^48][^49] |
| **BEAM** | 2025 | Multiple authors | B | [arXiv:2510.27246](https://arxiv.org/abs/2510.27246) | Long-term conversational memory at scale | 100 conversations, 2000 questions, 100K–10M tokens | Auto-generated coherent multi-domain dialogues | Episodic memory, multi-domain recall at extreme scale | Accuracy | Yes (paper code) | Auto-generated conversations; limited to conversational domain[^4][^5][^6] |
| **MemoryAgentBench** | 2025/2026 | Hu et al., ICLR 2026 | A | [arXiv:2507.05257](https://arxiv.org/abs/2507.05257) | Four-competency agent memory | Multi-turn incremental interactions across reformulated datasets | Mixed: reformulated + newly constructed (EventQA, FactConsolidation) | Accurate retrieval, test-time learning, long-range understanding, conflict resolution | Task-specific accuracy | Yes (GitHub) | No real user data; no privacy testing; no temporal drift evaluation[^20][^50][^21] |
| **MemoryArena** | 2026 | He et al., Stanford/UCSD | B | [arXiv:2602.16313](https://arxiv.org/abs/2602.16313) | Multi-session agentic memory | Human-crafted interdependent tasks across 4 agentic domains | Human-crafted | Memorize + act coupling: web nav, planning, search, reasoning | Task success rate | Yes (HuggingFace) | Human-crafted scale may limit coverage; focuses on action coupling[^7][^51][^8] |
| **EvolMem** | 2026 | Shen et al. | B | [arXiv:2601.03543](https://arxiv.org/abs/2601.03543) | Multi-session dialogue memory | 1,600 dialogues, 6.82 sessions avg, cognitive taxonomy | Hybrid synthetic (TIG + NIT) | Declarative + non-declarative (7 fine-grained abilities) | Accuracy, precision, LCS, LLM-judge | Code to be released | Fully synthetic; no real user data; habituation hardest capability[^52][^53][^54] |
| **MemoryBench** | 2025 | Ai et al. | B | [arXiv:2510.17281](https://arxiv.org/abs/2510.17281) | Memory + continual learning | LLM-based user simulator, multi-domain feedback | Simulated feedback, multi-domain | Continual learning from user feedback in service time | Accuracy, efficiency | Partial (code) | Simulated user feedback only; not real-world deployment traces[^55][^56] |
| **PERSONAMEM** | 2025 | Jiang et al., COLM 2025 | A | [arXiv:2504.14225](https://arxiv.org/abs/2504.14225) | Dynamic user profiling | 180+ simulated histories, 60 sessions, 15 task types | LLM-simulated user profiles | Evolving user profile tracking + personalized response generation | Multiple-choice accuracy | Yes (GitHub) | Simulated users; GPT-4.1/o4-mini/Gemini-2.0 all ~50% accuracy[^16][^17][^57] |
| **PrefEval** | 2025 | ICLR 2025 submission | B | [arXiv:2502.09597](https://arxiv.org/abs/2502.09597) | Preference following | 3,000 curated preference-query pairs, 20 topics, 100K tokens max | Human-curated explicit + implicit preferences | Infer, memorize, adhere to user preferences across sessions | Generation + classification accuracy | Yes | Accuracy <10% at 10 turns in zero-shot; limited to stated preferences[^14][^15] |
| **CIMemories** | 2025 | Mireshghallah et al., Meta FAIR | B | [arXiv:2511.14937](https://arxiv.org/abs/2511.14937) | Privacy-sensitive memory | Synthetic profiles, 100+ attributes, diverse task contexts | Synthetic | Contextual integrity: appropriate vs. inappropriate memory recall | Attribute-level violation rate | Yes (GitHub) | Synthetic profiles only; no real user data[^22][^23] |
| **CounterFact** | 2022 | Meng et al. (ROME paper) | A | [arXiv:2202.05262](https://arxiv.org/abs/2202.05262) | Knowledge editing | 21,919 counterfactual triples, GPT-style models | Synthetic counterfactuals | Parametric fact editing in model weights | Efficacy, specificity, generalization | Yes (rome.baulab.info) | Tests weight editing, not agent memory; model collapse with ROME documented[^58][^59] |
| **MQuAKE** | 2023 | Zhong et al., ACL 2023 | A | [arXiv:2305.14795](https://arxiv.org/abs/2305.14795) | Knowledge editing + ripple effects | Multi-hop QA requiring consistent propagation of edits | Synthetic multi-hop chains | Multi-hop consequence of knowledge edits | Multi-hop accuracy after edit | Yes | Tests only edit propagation correctness; not agent-level memory[^18][^19] |
| **TRACE** | 2023 | Wang et al. | B | [arXiv:2310.06762](https://arxiv.org/abs/2310.06762) | Continual learning in LLMs | 8 datasets: domain tasks, multilingual, code, math | Mixed | Catastrophic forgetting + instruction following after training | Accuracy drop post-training | Yes | Tests fine-tuning, not agent runtime memory[^60][^61] |
| **StreamingQA** | 2022 | Liška et al., DeepMind/ICML 2022 | A | [PMLR 2022](https://proceedings.mlr.press/v162/liska22a.html) | Temporal knowledge adaptation | Time-stamped news QA evaluated quarterly | 14 years of real news | Parametric vs. semi-parametric adaptation to new knowledge | QA accuracy over time | Partial | Tests LM adaptation, not agent memory; no multi-session state[^62][^63] |
| **LifelongAgentBench** | 2025 | Zheng et al. | B | [arXiv:2505.11942](https://arxiv.org/abs/2505.11942) | Lifelong learning for LLM agents | Skill-grounded, interdependent tasks across DB/OS/KG environments | Synthetic interactive environments | Cross-task skill accumulation and transfer | Task success, knowledge transfer | Yes | Synthetic environments; no real user data; conventional experience replay limited[^9][^10] |
| **MemoryBank/SiliconFriend** | 2023 | Zhong et al. | B | [arXiv:2305.10250](https://arxiv.org/abs/2305.10250) | Long-term companion memory | Qualitative + simulated user conversations | Simulated (ChatGPT-as-user) | User personality adaptation, memory recall over time | Qualitative + simulated QA accuracy | Yes (GitHub) | Evaluation uses simulated users only; no standardized benchmark suite[^64][^65] |
| **AgentBench** | 2023 | Liu et al., THUDM | B | [arXiv:2308.03688](https://arxiv.org/abs/2308.03688) | General LLM-as-agent | 8 environments: web, OS, DB, game, etc. | Mixed | Multi-turn reasoning + decision-making | Task success rate across 8 environments | Yes | Memory is not a distinct test dimension; focuses on planning/reasoning/tool-use[^66] |
| **WebArena** | 2023 | Zhou et al., CMU | A | [leaderboard](https://leaderboard.steel.dev/registry/benchmarks/webarena) | Web agent task completion | 812 tasks across 4 web environments | Real-world web data | Long-horizon web navigation + tool use | Programmatic task success | Yes | Memory is incidental; no persistent state across sessions[^24] |
| **VisualWebArena** | 2024 | Koh et al., CMU (ACL 2024) | A | [ACL Anthology](https://aclanthology.org/2024.acl-long.50/) | Multimodal web agent | 910 visually grounded tasks across 3 environments | Real-world web + visual data | Multimodal web task completion | Task success rate | Yes | Memory is incidental; baseline success 16.4%; no persistent state[^67][^68] |
| **OSWorld** | 2024 | Multiple authors | A | [leaderboard](https://www.codesota.com/benchmark/osworld) | Computer-use agent | 369 real tasks across Windows/macOS/Ubuntu | Real OS environments | Full desktop app interaction, multi-step planning | Success rate | Yes | No persistent memory across sessions; best agent ~63.5% as of 2026[^69] |
| **SWE-bench** | 2024 | Jimenez et al., Princeton (ICLR 2024) | A | [GitHub](https://github.com/swe-bench/SWE-bench) | Software engineering agent | 2,294 real GitHub issues from Python repos | Real GitHub issues + PRs | Code reasoning + patch generation | % resolved | Yes | Memory not tested; data leakage documented (32.67% solution leakage); most issues pre-cutoff[^70][^25] |
| **GAIA** | 2023 | Mialon et al., Meta/HuggingFace | B | [arXiv:2311.12983](https://arxiv.org/abs/2311.12983) | General AI assistant | 466 real-world questions requiring multi-step tool use | Human-designed real-world questions | Multi-tool reasoning, web browsing, multi-modality | % correct | Partial (questions public) | Memory not a distinct dimension; humans 92% vs GPT-4 ~15%[^27] |
| **τ-bench (tau-bench)** | 2024 | Sierra Research | B | [GitHub](https://github.com/sierra-research/tau2-bench) | Tool-agent-user interaction | Airline + retail customer service, LLM user simulator | Synthetic with rule-based APIs | Policy-adherent tool use, task success, consistency | Task success, consistency across trials | Yes | Memory not a distinct dimension; no persistent user profile across sessions[^26][^71] |
| **ToT (Test of Time)** | 2024 | Fatemi et al., Google | B | [arXiv:2406.09170](https://arxiv.org/abs/2406.09170) | Temporal reasoning | Synthetic temporal arithmetic and semantic QA | Synthetic | Temporal logic, ordering, arithmetic, event sequencing | Accuracy | Yes (HuggingFace) | Synthetic only; tests static temporal reasoning, not memory update or staleness[^72][^73] |

***

## 4. What Each Benchmark Actually Tests

### 4.1 Long-Context Retrieval Benchmarks

**NIAH (Needle-in-a-Haystack)**

- *Claimed purpose:* Test whether LLMs can retrieve a specific fact from a long context window. [AUTHOR CLAIM][^29]
- *Actual tested capability:* Single-fact literal-match retrieval from a static document in one session. [VERIFIED FACT]
- *Requires memory:* No — the needle is in the current context.
- *Can be solved by basic retrieval:* Yes — in fact, this IS basic retrieval.
- *Tests temporal update:* No. *Tests contradiction:* No. *Tests personalization:* No. *Tests forgetting:* No.
- *Key finding:* HELMET showed that despite models achieving near-perfect NIAH scores, they "significantly lag behind" on tasks requiring full-context reasoning. NoLiMa further showed that when literal matches are removed, performance at 32K tokens drops below 50% baseline for 11 of 13 models tested.[^43][^44][^1]
- *Judgment:* **This benchmark tests nothing about agentic memory.** It is misused as a proxy for memory capability. [JUDGMENT]

**RULER**

- *Claimed purpose:* Provide a more comprehensive long-context evaluation beyond NIAH. [AUTHOR CLAIM][^2]
- *Actual tested capability:* Single-session retrieval (NIAH variants), multi-hop variable tracing, and aggregation—all within one context window.
- *Requires memory:* No.
- *Basic RAG can pass:* Partially; multi-hop tracing is harder, but all answers are within the injected context.
- *Temporal/contradiction/personalization:* None tested.
- *Key finding:* "Despite achieving nearly perfect accuracy in the vanilla NIAH test, almost all models exhibit large performance drops as the context length increases."[^2]
- *Judgment:* Better than NIAH for stress-testing context length, but still purely single-session retrieval. [JUDGMENT]

**LongBench**

- *Actual tested capability:* 21 diverse single-session NLP tasks (QA, summarization, code, few-shot learning).
- *Requires memory:* No — all information is in the single-session context.
- *Key limitation:* Average context length is only 6,711 tokens (English), now trivially handled by modern models.[^33]

**InfiniteBench**

- *Actual tested capability:* Long single-session document comprehension at 100K+ tokens. Uses entity substitution to avoid contamination.
- *Requires memory:* No.
- *Key finding:* "Existing long-context LLMs still require significant advancements to process 100K+ contexts effectively."[^35]
- *Gaming risk:* Entity substitution can create unnatural documents; models may use memorized world knowledge shortcuts.

**HELMET**

- *Actual tested capability:* Seven application-centric categories of long-context use, including RAG, summarization, ICL, and reasoning.
- *Requires memory:* No — single-session.
- *Key finding (important for this review):* Explicitly demonstrates that NIAH is unreliable and that RAG tasks are better predictors of downstream performance than synthetic tasks.[^1][^3]
- *Limitation:* Does not test any cross-session or persistent memory capability.

***

### 4.2 Multi-Session and Agent Memory Benchmarks

**LongMemEval**

- *Claimed purpose:* Evaluate five core long-term memory abilities of chat assistants. [AUTHOR CLAIM][^13]
- *Actual tested capability:* Memory retrieval and reasoning across artificially constructed multi-session chat histories. Five ability dimensions: information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention.
- *Requires memory:* Yes — histories are externalized and must be indexed/retrieved.
- *Can be solved by basic retrieval:* Partially — simple extraction questions can be answered by keyword retrieval; multi-session reasoning, temporal, and abstention questions require more.
- *Tests temporal update:* Yes (limited). *Tests contradiction:* Partially (knowledge update dimension). *Tests personalization:* Partially (information extraction from user statements).
- *Tests forgetting:* No explicitly. *Tests memory hygiene:* No. *Tests privacy:* No.
- *Caution:* With large context windows, many LongMemEval instances can now be solved by stuffing entire histories into context. [INFERENCE based on cite:167]
- *Saturation risk:* Moderate to high as context windows expand beyond 128K.

**LoCoMo**

- *Actual tested capability:* QA, summarization, and multimodal dialogue over very long-term conversations (300 turns, 9K tokens avg, up to 35 sessions). Ten conversations total.
- *Requires memory:* Yes — at original context lengths.
- *Can be solved by context stuffing:* Yes, with 128K+ models. [VERIFIED FACT][^6]
- *Key finding:* "LLMs exhibit challenges in understanding lengthy conversations and comprehending long-range temporal and causal dynamics."[^47]
- *Critical limitation:* Only 10 conversations; now easily handled by context stuffing; MemoryArena showed that near-saturated LoCoMo performance does NOT translate to real agentic memory ability.[^7]

**BEAM**

- *Claimed purpose:* A benchmark with conversations up to 10M tokens, where context stuffing is physically impossible. [AUTHOR CLAIM][^5]
- *Actual tested capability:* Long-term episodic memory recall over extremely long coherent multi-domain conversations (100K–10M tokens), 100 conversations, 2,000 questions.
- *Requires memory:* Yes — at 10M tokens, no context window can hold the full history.
- *Can be solved by basic retrieval:* No at 10M tier. At 100K tier, context stuffing is still viable.
- *Tests temporal update:* Partially. *Tests contradiction:* Partially.
- *Key finding:* "Even LLMs with 1M token context windows struggle as dialogues lengthen." RAG baseline scores only 24.9% at 10M; LIGHT scores 26.6%.[^4][^6]
- *Limitation:* Auto-generated conversations may lack the nuance of real user interactions. Evaluation remains primarily recall-based, not action-coupled.

**MemoryAgentBench (ICLR 2026)**

- *Claimed purpose:* The first benchmark to cover all four core memory competencies for agents. [AUTHOR CLAIM][^20]
- *Actual tested capability:* Incremental multi-turn memory across four dimensions in a reformulated multi-turn format. Includes newly constructed EventQA and FactConsolidation datasets.
- *Requires memory:* Yes — the incremental, inject-once-query-multiple-times design requires genuine memory over turns.
- *Tests conflict resolution:* Yes (one of the four core dimensions). *Tests test-time learning:* Yes.
- *Tests personalization:* No explicitly. *Tests temporal drift:* No. *Tests privacy:* No.
- *Key finding:* "Current methods fall short of mastering all four competencies."[^50][^20]

**MemoryArena (2026)**

- *Claimed purpose:* Benchmark agent memory in multi-session Memory-Agent-Environment loops. [AUTHOR CLAIM][^7]
- *Actual tested capability:* Human-crafted interdependent agentic tasks (web navigation, preference-constrained planning, progressive search, sequential reasoning) across sessions, where earlier actions must be remembered to succeed in later tasks.
- *Requires memory:* Yes — memorize + act coupling is the core design principle.
- *Can be solved by basic retrieval:* No — the tasks require using memories to guide actions, not just recall facts.
- *Tests temporal update:* Partially. *Tests contradiction:* Partially (preference-constrained planning).
- *Key finding:* Directly falsifies LoCoMo as a proxy: agents with "near-saturated performance on LoCoMo perform poorly in our agentic setting."[^8][^7]
- *Judgment:* **Best current benchmark for testing whether memory is causally useful for action.** [JUDGMENT]

**EvolMem (2026)**

- *Claimed purpose:* Evaluate both declarative and non-declarative memory in multi-session dialogue. [AUTHOR CLAIM][^52]
- *Actual tested capability:* 7 fine-grained memory capabilities derived from cognitive psychology taxonomy, across 1,600 dialogues with 6.82 sessions average.
- *Tests forgetting:* Indirectly (session count difficulty scaling). *Tests non-declarative memory:* Yes — unique among verified benchmarks.
- *Key finding:* "No LLM consistently outperforms others across all memory dimensions. Agent memory mechanisms do not necessarily enhance LLMs' capabilities and often exhibit notable efficiency limitations."[^52]

***

### 4.3 Personalization Benchmarks

**PERSONAMEM (COLM 2025)**

- *Actual tested capability:* Whether LLMs can track evolving user profiles across 60 sessions and respond appropriately to current user state (not historical state).
- *Tests personalization over time:* Yes — specifically designed for profile drift.
- *Tests preference drift:* Yes. *Tests stale-fact detection:* Yes (implicitly — must recognize when old preference is obsolete).
- *Key finding:* Frontier models including GPT-4.1, o4-mini, and Gemini-2.0 all score ~50% accuracy.[^16][^17]
- *Limitation:* Fully simulated user profiles; no real-world user traces.

**PrefEval**

- *Actual tested capability:* Proactive preference following in long-context conversations; both explicit and implicit preferences; generation + classification evaluation.
- *Tests preference decay over context:* Yes. *Tests personalization:* Yes.
- *Key finding:* "Preference following accuracy falls below 10% at merely 10 turns (~3K tokens) across most evaluated models in zero-shot settings."[^15][^14]

***

### 4.4 Privacy Memory Benchmarks

**CIMemories (Nov 2025, Meta FAIR)**

- *Actual tested capability:* Whether models appropriately control information flow from memory based on task context — contextual integrity of persistent memory.
- *Tests memory hygiene:* Yes — this is the explicit design goal.
- *Tests negative memory effects:* Yes — quantifies leakage violations.
- *Key finding:* "Frontier models exhibit up to 69% attribute-level violations." GPT-5's violations rise from 0.1% to 9.6% as tasks increase from 1 to 40.[^23][^22]

***

### 4.5 Knowledge Editing Benchmarks

**CounterFact / ROME**

- *Actual tested capability:* Whether rank-one model weight edits preserve edited facts, maintain specificity, and generalize. Tests parametric memory modification, not external agent memory.
- *Tests forgetting:* Indirectly (specificity = not forgetting other facts).
- *Tests causal relevance:* No. *Tests agent-level memory:* No.
- *Key finding:* Model collapse documented with ROME sequential editing on CounterFact specifically; does not occur with zsRE dataset.[^59]

**MQuAKE**

- *Actual tested capability:* Whether editing one fact causes correct propagation through multi-hop reasoning chains.
- *Key finding:* "Current knowledge-editing approaches can recall edited facts accurately, they fail catastrophically on the constructed multi-hop questions."[^18]
- *Judgment:* Tests the right thing (ripple effects of edits) but in the parametric domain, not agent memory stores. [JUDGMENT]

***

### 4.6 Long-Horizon Task Benchmarks (Indirect Memory)

**WebArena, VisualWebArena, OSWorld, SWE-bench, GAIA, τ-bench**

All these benchmarks share a structural characteristic: memory is an incidental, uncontrolled variable rather than the primary tested capability. A highly capable planner with zero cross-session memory can succeed on most tasks.

- *WebArena:* 812 tasks, single-session, programmatic evaluation. Memory is not required.[^24]
- *OSWorld:* 369 real computer tasks; no cross-session state; best agent ~63.5%.[^69]
- *SWE-bench:* Tests code patch generation; data leakage documented; 32.67% "solution leakage" identified.[^70]
- *GAIA:* Real-world tool-use questions; memory is not a distinct dimension; primarily tests tool chaining and reasoning.[^27]
- *τ-bench:* Tests tool-agent-user interaction consistency; simulated users; no persistent user memory across tasks.[^26][^71]

**For agentic memory evaluation, these benchmarks are useful as baselines for task completion capability but should not be used to measure memory directly.** [JUDGMENT]

***

## 5. Benchmark Family Map

### Family 1: Long-Context Recall

**Best representatives:** RULER, HELMET, InfiniteBench, NIAH

**What they measure well:** How much information a model can attend to within a single long context window; performance degradation with length; position bias (Lost in the Middle effect).

**What they systematically miss:** Everything post-session. No persistence, no update, no forgetting, no multi-session state, no temporal drift, no personalization.

**Useful for a new memory project?** Only as a baseline component showing that the underlying model can retrieve information within context. Not as a primary memory evaluation.[^1][^2]

***

### Family 2: Long-Document QA

**Best representatives:** LongBench, L-Eval, BAMBOO, InfiniteBench

**What they measure well:** Comprehension of complex, long documents; multi-document reasoning; domain coverage.

**What they miss:** Multi-session memory, temporal state, personalization, anything beyond document comprehension.

**Useful for memory project?** No — these test reading, not memory. [JUDGMENT]

***

### Family 3: Multi-Hop Retrieval

**Best representatives:** RULER (multi-hop tracing), MQuAKE (for knowledge editing), NoLiMa (associative retrieval)

**What they measure well:** Chained reasoning across multiple stored facts; propagation of edits; retrieval without literal matching.

**What they miss:** Cross-session persistence, temporal update, personalization, privacy.

**Useful for memory project?** Partially — good for testing retrieval precision with distractors. [JUDGMENT]

***

### Family 4: Multi-Session Memory

**Best representatives:** LongMemEval, LoCoMo, BEAM, MemoryAgentBench, MemoryArena, EvolMem, PERSONAMEM

**What they measure well (collectively):**
- Information extraction from long conversation histories [LongMemEval, LoCoMo]
- Memory at extreme scales where stuffing is impossible [BEAM at 10M tokens]
- Four core agent memory competencies including conflict resolution [MemoryAgentBench]
- Memory coupled to action in agentic loops [MemoryArena]
- Declarative + non-declarative memory types [EvolMem]
- Evolving user profile tracking [PERSONAMEM]

**What they collectively miss:** Real user data (all use simulation), privacy-sensitive selective recall, long-horizon procedural skill reuse, multi-agent shared memory, memory provenance, cost/latency constraints.

**Useful for memory project?** Yes — this is the primary evaluation family. LongMemEval and MemoryArena are the highest-value starting points. [JUDGMENT][^13][^7]

***

### Family 5: Personalization

**Best representatives:** PERSONAMEM, PrefEval

**What they measure well:** Preference tracking over time; adaptation to evolving user state; explicit vs. implicit preference handling.

**What they miss:** Privacy-sensitive recall; real user data; negative personalization effects (harmful memory); cross-user contamination.

**Useful for memory project?** Yes — critical for evaluating user-facing memory systems. [JUDGMENT][^14][^16]

***

### Family 6: Temporal Reasoning

**Best representatives:** LongMemEval (temporal dimension), ToT (Test of Time), StreamingQA, PAT-Questions

**What they measure well:** Temporal ordering, arithmetic over dates, adaptation to new knowledge over time.

**What they miss:** Agent-level stale-fact detection in memory stores, preference drift over time, temporal contradiction between stored memories.

**Useful for memory project?** Partially — the temporal dimension of LongMemEval is most directly relevant. ToT is purely static temporal logic, not agent memory. [JUDGMENT]

***

### Family 7: Knowledge Editing

**Best representatives:** CounterFact, MQuAKE, zsRE, RippleEdits

**What they measure well:** Parametric model editing: locality, generalization, fluency post-edit, ripple effect propagation.

**What they miss:** Everything about external agent memory. These benchmarks test model weights, not retrieval stores, memory graphs, or episodic buffers.

**Useful for memory project?** Only if the project involves parametric editing. For external memory systems, these benchmarks are essentially irrelevant as primary evaluations, but provide a useful analogy for memory-update design. [JUDGMENT][^58][^18]

***

### Family 8: Continual Learning

**Best representatives:** TRACE, LifelongAgentBench, MemoryBench, StreamingQA

**What they measure well:** Catastrophic forgetting prevention; cross-task knowledge transfer; adaptation to streaming knowledge.

**What they miss:** Real user personalization; privacy; multi-session agentic action coupling; explicit memory hygiene.

**Useful for memory project?** LifelongAgentBench is the most relevant — it tests skill transfer across interdependent tasks. TRACE is training-time focused and less relevant for inference-time agent memory. [JUDGMENT][^55][^9]

***

### Family 9: Long-Horizon Agents

**Best representatives:** WebArena, VisualWebArena, OSWorld, τ-bench, GAIA, SWE-bench, AgentBench

**What they measure well:** Multi-step task planning, tool use, web navigation, software engineering, policy adherence.

**What they miss:** Cross-session state, persistent memory, temporal update, personalization — memory is incidental.

**Useful for memory project?** As task-completion baselines only. Provides the downstream task context in which memory should improve performance. [JUDGMENT]

***

## 6. "Basic RAG Can Pass This" Analysis

The following patterns allow shallow RAG or context stuffing to score competitively without genuine memory capability.

### Pattern 1: Single-Session Needle Retrieval

**Affected benchmarks:** NIAH, RULER, InfiniteBench, LongBench, L-Eval, BAMBOO

**How RAG passes:** Chunk the document, embed, retrieve the relevant chunk by query similarity. Literal match between needle wording and query wording is the primary signal.

**Evidence:** Claude 3 Opus "scored above 99% accuracy on NIAH" and "even pointed out that the needle sentence seemed to be artificially inserted into the text" — demonstrating that the benchmark tests recognizability, not memory. NoLiMa was explicitly designed to remove literal match shortcuts, yet performance still degrades substantially.[^30][^43]

**Why it matters:** Developers marketing context window size use NIAH as a "pass/fail" memory test. Passing NIAH provides no evidence of agentic memory capability.

**How to harden:** Remove lexical overlap between needle and query (NoLiMa approach); require multi-hop chains; require temporal ordering of multiple facts; use adversarial distractors.

***

### Pattern 2: Context Stuffing on Pre-2024 Memory Benchmarks

**Affected benchmarks:** LoCoMo, early LongMemEval settings

**How it works:** With 128K+ context windows, entire conversation histories fit in context. The model performs single-pass attention over all history rather than retrieving selectively.

**Evidence:** Hindsight's benchmark analysis explicitly states: "On most LoComo and LongMemEval instances today, a naive dump everything into context approach scores competitively."[^6]

**Why it matters:** A system with zero memory architecture can score competitively on these benchmarks by sheer context size, making the benchmarks useless for discriminating memory architectures.

**How to harden:** Use BEAM at 10M tokens; require memory at scales that exceed all available context windows.

***

### Pattern 3: Recency Bias Exploitation

**Affected benchmarks:** Any sequential conversation benchmark where recent information is most query-relevant.

**How it works:** Simple RAG with recency weighting retrieves the most recent N items and answers from those. This simulates "memory" but ignores older, possibly more relevant or contradictory information.

**Evidence:** The "lost in the middle" phenomenon confirms that LLMs exhibit U-shaped attention bias — attending to beginning and end of context. RAG systems that chunk by recency can exploit this.[^40][^41]

**How to harden:** Include questions where only older sessions contain the answer; penalize systems that systematically ignore older memories.

***

### Pattern 4: Summary Memory Shortcut

**Affected benchmarks:** Benchmarks that allow summarization-based memory (any benchmark that does not restrict memory type).

**How it works:** A system compresses entire session histories into rolling summaries, then retrieves from those summaries. For simple factual questions, summaries are often sufficient.

**Evidence:** [INFERENCE] — Summary-based baselines in LongMemEval show competitive performance on simple information extraction tasks. The fact that session decomposition was a proposed improvement in LongMemEval suggests summaries are insufficient for complex tasks.[^12]

**How to harden:** Include questions that require precise wording or exact values not preserved in summaries; test verbatim recall alongside semantic recall.

***

### Pattern 5: Synthetic Shortcut Exploitation in Knowledge Editing

**Affected benchmarks:** CounterFact (ROME sequential editing)

**How it works:** The CounterFact dataset contains patterns exploitable by the ROME algorithm that cause model collapse — "disabling edits" — demonstrating that the benchmark's structure creates artifacts not present in real editing scenarios.

**Evidence:** "Model collapse with ROME only happens when making edits using the CounterFact dataset and does not happen when using the zsRE dataset."[^59]

**How to harden:** Use diverse, realistic edit distributions; test longitudinal edit sequences rather than isolated edits.

***

## 7. Real Breakthrough Exposure Test

A memory benchmark that would genuinely expose a breakthrough must satisfy the following criteria. Each criterion is marked by current evaluation coverage status.

| Criterion | Required Capability | Current Benchmark Coverage | Verdict |
|-----------|-------------------|--------------------------|---------|
| **Long-horizon usefulness** | Memory guides successful action 10+ sessions later | MemoryArena (partial) | ⚠️ Weak |
| **Multi-session continuity** | Facts from session 1 correctly available in session 50 | BEAM (recall only), MemoryArena (action coupling) | ⚠️ Partial |
| **Memory update and correction** | Updated fact replaces stale fact correctly, without corrupting related memories | LongMemEval (knowledge update dim.), MQuAKE (parametric only) | ⚠️ Weak |
| **Temporal validity** | "What was true then" ≠ "what is true now"; preference drift detected | PERSONAMEM (limited), LongMemEval (temporal dim.) | ⚠️ Partial |
| **Contradiction handling** | System detects and resolves conflicting memories | MemoryAgentBench (conflict resolution), EvolMem (inference dim.) | ⚠️ Partial |
| **Selective forgetting** | Correctly discards stale/irrelevant memories; does not recall after user deletion | EvolMem (habituation), LifelongAgentBench (indirect) | ❌ Missing |
| **Privacy-preserving recall** | Does not leak sensitive attributes in inappropriate task contexts | CIMemories | ⚠️ Early |
| **Provenance and explainability** | Can attribute recalled fact to source session and context | [UNKNOWN] No verified benchmark found | ❌ Missing |
| **Causal relevance** | Recalled memory causally changed the outcome (not coincidental retrieval) | MemoryArena (action coupling is proxy) | ⚠️ Weak |
| **Skill transfer** | Procedural pattern from session 1 applied to new task in session 20 | LifelongAgentBench | ⚠️ Weak |
| **Low context pollution** | System does not degrade from irrelevant retrieved memories | [INFERENCE] No dedicated verified benchmark | ❌ Missing |
| **Cost/latency constraints** | Memory retrieval cost scales acceptably with history size | EvolMem notes efficiency limitations; MemoryBench includes efficiency | ⚠️ Partial |
| **User trust** | System behavior is predictable and explainable to users | Not evaluated in any verified benchmark | ❌ Missing |

**Summary:** Only causal relevance and action coupling (MemoryArena), extreme-scale recall (BEAM), and privacy (CIMemories) come close to breakthrough-exposure criteria. All other dimensions are either weakly tested or completely missing from verified benchmarks. [JUDGMENT]

***

## 8. Benchmark Gap Analysis

The following 10 gaps are ranked by research impact and consequence for builders.

### Gap 1: No Benchmark Tests Memory-Action Coupling at Scale

**Missing capability:** Long-horizon tasks (20+ sessions) where specific memorized facts, preferences, or skills must guide concrete actions — not just be recalled.

**Why current benchmarks fail:** LoCoMo and LongMemEval test recall; long-horizon agent benchmarks (WebArena, OSWorld) don't track memory; MemoryArena is the closest but is still early-stage.

**Consequence for builders:** Systems optimized on existing benchmarks may recall facts perfectly but never use them to improve downstream decisions.

**Possible benchmark design:** Multi-session agent tasks where session N cannot succeed without applying a lesson from session 1. Reward function separates retrieval accuracy from task outcome.

**Implementation difficulty:** High — requires reproducible interactive environments, long session coordination, and ground-truth action attribution.

**Research value:** Very high. [JUDGMENT]

***

### Gap 2: No Benchmark Tests Stale-Fact Detection and Temporal Contradiction Resolution

**Missing capability:** A memory store contains Fact A from month 1 and contradictory Fact A' from month 6. The system must use A' and flag A as stale, not blend them.

**Why current benchmarks fail:** LongMemEval's "knowledge update" dimension tests whether new facts are learned, but not whether old contradictory facts are correctly suppressed. Temporal benchmarks (ToT, PAT-Questions) test static temporal reasoning, not dynamic staleness in a live memory store.

**Consequence for builders:** Systems may accumulate stale memories and confabulate by blending old and new facts.

**Possible design:** Real or simulated user interaction histories with deliberately constructed temporal contradictions at controlled intervals. Question: "What is the user's current preference for X?" with the correct answer depending on recognizing the most recent update.

**Implementation difficulty:** Medium — can be constructed synthetically with temporal metadata.

**Research value:** High. [JUDGMENT]

***

### Gap 3: No Verified Benchmark for Selective Forgetting and User-Requested Deletion

**Missing capability:** User asks the system to forget a specific fact or conversation; system correctly no longer surfaces that information; no residual leakage.

**Why current benchmarks fail:** EvolMem tests habituation (stable pattern formation), not deletion on demand. No verified dedicated benchmark for intentional forgetting exists.

**Consequence for builders:** GDPR and privacy requirements cannot be evaluated; systems that cannot forget are non-deployable in regulated contexts.

**Possible design:** Introduce a forgetting request at session N; test at session N+5 whether the deleted fact still influences outputs. Adversarial probe: include the deleted topic in a distractor-rich retrieval query.

**Implementation difficulty:** Medium.

**Research value:** High (regulatory + technical). [JUDGMENT]

***

### Gap 4: No Benchmark for Memory Provenance and Explainability

**Missing capability:** System correctly identifies which session, source, and context a retrieved memory came from, and can present this to users or downstream processes.

**Why current benchmarks fail:** All current benchmarks evaluate only output correctness (is the recalled fact correct?), not provenance (where did this fact come from?).

**Consequence for builders:** Systems cannot support user trust mechanisms, audit logs, or debugging of incorrect memory retrieval.

**Possible design:** Provenance attribution task: system must cite session ID, turn, and approximate wording of the source for each recalled memory.

**Implementation difficulty:** Medium — annotation cost is the primary challenge.

**Research value:** High (trust, safety, debugging). [JUDGMENT]

***

### Gap 5: No Benchmark for Multi-Agent Shared Memory and Contamination

**Missing capability:** Multiple agents share a memory store; information written by Agent A should be usable by Agent B; private or role-specific memories should not leak across agents.

**Why current benchmarks fail:** All verified benchmarks test single-agent memory. The 2025 survey on agentic memory systems noted "multi-agent memory" as a key frontier.[^74]

**Consequence for builders:** Multi-agent architectures cannot be evaluated for memory safety, contamination, or coordination.

**Possible design:** Two-agent tasks where Agent A learns a fact in session 1; Agent B must use it in session 2; adversarial probe: inject a false memory via Agent A to test contamination propagation.

**Implementation difficulty:** High — requires multi-agent infrastructure.

**Research value:** High. [JUDGMENT]

***

### Gap 6: No Benchmark for Procedural/Skill Memory Reuse

**Missing capability:** System observes a workflow in session 1 (e.g., how a user likes to structure reports); applies the learned procedure in session 20 without re-explanation.

**Why current benchmarks fail:** LifelongAgentBench tests skill transfer across database/OS/KG tasks but in a controlled synthetic setting. No benchmark tests procedural memory reuse in naturalistic open-domain agent scenarios.

**Consequence for builders:** Systems cannot evaluate the "learns your workflow" value proposition.

**Possible design:** Demonstration-then-application tasks: session 1 demonstrates a multi-step procedure; sessions 2–5 require applying the procedure to novel inputs; session 10 tests retention without hints.

**Implementation difficulty:** Medium-high.

**Research value:** High (user value proposition). [JUDGMENT]

***

### Gap 7: Real-User-Trace Benchmark for Longitudinal Memory

**Missing capability:** A benchmark grounded in real (anonymized) user interaction histories, not LLM-simulated users.

**Why current benchmarks fail:** Every verified multi-session benchmark uses LLM-simulated users (PERSONAMEM, EvolMem, LoCoMo pipeline, MemoryBank). Simulated users systematically lack the messiness, contradiction, and domain variety of real users.

**Consequence for builders:** Benchmarks built on simulated users may overfit to LLM-generated conversation patterns.

**Implementation difficulty:** Very high — requires data collection, IRB approval, anonymization, and significant annotation cost.

**Research value:** Very high (ecological validity). [JUDGMENT]

***

### Gap 8: Cost/Latency as a First-Class Metric

**Missing capability:** Memory system benchmarks that jointly measure accuracy and the per-query cost or latency of memory retrieval.

**Why current benchmarks fail:** EvolMem notes that "agentic memory systems incur substantial latency." IBM's review of agent benchmarks recommends that "API costs, token usage, inference speeds, and overall resource consumption should be measured." No memory benchmark operationalizes this.[^75][^52]

**Consequence for builders:** Winning a memory benchmark with a system that makes 50 LLM calls per memory retrieval is not deployable.

**Possible design:** Augment any existing benchmark with a cost-accuracy Pareto frontier score; penalize systems that exceed a token budget; include a cost-normalized leaderboard.

**Implementation difficulty:** Low — can be added to existing benchmark infrastructure.

**Research value:** Medium-high (deployment readiness). [JUDGMENT]

***

### Gap 9: Negative Memory Effects (Harmful Retrieval)

**Missing capability:** Cases where surfacing a memory causes harm — incorrect medical advice based on stale health information; discriminatory recommendations based on outdated demographic assumptions; inappropriate disclosure of sensitive context.

**Why current benchmarks fail:** CIMemories addresses leakage but not downstream harm from surfaced-but-incorrect memories.

**Consequence for builders:** Memory systems optimized purely for recall accuracy may surface harmful information.

**Implementation difficulty:** Medium — requires careful adversarial case design.

**Research value:** High (safety). [JUDGMENT]

***

### Gap 10: Benchmark Saturation and Gaming Resistance

**Missing capability:** Benchmarks that remain discriminative as model capabilities improve, resisting over-fitting and benchmark-specific optimization.

**Why current benchmarks fail:** LoCoMo and many LongMemEval settings are now saturated by context stuffing. The 2026 agentic memory survey explicitly noted "existing benchmarks are underscaled and often saturated."[^28]

**Consequence for builders:** Leaderboards become meaningless; benchmark optimization replaces genuine capability improvement.

**Possible design:** Live/dynamic benchmarks with continuously updated content; adversarial evaluation protocols; task structures that are provably not solvable by known shortcut patterns.

**Implementation difficulty:** High — requires ongoing maintenance.

**Research value:** Very high (long-term field health). [JUDGMENT]

***

## 9. Candidate Benchmark Designs

### Benchmark Concept 1: HORIZON — Long-Horizon Memory-Action Attribution Benchmark

**[LIKELY USEFUL]**

**Core task:** A simulated personal assistant agent interacts with a user over 50 sessions across 90 days. Each session involves realistic tasks (scheduling, email drafting, research). At session 50, a set of evaluation tasks is administered where correct completion requires integrating information from at least 3 prior non-adjacent sessions. A counterfactual baseline (same task with those memories erased) quantifies the causal value of memory.

**Memory capability tested:** Long-horizon causal usefulness; multi-session integration; memory-action coupling.

**Dataset construction:** LLM-simulated + human-curated critical sessions; controlled temporal dependencies with verified ground truth.

**Ground truth design:** For each evaluation task, a dependency graph specifies which prior sessions are causally necessary. The scoring function penalizes systems that get the right answer for the wrong reason (by checking intermediate retrieval logs).

**Scoring method:** Task success rate × provenance precision; counterfactual delta (score with memory − score without memory).

**Adversarial cases:** Tasks where the wrong memory leads to plausible but incorrect actions; tasks where recency bias would select the wrong session.

**What shallow RAG would fail:** Tasks requiring integration across 5+ non-adjacent sessions separated by irrelevant content; tasks where the relevant memory requires semantic inference, not keyword match.

**What a real memory system must do:** Index with semantic tags, not just embeddings; maintain temporal metadata; return causal memory chains, not just top-k similar passages.

**Cost to build:** High — requires 50-session simulation infrastructure, ground-truth dependency annotation, counterfactual evaluation harness.

**Risk of benchmark gaming:** Medium — counterfactual design reduces gaming; dependency annotation creates a verifiable audit trail.

***

### Benchmark Concept 2: DRIFT — Temporal Memory Update and Preference Drift Benchmark

**[LIKELY USEFUL]**

**Core task:** A user's preferences, facts, and life circumstances change over 12 simulated months. The memory system must correctly surface the current state, flag outdated information, and resolve contradictions. Tasks are administered at multiple time points with ground truth keyed to the current state at each time point.

**Memory capability tested:** Temporal validity, stale-fact detection, contradiction resolution, preference drift tracking.

**Dataset construction:** Synthetic user profiles with controlled temporal transitions; each fact has a validity window; contradictions are injected at known times with known resolution ground truth.

**Ground truth design:** For each query at time T, the ground truth is the value of the fact that was valid at time T, with explicit staleness labels for superseded values.

**Scoring method:** Temporal accuracy (correct at T) × staleness suppression rate (% of stale values not returned when queried at T+n) × contradiction resolution accuracy.

**Adversarial cases:** Queries that can be answered correctly by the stale value but not the current value; queries where both old and new values are plausible; queries about facts that changed back (A → B → A pattern).

**What shallow RAG would fail:** Recency-bias RAG would fail the "reversion" case (A → B → A); keyword-match RAG would fail contradictions where old and new values use similar language.

**What a real memory system needs:** Temporal metadata on every stored fact; explicit staleness marking; contradiction detection and resolution logic.

**Cost to build:** Medium — primarily annotation and temporal simulation infrastructure.

**Risk of benchmark gaming:** Low-medium — temporal metadata requirements are hard to fake; reversion patterns are adversarially robust.

***

### Benchmark Concept 3: FORGE — Selective Forgetting and Privacy Hygiene Benchmark

**[LIKELY USEFUL]**

**Core task:** A user issues explicit and implicit forgetting requests across sessions. The benchmark evaluates: (1) whether explicitly deleted information is truly removed; (2) whether related but undeleted information is preserved; (3) whether adversarial probes can still surface deleted information.

**Memory capability tested:** Selective forgetting, memory hygiene, privacy compliance, locality of deletion.

**Dataset construction:** Synthetic user histories with tagged "forgettable" information at varying semantic distances from other stored facts.

**Ground truth design:** Binary: did the system surface the deleted information when probed? Did it preserve undeleted related information correctly?

**Scoring method:** Deletion efficacy rate (% of deleted items not surfaced under adversarial probing) × preservation rate (% of undeleted items still correctly recalled after deletion event).

**Adversarial cases:** Probe questions that do not mention the deleted fact by name but require it for a full answer; questions where the deleted fact is embedded in a summary that was not deleted.

**What shallow RAG would fail:** Vector-store-based systems that cannot delete individual embedding chunks without corrupting the index; systems with cached summaries containing deleted information.

**What a real memory system needs:** Chunk-level deletion with propagation to derivative memories (summaries, extracted facts); adversarial probe resistance.

**Cost to build:** Medium — primarily requires careful ground-truth design for the deletion + preservation duality.

**Risk of gaming:** Low — deletion efficacy under adversarial probing is difficult to fake.

***

### Benchmark Concept 4: COLLAB — Multi-Agent Shared and Role-Specific Memory Benchmark

**[UNCERTAIN]**

**Core task:** A two-agent or three-agent system (e.g., planner + executor + reviewer) processes a multi-session project. Agents have role-specific memory (planner sees strategy; executor sees tool outputs; reviewer sees both). Evaluation tests: (a) correct information sharing; (b) absence of cross-role contamination; (c) consistency across agents' views of shared facts.

**Memory capability tested:** Multi-agent shared memory, role-specific access control, contamination prevention.

**Dataset construction:** Simulated multi-agent project scenarios with defined role boundaries and information access policies.

**Ground truth design:** For each agent-at-session, specify which facts should be accessible and which should not. Ground truth = accessibility matrix.

**Scoring method:** Shared fact availability rate × contamination rate (lower = better) × consistency rate across agents.

**Adversarial cases:** Prompt injection via one agent attempting to write false memories into the shared store; agent attempting to read out-of-role memories.

**What shallow RAG would fail:** Flat vector stores with no access control; systems without agent-specific memory namespaces.

**Cost to build:** High — requires multi-agent infrastructure and access control modeling.

**Risk of gaming:** Medium — adversarial injection cases are hard to game without genuine access control.

***

### Benchmark Concept 5: TRANSFER — Procedural and Episodic Skill Transfer Benchmark

**[PARTIALLY USEFUL]**

**Core task:** In session 1–3, a user teaches the agent a complex multi-step procedure (e.g., how they like their research reports structured; their coding style preferences). Sessions 4–10 test silent application of the learned procedure to new inputs without re-teaching. Sessions 15+ test retention and generalization to new domains.

**Memory capability tested:** Procedural skill reuse, episodic-to-semantic consolidation, transfer across domains.

**Dataset construction:** Human-authored procedure demonstrations with novel-domain evaluation tasks; controlled for surface similarity between demonstration and test.

**Ground truth design:** Expert-annotated rubrics for procedure compliance in evaluation tasks.

**Scoring method:** Procedure compliance rate × generalization distance (how far the test task is from the demonstration domain).

**Adversarial cases:** Test tasks that share surface features but require different procedures; test tasks where the demonstrated procedure is counterproductive.

**What shallow RAG would fail:** Systems that retrieve the demonstration verbatim and copy it rather than extracting the abstract procedure; systems with no semantic consolidation.

**Cost to build:** Medium-high — requires human annotation for procedure compliance rubrics.

**Risk of gaming:** Medium — rubric-based scoring introduces subjectivity; LLM judges can be calibrated with human validation.

***

## 10. Recommended Benchmark Strategy for a New Open-Source Memory System

### Benchmarks to Reuse (High Value)

| Benchmark | Why Reuse | Usage |
|-----------|-----------|-------|
| **LongMemEval** | Well-validated, multi-ability, publicly available, includes temporal and knowledge-update dimensions | Primary evaluation suite; use all 5 ability dimensions[^13] |
| **MemoryAgentBench** | Covers 4 core competencies including conflict resolution and test-time learning; ICLR 2026 | Secondary evaluation; especially for conflict resolution dim.[^20][^21] |
| **PERSONAMEM** | Tests evolving user profiles; COLM 2025; frontier models at ~50% = strong discrimination | Personalization evaluation; use for user-profile tracking claims[^16] |
| **BEAM (100K tier)** | Provides a scale stress test with narrative coherence | Long-term episodic recall; compare all tiers for scaling analysis[^5][^6] |
| **MemoryArena** | Directly tests memory-action coupling; falsifies LoCoMo as proxy | Critical agentic memory eval; use as primary action-coupling test[^7] |
| **CIMemories** | Only verified privacy/contextual integrity memory benchmark | Privacy evaluation if system stores sensitive user information[^23] |

### Benchmarks to Avoid (Low Signal / High Gaming Risk)

| Benchmark | Reason to Avoid |
|-----------|----------------|
| **NIAH (vanilla)** | Saturated; does not test memory; gameable by literal match[^1][^30] |
| **LoCoMo** | Saturated by context stuffing with modern models[^6] |
| **LongBench (as memory claim)** | Tests reading, not memory; single-session only[^33] |
| **CounterFact (alone)** | Tests parametric editing, not agent memory; model collapse risk[^59] |
| **AgentBench** | Memory is not a tested dimension[^66] |

### Benchmarks to Adapt

| Benchmark | Adaptation |
|-----------|-----------|
| **LongMemEval** | Extend the knowledge-update and temporal dimensions with more adversarial contradiction cases; add cost/latency tracking as a secondary metric |
| **MemoryArena** | Instrument intermediate memory states to enable provenance scoring; add a multi-agent variant |
| **BEAM** | Add a temporal-contradiction sub-task to the 1M+ token tiers |

### New Benchmark to Build First

**DRIFT** (Temporal Memory Update and Preference Drift Benchmark) — described in Section 9 — addresses the largest verified gap (stale-fact detection + temporal contradiction resolution) at moderate construction cost. This gap is directly relevant to deployed memory systems and no existing verified benchmark covers it adequately. Build this first.

### Minimum Credible Evaluation Suite

To credibly claim a memory system breakthrough, the following **minimum evaluation suite** is recommended:

1. **LongMemEval** — all 5 ability dimensions
2. **MemoryArena** — multi-session agentic action coupling
3. **PERSONAMEM** — evolving user profile tracking
4. **BEAM at 1M and 10M tiers** — extreme-scale recall stress test
5. **CIMemories** — contextual integrity and privacy
6. **One long-horizon task benchmark** (WebArena or τ-bench) — as a task-completion baseline proving the memory system does not degrade agent performance

### Public Leaderboard Strategy

- Host on HuggingFace Spaces or equivalent.
- Include a "cost-normalized" leaderboard column (accuracy / token-cost-per-query).
- Pin a "no memory" baseline (full context stuffing), a RAG baseline, and a conversation summary baseline in all leaderboard tables.
- Publish all baseline results before claiming state-of-the-art.
- Commit to re-running baselines every 6 months as context windows expand (to avoid LoCoMo-style saturation).

### Required Baselines

| Baseline | Description | Justification |
|---------|-------------|---------------|
| **No memory (full stuffing)** | Entire conversation history injected as context | Establishes cost of not using memory; reveals saturation risk |
| **Conversation summary** | Rolling summary of prior sessions as context | Tests whether compression alone is sufficient |
| **Vector RAG** | Chunked conversation history, vector similarity retrieval | Primary comparison for retrieval-based memory systems |
| **Graph memory** | Knowledge graph of extracted facts with semantic edges | Comparison for structured memory approaches |
| **Time-aware retrieval** | Vector RAG + recency weighting | Tests whether temporal metadata alone adds value |
| **Human-curated memory** | Human-selected relevant memories (oracle upper bound) | Upper-bound calibration |
| **Proposed system** | The new architecture | Primary claim |

### Ablation Strategy

For each claimed memory innovation, run ablations that independently remove:
1. The memory store (no-memory baseline)
2. Temporal metadata
3. Contradiction resolution logic
4. Update/deletion capability
5. Any proprietary retrieval enhancement

Report each ablation on LongMemEval and MemoryArena to establish which components drive performance gains.

***

## 11. Evidence Ledger

| Claim | Supporting Source(s) | Grade | Evidence Strength | Confidence | Caveat |
|-------|---------------------|-------|------------------|------------|--------|
| NIAH does not reliably predict downstream LM performance | HELMET (arXiv:2410.02694)[^1] | A | Strong | High | Based on 59 models; ICLR 2025 paper |
| Most LongMemEval/LoCoMo instances can now be solved by context stuffing | Hindsight benchmark blog post (hindsight.vectorize.io)[^6] | C | Moderate | Medium-High | Blog/vendor post, not peer-reviewed paper; but consistent with window size growth argument |
| MemoryArena agents near-saturated on LoCoMo fail in agentic setting | MemoryArena (arXiv:2602.16313)[^7] | B | Strong | High | arXiv preprint; verified repo on HuggingFace |
| PERSONAMEM: frontier models ~50% accuracy on evolving profiles | PERSONAMEM (arXiv:2504.14225; COLM 2025)[^16][^17] | A | Strong | High | Published COLM 2025; multiple models tested |
| PrefEval: accuracy < 10% at 10 turns in zero-shot | PrefEval (arXiv:2502.09597)[^14] | B | Strong | High | arXiv preprint with code/data |
| CIMemories: frontier models exhibit up to 69% contextual integrity violations | CIMemories (arXiv:2511.14937)[^23] | B | Strong | High | Meta FAIR authors; code available |
| MQuAKE: editors fail catastrophically on multi-hop questions after edits | MQuAKE (arXiv:2305.14795)[^18] | A | Strong | High | ACL 2023 peer-reviewed |
| LongMemEval: 30%–60% performance drop for long-context LLMs | LongMemEval (arXiv:2410.10813)[^13] | B | Strong | High | arXiv preprint with code/data; multiple commercial systems tested |
| MemoryAgentBench: no existing benchmark covers all four competencies | MemoryAgentBench (arXiv:2507.05257; ICLR 2026)[^20] | A | Strong | High | ICLR 2026 accepted paper |
| BEAM at 10M: RAG baseline scores 24.9%, LIGHT 26.6% | Hindsight blog citing BEAM paper[^6] | C/B | Moderate | Medium-High | Vendor blog citing paper; paper is arXiv:2510.27246[^4] |
| Agentic memory benchmarks are underscaled and often saturated | DAIR-AI summary of agentic memory survey (LinkedIn)[^28] | D | Weak | Medium | Secondary summary; references arXiv:2602.19320 which could not be directly inspected |
| ROME model collapse with CounterFact; not with zsRE | Rebuild ROME paper (arXiv:2403.07175)[^59] | B | Strong | High | arXiv preprint with empirical validation |
| EvolMem: no LLM consistently outperforms on all memory dimensions | EvolMem (arXiv:2601.03543)[^52] | B | Strong | High | arXiv preprint; 7 LLMs + 4 agent systems tested |
| LifelongAgentBench: conventional experience replay is limited | LifelongAgentBench (arXiv:2505.11942)[^9] | B | Strong | High | arXiv preprint with code |
| HELMET: synthetic tasks like NIAH are not good predictors of downstream performance | HELMET (arXiv:2410.02694; ICLR 2025)[^1] | A | Strong | High | ICLR 2025 peer-reviewed; 59 models |

***

## 12. Unknowns and Further Research

### Benchmarks That Could Not Be Fully Verified

- **MemPrivacy-Bench** (arXiv:2605.09530) — newly submitted (May 2026); no peer review yet; claims 200 users, 52K privacy instances; worth tracking but not included in primary analysis.[^76]
- **Locomo-Plus** (arXiv:2602.10715) — referenced as "beyond-factual cognitive memory evaluation"; paper could not be fully inspected; potential extension of LoCoMo for higher-order reasoning.
- **MemoryBench** (arXiv:2510.17281) — submitted to ICLR 2026 but withdrawn/rejected based on OpenReview status; paper and code partially available; evaluation methodology needs closer inspection.[^56][^55]

### Unavailable or Unclear Datasets

- **SiliconFriend real-user dialogues** — MemoryBank evaluation includes "qualitative analysis with real-world user dialogs" but these are not released publicly. The quantitative evaluation uses ChatGPT-simulated users.[^64]
- **GAIA test answers** — Test answers for 300 questions are withheld for the leaderboard; methodology for leaderboard submission involves API calls that could change over time.[^27]
- **τ-bench task fixes** — τ³-bench (tau3-bench) notes "75+ task fixes" for the benchmark, suggesting the original τ-bench had quality issues not fully characterized in the primary paper.[^71]

### Papers Needing Closer Inspection

- **arXiv:2602.19320** (survey on agentic memory systems cited by DAIR-AI) — could not be directly inspected; cited for the "benchmark saturation" finding; requires primary source verification.[^28]
- **arXiv:2601.20352** (AMA: Adaptive Memory via Multi-Agent Collaboration) — surface-level search hit; not inspected for benchmark relevance.

### Missing Leaderboards

- BEAM has a leaderboard at `agentmemorybenchmark.ai` but the site was accessed only through vendor blog references; independent verification of the leaderboard methodology is pending.[^6]
- MemoryArena has a HuggingFace dataset but a formal leaderboard was not identified at the time of writing.

### Likely Stale Results

- **LoCoMo** results from the 2024 paper should be treated as stale for any model with >128K context window. The 10-conversation dataset is effectively solvable by context stuffing.
- **LongBench** baselines from 2023 using GPT-3.5-Turbo-16k as the "commercial model" leader are entirely outdated given 1M+ context windows.
- **NIAH** perfect scores by Claude 3 Opus (2024) are now replicated by virtually all frontier models, confirming saturation.

### Open Research Questions

1. Does MemoryArena generalize across agentic domains beyond the four tested (web navigation, preference-constrained planning, progressive search, sequential reasoning)?
2. What is the correct evaluation protocol for memory provenance — and can it be automated without human annotation?
3. Can synthetic-user benchmarks (PERSONAMEM, EvolMem) be validated against real-user interaction traces, and if so, how large is the distribution gap?
4. What is the threshold context length at which LongMemEval becomes fully saturated for a given model generation? Is this a function of context window size alone, or also of attention quality?
5. Is there a verified benchmark testing negative personalization effects (harmful memory surfacing leading to discriminatory or harmful outputs)? None was found in this review.

---

## References

1. [HELMET: How to Evaluate Long-Context Language Models Effectively and Thoroughly](https://arxiv.org/abs/2410.02694v3) - Many benchmarks exist for evaluating long-context language models (LCLMs), yet developers often rely...

2. [RULER: What's the Real Context Size of Your Long-Context Language Models?](https://www.arxiv.org/abs/2404.06654) - The needle-in-a-haystack (NIAH) test, which examines the ability to retrieve a piece of information ...

3. [HELMET: How to Evaluate Long-Context Language Models ... - arXiv](https://arxiv.org/abs/2410.02694) - Many benchmarks exist for evaluating long-context language models (LCLMs), yet developers often rely...

4. [Benchmarking and Enhancing Long-Term Memory in LLMs](https://huggingface.co/papers/2510.27246) - A new benchmark and memory framework improve long-term memory and reasoning in large language models...

5. [Benchmarking and Enhancing Long-Term Memory in LLMs](https://openreview.net/forum?id=y59hf5lrMn) - TL;DR: We introduce BEAM, a multi-domain benchmark of long (100K–10M token) conversations with compr...

6. [Hindsight Is #1 on BEAM — the Benchmark That Tests Memory at 10 ...](https://hindsight.vectorize.io/blog/2026/04/02/beam-sota) - Hindsight is SOTA on BEAM, the benchmark that tests memory at 10 million tokens, where context stuff...

7. [[2602.16313] MemoryArena: Benchmarking Agent Memory in ... - arXiv](https://arxiv.org/abs/2602.16313) - Existing evaluations of agents with memory typically assess memorization and action in isolation. On...

8. [MemoryArena: Benchmarking Agent Memory in Interdependent ...](https://memoryarena.github.io) - This dataset contains structured multi-session agentic tasks with questions (list), answers (list), ...

9. [LifelongAgentBench: Evaluating LLM Agents as Lifelong Learners](https://www.arxiv.org/abs/2505.11942) - Lifelong learning is essential for intelligent agents operating in dynamic environments. Current lar...

10. [LifelongAgentBench: Evaluating LLM Agents as Lifelong Learners](https://arxiv.org/abs/2505.11942) - Lifelong learning is essential for intelligent agents operating in dynamic environments. Current lar...

11. [Benchmarking Chat Assistants on Long-Term Interactive Memory](https://huggingface.co/papers/2410.10813) - Join the discussion on this paper page

12. [LongMemEval - Di Wu](https://xiaowu0162.github.io/long-mem-eval/) - We meticulously create 500 questions of seven types (see examples above) to test five long-term memo...

13. [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813v1) - Recent large language model (LLM)-driven chat assistant systems have integrated memory components to...

14. [Do LLMs Recognize Your Preferences? Evaluating Personalized...](https://openreview.net/forum?id=QWunLKbBGF) - Large Language Models (LLMs) are increasingly deployed as chatbots, yet their ability to personalize...

15. [[2502.09597] Do LLMs Recognize Your Preferences? Evaluating ...](https://ar5iv.labs.arxiv.org/html/2502.09597) - Large Language Models (LLMs) are increasingly used as chatbots, yet their ability to personalize res...

16. [Know Me, Respond to Me: Benchmarking LLMs for Dynamic User...](https://openreview.net/forum?id=6ox8XZGOqP) - This paper introduces PERSONAMEM, a novel benchmark for evaluating how well large language models (L...

17. [Know Me, Respond to Me: Benchmarking LLMs for Dynamic User ...](https://arxiv.org/abs/2504.14225) - In this work, we introduce the PERSONAMEM benchmark. PERSONAMEM features curated user profiles with ...

18. [MQuAKE: Assessing Knowledge Editing in Language Models via ...](https://arxiv.org/abs/2305.14795) - The information stored in large language models (LLMs) falls out of date quickly, and retraining fro...

19. [MQuAKE: Assessing Knowledge Editing in Language Models via Multi-Hop Questions](https://arxiv.org/html/2305.14795v3)

20. [Evaluating Memory in LLM Agents via Incremental Multi-Turn ... - arXiv](https://arxiv.org/abs/2507.05257) - We introduce MemoryAgentBench, a new benchmark specifically designed for memory agents. Our benchmar...

21. [️ MemoryAgentBench: Evaluating Memory in LLM Agents ... - GitHub](https://github.com/HUST-AI-HYZ/MemoryAgentBench) - Open source code for ICLR 2026 Paper: Evaluating Memory in LLM Agents via Incremental Multi-Turn Int...

22. [000](https://openreview.net/pdf?id=YnNIp38v1M)

23. [[2511.14937] CIMemories: A Compositional Benchmark for ...](https://www.arxiv.org/abs/2511.14937) - Large Language Models (LLMs) increasingly use persistent memory from past interactions to enhance pe...

24. [WebArena benchmark | Web navigation agent evaluation | Steel.dev](https://leaderboard.steel.dev/registry/benchmarks/webarena) - WebArena is a self-hosted web navigation benchmark. Compare its evaluation method, task count, top m...

25. [GitHub - SWE-bench/SWE-bench: SWE-bench [Multimodal]: Can Language Models Resolve Real-world Github Issues?](https://github.com/swe-bench/SWE-bench) - SWE-bench: Can Language Models Resolve Real-world Github Issues? - SWE-bench/SWE-bench

26. [tau-bench: A benchmark for tool-agent-user interaction - VerifyWise](https://verifywise.ai/ai-governance-library/agentic-evaluation/agent-tau-bench-repo) - Sierra Research's open benchmark for tool-using agents, simulating airline and retail customer-servi...

27. [GAIA:A Benchmark for General AI Assistants - ar5iv - arXiv](https://ar5iv.labs.arxiv.org/html/2311.12983) - We introduce GAIA, a benchmark for General AI Assistants that, if solved, would represent a mileston...

28. [Agentic Memory Systems Survey: Limitations and Future Directions](https://www.linkedin.com/posts/dair-ai_important-survey-on-agentic-memory-systems-activity-7432081127038889985-6ZCz) - The authors introduce a taxonomy based on four core memory structures and then systematically analyz...

29. [LLMTest_NeedleInAHaystack/README.md at main · gkamradt/LLMTest_NeedleInAHaystack](https://github.com/gkamradt/LLMTest_NeedleInAHaystack/blob/main/README.md) - Doing simple retrieval from LLM models at various context lengths to measure accuracy - gkamradt/LLM...

30. [Plivo sur LinkedIn : Needle in a Haystack LLM Benchmark](https://www.linkedin.com/posts/plivo-inc_needle-in-a-haystack-llm-benchmark-activity-7243611000057319424-NmD5) - What is the 'Needle in a Haystack' benchmark for LLMs? Initially popularized by Gregory Kamradt in 2...

31. [\faRulerRuler: What’s the Real Context Size of Your Long-Context Language Models?](https://arxiv.org/html/2404.06654v3)

32. [LongBench/LongBench/README.md at main · THUDM/LongBench](https://github.com/THUDM/LongBench/blob/main/LongBench/README.md) - LongBench v2 and LongBench (ACL 25'&24'). Contribute to THUDM/LongBench development by creating an a...

33. [A Bilingual, Multitask Benchmark for Long Context Understanding](https://huggingface.co/papers/2308.14508) - Join the discussion on this paper page

34. [InfiniteBench/README.md at main · OpenBMB/InfiniteBench](https://github.com/OpenBMB/InfiniteBench/blob/main/README.md) - Codes for the paper "∞Bench: Extending Long Context Evaluation Beyond 100K Tokens": https://arxiv.or...

35. [∞Bench: Extending Long Context Evaluation Beyond 100K Tokens](https://aclanthology.org/2024.acl-long.814/) - Xinrong Zhang, Yingfa Chen, Shengding Hu, Zihang Xu, Junhao Chen, Moo Hao, Xu Han, Zhen Thai, Shuo W...

36. [L-Eval: Instituting Standardized Evaluation for Long Context...](https://openreview.net/forum?id=eUAr4HwU0X) - Recently, there has been growing interest in extending the context length of large language models (...

37. [L-Eval: Instituting Standardized Evaluation for Long Context Language Models](https://arxiv.org/html/2307.11088v3)

38. [BAMBOO: A Comprehensive Benchmark for Evaluating Long Text ...](https://arxiv.org/html/2309.13345v3) - It consists of 10 datasets from 5 different long text understanding tasks, ie, question answering, h...

39. [GitHub - RUCAIBox/BAMBOO](https://github.com/RUCAIBox/BAMBOO) - This repository contains the evaluation code, prompt, and datasets for the paper BAMBOO: A Comprehen...

40. [Found in the Middle: Calibrating Positional Attention Bias Improves ...](https://snorkel.ai/research-paper/found-in-the-middle-calibrating-positional-attention-bias-improves-long-context-utilization/) - In doing so, we establish a connection between lost-in-the-middle to LLMs' intrinsic attention bias:...

41. [[PDF] Lost in the Middle: How Language Models Use Long Contexts](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.tacl2023.pdf) - While recent language models have the abil- ity to take long contexts as input, relatively little is...

42. [NoLima | PDF | Cognitive Science | Learning - Scribd](https://www.scribd.com/document/905017391/NoLima) - The document introduces N O L I M A, a benchmark designed to evaluate large language models' (LLMs) ...

43. [[PDF] NoLiMa: Long-Context Evaluation Beyond Literal Matching](https://openreview.net/pdf?id=0OshX1hiSa)

44. [NoLiMa: Long-Context Evaluation Beyond Literal Matching - arXiv](https://arxiv.org/html/2502.05167v1)

45. [Sequential-NIAH: A Needle-In-A-Haystack Benchmark for Extracting ...](https://aclanthology.org/2025.emnlp-main.1497/) - Yifei Yu, Qian-Wen Zhang, Lingfeng Qiao, Di Yin, Fang Li, Jie Wang, Chen Zeng Xi, Suncong Zheng, Xia...

46. [[PDF] Sequential-NIAH: A Needle-In-A-Haystack Benchmark for Extracting ...](https://aclanthology.org/2025.emnlp-main.1497.pdf) - LLMs' Limitations on Sequential-NIAH: Experimental results indicate that all current. LLMs have sign...

47. [Evaluating Very Long-Term Conversational Memory of LLM Agents](https://huggingface.co/papers/2402.17753) - Join the discussion on this paper page

48. [Evaluating Very Long-Term Conversational Memory of LLM Agents](https://arxiv.org/html/2402.17753v1)

49. [GitHub - snap-research/locomo](https://github.com/snap-research/locomo) - Contribute to snap-research/locomo development by creating an account on GitHub.

50. [Evaluating Memory in LLM Agents via Incremental Multi-Turn ... - Liner](https://liner.com/review/evaluating-memory-in-llm-agents-via-incremental-multiturn-interactions) - Regarding this ICLR 2026 paper, this review summarizes MemoryAgentBench, a new benchmark evaluating ...

51. [Benchmarking Agent Memory in Interdependent Multi-Session ...](https://arxiv.org/html/2602.16313v1)

52. [EvolMem: A Cognitive-Driven Benchmark for Multi-Session Dialogue Memory](https://arxiv.org/abs/2601.03543) - Despite recent advances in understanding and leveraging long-range conversational memory, existing b...

53. [[論文評述] EvolMem: A Cognitive-Driven Benchmark for ...](https://www.themoonlight.io/tw/review/evolmem-a-cognitive-driven-benchmark-for-multi-session-dialogue-memory) - The paper introduces EvolMem, a novel cognitive-driven benchmark designed for comprehensively assess...

54. [EvolMem: A Cognitive-Driven Benchmark for Multi-Session Dialogue Memory](https://www.arxiv.org/abs/2601.03543) - Despite recent advances in understanding and leveraging long-range conversational memory, existing b...

55. [A Benchmark for Memory and Continual Learning in LLM Systems](https://arxiv.org/abs/2510.17281) - Abstract page for arXiv paper 2510.17281: MemoryBench: A Benchmark for Memory and Continual Learning...

56. [A Benchmark for Memory and Continual Learning in LLM Systems](https://openreview.net/forum?id=wU4Tjlzg3h) - The paper proposes MemoryBench, a benchmark designed to evaluate memory and continual learning in LL...

57. [GitHub - bowen-upenn/PersonaMem: [COLM 2025] Know Me ...](https://github.com/bowen-upenn/PersonaMem) - A new personalization benchmark to assess how well language models can infer evolving user profiles ...

58. [Locating and Editing Factual Knowledge in GPT](https://arxiv.org/abs/2202.05262v1) - We investigate the mechanisms underlying factual knowledge recall in autoregressive transformer lang...

59. [Rebuilding ROME : Resolving Model Collapse during Sequential Model Editing](https://arxiv.org/html/2403.07175v1)

60. [TRACE: A Comprehensive Benchmark for Continual Learning in ...](https://openreview.net/forum?id=xelrLobW0n) - Aligned large language models (LLMs) demonstrate exceptional capabilities in task-solving, following...

61. [TRACE: A Comprehensive Benchmark for Continual Learning in Large Language Models](https://ar5iv.labs.arxiv.org/html/2310.06762) - Aligned large language models (LLMs) demonstrate exceptional capabilities in task-solving, following...

62. [StreamingQA: A Benchmark for Adaptation to New Knowledge over ...](https://proceedings.mlr.press/v162/liska22a.html) - Knowledge and language understanding of models evaluated through question answering (QA) has been us...

63. [StreamingQA: A Benchmark for Adaptation to New Knowledge over ...](https://arxiv.org/abs/2205.11388) - Abstract page for arXiv paper 2205.11388: StreamingQA: A Benchmark for Adaptation to New Knowledge o...

64. [Enhancing Large Language Models with Long-Term Memory](https://huggingface.co/papers/2305.10250) - Join the discussion on this paper page

65. [Enhancing Large Language Models with Long-Term Memory - arXiv](https://arxiv.org/abs/2305.10250) - We exemplify application of MemoryBank through the creation of an LLM-based chatbot named SiliconFri...

66. [AgentBench: Evaluating LLMs as Agents](https://ar5iv.labs.arxiv.org/html/2308.03688v1) - Large Language Models (LLMs) are becoming increasingly smart and autonomous, targeting real-world pr...

67. [Paper](https://jykoh.com/vwa) - Project webpage for the VisualWebArena paper.

68. [Evaluating Multimodal Agents on Realistic Visual Web Tasks](https://aclanthology.org/2024.acl-long.50/) - Jing Yu Koh, Robert Lo, Lawrence Jang, Vikram Duvvur, Ming Lim, Po-Yu Huang, Graham Neubig, Shuyan Z...

69. [OSWorld Leaderboard - Codesota](https://www.codesota.com/benchmark/osworld) - OSWorld Leaderboard (2026): Agent S3 w/ bBoN leads with 63.5%. Compare 27 models on Success Rate.

70. [SWE-Bench+: Enhanced Coding Benchmark for LLMs](https://ui.adsabs.harvard.edu/abs/2024arXiv241006992A/abstract) - Large Language Models (LLMs) in Software Engineering (SE) can offer assistance for coding. To facili...

71. [sierra-research/tau2-bench: τ-Bench: A Benchmark for Tool-Agent ...](https://github.com/sierra-research/tau2-bench) - A set of tools that the agent can use; A set of tasks to evaluate the agent's performance; Optionall...

72. [A Benchmark for Evaluating LLMs on Temporal Reasoning](https://arxiv.org/abs/2406.09170) - Large language models (LLMs) have showcased remarkable reasoning capabilities, yet they remain susce...

73. [Test of Time: A Benchmark for Evaluating LLMs on Temporal Reasoning](https://arxiv.org/html/2406.09170)

74. [[2512.13564] Memory in the Age of AI Agents - arXiv](https://arxiv.org/abs/2512.13564) - To support practical development, we compile a comprehensive summary of memory benchmarks and open-s...

75. [A 360 review of AI agent benchmarks - IBM Research](https://research.ibm.com/blog/AI-agent-benchmarks) - Researchers at Hebrew University, IBM, and Yale summarize the latest in AI agent benchmarking and su...

76. [MemPrivacy: Privacy-Preserving Personalized Memory ...](https://papers.cool/arxiv/2605.09530) - As LLM-powered agents are increasingly deployed in edge-cloud environments, personalized memory has ...

