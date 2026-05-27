\## Brutal verdict



The breakout project is \*\*not an agent memory database\*\*. It is a \*\*memory compiler/runtime that converts past agent trajectories into verified, typed, temporally scoped, causally useful experience\*\* that measurably changes future behavior.



The primitive I would build is:



> \*\*Causal Experience Memory\*\*: an open-source system that ingests raw agent traces, extracts evidence-backed “experience atoms,” promotes only verified causal lessons into reusable memory, and evaluates memory by the marginal improvement it creates in future long-horizon tasks.



This is materially different from vector recall, chat summaries, temporal graph RAG, MCP memory, or “universal memory.” Those store or retrieve context. The harder unsolved problem is: \*\*what should an agent learn from experience, when should it trust that learning, and how do we prove it helped?\*\*



The strongest wedge is not “remembers user preferences.” It is:



> “After 100 failed and successful trajectories in a specialized environment, the agent becomes an experienced operator: it knows the hidden gotchas, workflows, state transitions, affordances, and failure modes — with evidence, timestamps, uncertainty, and tests.”



That aligns with where the frontier is moving. LongMemEval-V2 frames high-quality memory as making an agent an “experienced colleague” in specialized web environments; it uses 451 manually curated questions over up to 500 trajectories and 115M tokens, and reports that a coding-agent-based memory baseline beats a strong RAG baseline but still leaves large room for improvement. (\[arXiv]\[1]) MemoryArena explicitly shows the gap between conversational recall benchmarks and multi-session agentic tasks where memory must guide later action. (\[Stanford Digital Economy Lab]\[2]) AMA-Bench reports that existing memory systems can underperform long-context baselines on long-horizon agentic tasks, largely because lossy compression and similarity retrieval are misaligned with agent memory. (\[arXiv]\[3])



The project should \*\*not\*\* compete as “better memory storage.” It should sit above any storage backend and own the hard layer: \*\*trajectory → trusted experience → future action advantage\*\*.



\---



\## Frontier map



\### 1. What is already mature or crowded



The lower layers of agent memory are now infrastructure, not invention.



| Layer                    |                                             Current state | Verdict                                   |

| ------------------------ | --------------------------------------------------------: | ----------------------------------------- |

| Raw persistence          |       Store messages, traces, tool calls, files, profiles | Commodity                                 |

| Vector recall            |                     Embed chunks, retrieve top-k memories | Commodity                                 |

| Hybrid retrieval         |                       Vector + keyword + metadata filters | Commodity                                 |

| Chat summaries           |          Session summaries, rolling summaries, user facts | Commodity                                 |

| Temporal graph memory    | Entity-relation-time graphs, validity windows, provenance | Useful but crowded                        |

| MCP memory servers       |         Standardized access to local/remote memory stores | Integration layer, not research primitive |

| Long-context stuffing    |                               Put more history in context | Baseline, not memory                      |

| Basic reflection buffers |          “What I learned” text appended to future prompts | Weak unless verified                      |

| Agent-framework glue     |               LangGraph/CrewAI/AutoGen/Letta integrations | DX, not invention                         |



Open-source evidence is strong: Graphiti already provides temporal context graphs with provenance and validity windows; Mem0 positions itself as a universal memory layer; Letta/MemGPT provides stateful agents with memory blocks; Qdrant’s MCP server exposes vector memory via `store` and `find`; Anthropic’s MCP exists to standardize model access to external data/tools. (\[GitHub]\[4])



Vendor claims are also saturating the space. Supermemory, for example, publicly claims SOTA LongMemEval results using chunk ingestion, relational versioning, temporal grounding, and hybrid search. Treat that as vendor evidence, not independent proof, but it shows that “better LongMemEval RAG memory” is becoming a scoreboard race. (\[Supermemory]\[5])



\### 2. What is technically deep



The deep problems are not storage problems. They are \*\*policy, epistemology, causality, lifecycle, and evaluation\*\* problems.



| Bottleneck                       | Why it is deep                                                                                                            |

| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |

| Memory write policy              | The agent must decide what is worth storing, updating, deleting, abstracting, or ignoring. Heuristics are brittle.        |

| Experience-to-skill abstraction  | Raw traces are too specific; summaries are too vague. The hard layer is extracting reusable procedures and failure modes. |

| Causal retrieval                 | Similarity retrieval finds related text. Agents need memories that affect the next action.                                |

| Provenance and source monitoring | Agents confuse user claims, assistant speculation, tool outputs, environment observations, and derived conclusions.       |

| Temporal contradiction           | Facts change. Preferences expire. Old observations remain historically true but operationally invalid.                    |

| Trustworthy reflection           | Self-reflection can help, but unverified “lessons” become hallucinated policy.                                            |

| Learned forgetting               | Forgetting is not deletion. It is risk/utility-aware demotion, invalidation, expiry, or isolation.                        |

| Multi-agent consistency          | Shared memory creates semantic cache-coherence problems: who saw what, who may use it, which version is authoritative?    |

| Evaluation                       | Chat recall accuracy does not predict long-horizon agent usefulness.                                                      |



Benchmark evidence increasingly supports this distinction. LongMemEval evaluates information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention in chat-assistant memory. (\[arXiv]\[6]) LoCoMo evaluates long-term conversational memory through QA, event summarization, and multimodal dialogue over long dialogues. (\[Snap Research]\[7]) MemoryAgentBench argues that memory agents need accurate retrieval, test-time learning, long-range understanding, and selective forgetting. (\[arXiv]\[8]) But newer agentic benchmarks shift from “can you answer from history?” to “can past experience improve future action?” — especially MemoryArena, AMA-Bench, Mem2ActBench, and LongMemEval-V2. (\[Stanford Digital Economy Lab]\[2])



\### 3. Current research signals worth taking seriously



There are four live research directions that matter.



First, \*\*workflow and experience memory\*\* is proving useful. Agent Workflow Memory induces reusable workflows from past web-agent tasks and reports large relative gains on Mind2Web and WebArena. (\[OpenReview]\[9]) ReasoningBank distills strategies from both successes and failures, explicitly criticizing raw trajectory storage and success-only workflow memory as insufficient. (\[Google Research]\[10])



Second, \*\*learned memory management\*\* is emerging. Memory-R1 trains agents to perform structured memory operations such as add, update, delete, and no-op; Mem-α trains memory construction policies through interaction and downstream QA reward. These are promising, but they are not yet a general open-source memory foundation for real deployed agents. (\[arXiv]\[11])



Third, \*\*temporal and symbolic reasoning\*\* is necessary. TReMu shows that time-aware memorization plus neuro-symbolic temporal reasoning can substantially improve temporal reasoning in multi-session dialogues, which indicates that plain retrieval is insufficient for time-scoped memory. (\[ACL Anthology]\[12])



Fourth, \*\*provenance typing is becoming unavoidable\*\*. Recent MemIR work names “provenance-role collapse” as a failure mode where flat text memories cause source-monitoring errors, and proposes typed memory atoms that separate raw evidence, retrieval cues, and truth-bearing claims. (\[arXiv]\[13])



My inference: the field is converging on the same answer from different directions. The next important primitive is not vector memory, graph memory, or chat memory. It is \*\*typed, verified, action-relevant experience memory\*\*.



\---



\## Dead-end ranking



This ranking is about \*\*bottlenecks that block real agents\*\*, not superficial feature gaps.



Scores: 5 = high. “OSS feasibility” means an open-source project can plausibly make progress without training frontier models.



| Rank | Dead end / bottleneck                                     | Importance | Unsolved | OSS feasibility | Attention if solved | Verdict                                                                                                  |

| ---: | --------------------------------------------------------- | ---------: | -------: | --------------: | ------------------: | -------------------------------------------------------------------------------------------------------- |

|    1 | \*\*Memory does not reliably improve future task success\*\*  |          5 |        5 |               4 |                   5 | The central dead end. Most systems prove recall, not behavioral advantage.                               |

|    2 | \*\*Experience abstraction is unverified\*\*                  |          5 |        5 |               4 |                   5 | Agents write “lessons,” but do not know when lessons generalize.                                         |

|    3 | \*\*Similarity retrieval is not causal retrieval\*\*          |          5 |        5 |               4 |                   5 | The relevant memory is often not semantically closest; it is the one that changes the next action.       |

|    4 | \*\*Memory write/update/delete policy is heuristic\*\*        |          5 |        5 |               3 |                   5 | Current systems mostly prompt the model to decide. RL papers show direction, not solved product.         |

|    5 | \*\*Provenance-role collapse\*\*                              |          5 |        4 |               5 |                   4 | Flat memories blur observed facts, user claims, assistant guesses, and derived beliefs.                  |

|    6 | \*\*Temporal contradiction and validity are under-modeled\*\* |          4 |        4 |               5 |                   4 | Temporal graphs help, but operational validity, expiry, exceptions, and changed preferences remain hard. |

|    7 | \*\*Benchmarks reward recall theater\*\*                      |          4 |        5 |               5 |                   4 | LongMemEval-style scores are useful but insufficient; agentic tasks expose different failures.           |

|    8 | \*\*False reflection contaminates future behavior\*\*         |          5 |        4 |               4 |                   4 | Reflection without external verification becomes policy hallucination.                                   |

|    9 | \*\*Multi-agent memory consistency\*\*                        |          4 |        5 |               3 |                   4 | Shared semantic memory has distributed-systems problems: visibility, authority, invalidation, leakage.   |

|   10 | \*\*Memory cost/latency grows faster than utility\*\*         |          4 |        3 |               5 |                   3 | Serious systems must track token, query, consolidation, and maintenance cost.                            |



The top three are the project-defining ones. If you solve only “better recall,” you are in a commodity lane. If you solve \*\*future action advantage from verified experience\*\*, serious agent builders will pay attention.



\---



\## Breakthrough candidates



\### Candidate 1: Causal Experience Memory



\*\*Core idea:\*\* Store not just what happened, but what past experience implies for future action. Each memory unit links state → action/strategy → outcome → evidence → preconditions → exceptions → confidence.



A memory entry should look less like:



> “The user used ServiceNow before.”



And more like:



> “In this ServiceNow instance, assignment fails unless the group field is selected before the assignee field. Evidence: traces 14, 21, 33. Scope: incident workflow. Confidence: high. Exceptions: not observed for change requests. Verification probe: reproduce on held-out incident form.”



\*\*What current systems fail to do:\*\* Vector RAG retrieves similar traces. Graph memory retrieves related entities. Summaries recall facts. But agents need \*\*action priors\*\*: “do this, avoid that, check this condition first.”



\*\*Why it could work:\*\* AWM and ReasoningBank suggest that procedural and strategic memories can improve web/software agents; LongMemEval-V2 explicitly frames memory as environment-specific experience, including workflows and gotchas. (\[OpenReview]\[9])



\*\*Why it might fail:\*\* Causal extraction from messy traces may hallucinate. The system may overfit environment-specific quirks. Memory may ossify bad strategies after UI changes.



\*\*Smallest prototype:\*\* Ingest BrowserGym/WebArena/WorkArena-style trajectories. Extract “experience cards” for workflows, gotchas, dynamic state, and failure modes. Retrieve cards before held-out tasks. Use an existing vector/graph store underneath, but make the novelty the causal compiler and action adapter.



\*\*Falsifying eval:\*\* If simple hybrid RAG over raw traces or a hand-written runbook performs within 5–10% on held-out workflow/gotcha tasks at comparable latency/token cost, the primitive is not strong enough.



\---



\### Candidate 2: Typed Memory IR / Provenance Firewall



\*\*Core idea:\*\* Introduce a memory intermediate representation where every memory atom is typed by epistemic role:



\* raw observation;

\* user claim;

\* assistant hypothesis;

\* tool output;

\* environment state;

\* derived claim;

\* preference;

\* policy;

\* skill;

\* failed attempt;

\* contradiction;

\* expiry/invalidation event.



Only supported claim atoms can be used as factual memory. Everything else must remain scoped as evidence, cue, or hypothesis.



\*\*What current systems fail to do:\*\* Flat text memories cause agents to confuse source roles. A model may treat its own previous speculation as a fact, or treat outdated user preference as current. MemIR’s “provenance-role collapse” framing is exactly the failure to avoid. (\[arXiv]\[13])



\*\*Why it could work:\*\* It turns trust into architecture rather than prompt instruction. It also composes well with temporal graphs, retrieval, audits, and safety controls.



\*\*Why it might fail:\*\* Typed extraction can be noisy. Developers may reject the complexity unless the demo shows clear reductions in harmful memory use.



\*\*Smallest prototype:\*\* A library that compiles logs/traces into typed atoms, returns only evidence-bound claims to the agent, and refuses unsupported memories. Start with text/tool traces before multimodal traces.



\*\*Falsifying eval:\*\* Inject false memories, stale summaries, assistant speculation, and conflicting user claims. If the typed system does not reduce unsupported claims and stale-memory errors versus flat memory, kill or narrow it.



\---



\### Candidate 3: Verifiable Sleep-Time Consolidation



\*\*Core idea:\*\* Do not promote memories immediately. After task streams, run an offline consolidation phase that generates candidate skills/runbooks/lessons, then tests them through probes, replays, unit tasks, or sandbox checks before committing them.



This is “CI/CD for memory.”



\*\*What current systems fail to do:\*\* Reflection buffers and summaries write plausible lessons, but rarely test whether the lesson is true or useful. ReasoningBank moves toward success/failure strategy distillation, but an open-source system with explicit promotion tests would be a stronger foundation. (\[Google Research]\[10])



\*\*Why it could work:\*\* Many agent domains have verifiable signals: browser task completion, code tests, API responses, schema validation, tool outputs, trajectory replay.



\*\*Why it might fail:\*\* Probe generation may be biased or too expensive. The system may verify easy proxy tasks but fail on real future tasks.



\*\*Smallest prototype:\*\* A web or coding agent that runs a nightly consolidation job: extract candidate lessons from the day’s traces, generate 3–5 verification probes per lesson, promote only lessons that pass, demote lessons that later cause failures.



\*\*Falsifying eval:\*\* Verification score must predict held-out memory usefulness. If promoted memories do not outperform unverified memories, the consolidation protocol is theater.



\---



\### Candidate 4: Marginal Memory Utility Benchmark



\*\*Core idea:\*\* Build a benchmark harness that measures the \*\*causal contribution of memory\*\* rather than answer accuracy alone.



Every evaluation should compare:



\* no memory;

\* full context;

\* raw RAG;

\* graph memory;

\* candidate memory;

\* shuffled memory;

\* stale memory;

\* poisoned memory;

\* oracle memory.



Metrics should include task success delta, memory-use precision, evidence support, stale-memory harm, latency, token cost, and whether retrieved memory changed the decisive action.



\*\*What current systems fail to do:\*\* Benchmarks often conflate model strength, retriever quality, prompt engineering, and memory quality. Anatomy of Agentic Memory argues that current empirical foundations are fragile because benchmarks can be underscaled, metrics misaligned, backbone-dependent, and cost-blind. (\[arXiv]\[14])



\*\*Why it could work:\*\* The field needs an evaluation protocol that serious builders trust. If the benchmark exposes failures in popular systems, attention follows.



\*\*Why it might fail:\*\* Benchmarks are hard to maintain. If it is too academic, builders ignore it. If it is too product-specific, researchers ignore it.



\*\*Smallest prototype:\*\* A wrapper around LongMemEval-V2, MemoryArena, and Mem2ActBench with standardized memory ablations and harm tests.



\*\*Falsifying eval:\*\* If results are unstable across models, or if the benchmark rewards prompt hacks rather than memory quality, it is not a useful foundation.



\---



\### Candidate 5: Semantic Memory Consistency Protocol for Multi-Agent Systems



\*\*Core idea:\*\* Treat multi-agent memory like distributed systems memory: local caches, shared memory, authority levels, invalidation, access control, versioned claims, role-specific views, and consistency contracts.



\*\*What current systems fail to do:\*\* Multi-agent systems often share summaries or logs without clear semantics. That creates leakage, stale beliefs, duplicated work, and inconsistent plans.



\*\*Why it could work:\*\* A 2026 position paper explicitly frames multi-agent memory as a computer-architecture problem and identifies memory consistency, cache sharing, and structured access control as critical gaps. LEGOMem also shows that memory placement matters: orchestrator memory helps task decomposition/delegation, while fine-grained agent memory improves execution. (\[arXiv]\[15])



\*\*Why it might fail:\*\* This can become protocol overbuilding before there is enough demonstrated capability.



\*\*Smallest prototype:\*\* A multi-agent workflow system where planner, browser agent, spreadsheet agent, and email agent use role-scoped memory. Evaluate inconsistent-memory tasks where one agent sees stale or private information.



\*\*Falsifying eval:\*\* If consistency controls add complexity without reducing task failures or leakage, do not lead with this.



\---



\## Recommended Plan 1



\### Invention thesis



Build \*\*Causal Experience Memory\*\*, an open-source memory system that turns agent trajectories into \*\*verified, evidence-backed, action-relevant experience\*\*.



The thesis:



> Agent memory should not be judged by what it can recall. It should be judged by how much it improves future decisions under changing, partially observed environments.



\### Architecture primitive



The core object is an \*\*Experience Atom\*\*.



A serious first schema:



```text

ExperienceAtom

\- id

\- domain\_scope

\- task\_family

\- source\_trace\_ids

\- source\_spans / screenshots / tool outputs

\- epistemic\_type: observation | user\_claim | tool\_output | hypothesis | derived\_claim | skill | failure\_mode

\- temporal\_scope: observed\_at | valid\_from | valid\_until | superseded\_by

\- state\_preconditions

\- action\_or\_strategy

\- observed\_outcome

\- causal\_claim

\- confidence

\- support\_count

\- contradiction\_links

\- exception\_boundary

\- retrieval\_cues

\- recommended\_use

\- verification\_probe

\- promotion\_status: candidate | verified | deprecated | quarantined

```



A higher-level memory object is an \*\*Experience Card\*\*:



```text

ExperienceCard

\- title: “Assignee field requires group selection first”

\- use\_when: “Incident assignment in ServiceNow-like UI”

\- do: “Select assignment group before assignee”

\- do\_not: “Do not search assignee before group is set”

\- evidence: trace links and observation spans

\- tested\_by: probe ids

\- confidence: high / medium / low

\- known\_exceptions

\- last\_validated\_at

```



This is the product primitive. Not “memory chunk.” Not “node.” Not “summary.” Not “embedding.” It is \*\*a tested unit of operational experience\*\*.



\### Runtime architecture



Use five layers:



1\. \*\*Raw trace ledger\*\*

&#x20;  Append-only storage of observations, actions, tool calls, screenshots, DOM snapshots, errors, rewards, and final outcomes. This layer is untrusted evidence.



2\. \*\*Typed memory compiler\*\*

&#x20;  Converts traces into typed atoms: observations, actions, outcomes, tool facts, user claims, hypotheses, failures, and candidate causal claims.



3\. \*\*Causal consolidation engine\*\*

&#x20;  Links repeated patterns across traces, identifies success/failure contrasts, extracts preconditions and exceptions, and generates candidate Experience Cards.



4\. \*\*Verification/promotion layer\*\*

&#x20;  Runs probes, replays, held-out tasks, or lightweight checks. Promotes useful cards. Demotes stale or harmful cards.



5\. \*\*Action-time retrieval adapter\*\*

&#x20;  Given a new task, returns a compact action brief: relevant cards, evidence, confidence, preconditions, warnings, and what to ignore.



The key distinction: retrieval returns \*\*an operational brief\*\*, not a pile of memories.



\### Research map before code



Read and map these areas first:



1\. \*\*Agentic memory evaluation\*\*: LongMemEval, LoCoMo, MemoryAgentBench, MemoryArena, AMA-Bench, LongMemEval-V2, Mem2ActBench.

2\. \*\*Experience abstraction\*\*: Agent Workflow Memory, ReasoningBank, Voyager, ExpeL, LEGOMem.

3\. \*\*Memory management policy\*\*: Memory-R1, Mem-α, agentic memory update/delete/no-op systems.

4\. \*\*Temporal/provenance systems\*\*: Graphiti/Zep, TReMu, MemIR, temporal knowledge graphs.

5\. \*\*Long-context failure\*\*: Lost in the Middle, NoLiMa, long-context retrieval failure modes.

6\. \*\*Multi-agent memory\*\*: LEGOMem, multi-agent memory consistency, role-scoped procedural memory.



The research output should be a 15–25 page design note with three deliverables: failure taxonomy, Experience Atom specification, and eval protocol.



\### Prototype scope



Do \*\*not\*\* start with a general memory platform. Start with one hard, defensible domain:



> \*\*Web/workflow agents in specialized environments.\*\*



Best options:



\* BrowserGym / WebArena / WorkArena-style trajectories;

\* LongMemEval-V2 data for context-gathering memory;

\* a custom mini enterprise web environment with seeded gotchas and workflows;

\* then MemoryArena or Mem2ActBench for action-level validation.



The prototype should ingest prior trajectories and improve held-out tasks requiring:



\* workflow knowledge;

\* environment gotchas;

\* dynamic state tracking;

\* premise awareness;

\* failure-mode avoidance;

\* tool parameter grounding.



LongMemEval-V2 is especially aligned because it evaluates whether memory systems help agents become experienced operators in customized web environments. (\[arXiv]\[1])



\---



\## Smallest serious prototype



Build \*\*CEM-0: Causal Experience Memory for web agents\*\*.



\### What it includes



1\. \*\*Trace ingestion\*\*



&#x20;  \* Input: browser/tool trajectories with observations, actions, errors, final outcome.

&#x20;  \* Output: normalized raw trace ledger.



2\. \*\*Typed atom extraction\*\*



&#x20;  \* Extract observation atoms, action atoms, outcome atoms, error atoms, state-transition atoms, candidate skill atoms.

&#x20;  \* Every atom links back to trace evidence.



3\. \*\*Experience card generation\*\*



&#x20;  \* Generate cards only when multiple traces or a strong success/failure contrast supports the lesson.

&#x20;  \* Cards include preconditions, exceptions, and confidence.



4\. \*\*Verification loop\*\*



&#x20;  \* Generate small probes or replay checks.

&#x20;  \* Promote cards only if they pass.

&#x20;  \* Quarantine unsupported reflections.



5\. \*\*Retrieval adapter\*\*



&#x20;  \* Given a new task, return:



&#x20;    \* relevant cards;

&#x20;    \* why they apply;

&#x20;    \* source evidence;

&#x20;    \* preconditions to check;

&#x20;    \* known failure modes;

&#x20;    \* suggested next actions.



6\. \*\*Ablation harness\*\*



&#x20;  \* Compare no memory, raw RAG, temporal graph retrieval, simple summaries, unverified cards, verified CEM.



\### What it deliberately excludes



\* No universal memory API.

\* No MCP-first release.

\* No multi-framework integration.

\* No dashboard-first product.

\* No attempt to support every agent type.

\* No broad personal memory use case.

\* No benchmark leaderboard chasing before ablations.



\### What the demo should show



A strong public demo:



1\. A browser agent repeatedly fails in a specialized workflow.

2\. CEM ingests failed and successful traces.

3\. It extracts a verified Experience Card with evidence:



&#x20;  \* “This form silently rejects submission unless field X is set before field Y.”

4\. On a held-out task, the agent uses the card and succeeds.

5\. A vector-memory baseline retrieves related traces but misses the causal precondition.

6\. A poisoned/stale memory is injected.

7\. CEM refuses or demotes it because it lacks evidence or conflicts with newer traces.



That is a real capability demo.



\---



\## Benchmark/evaluation strategy



\### Primary metric



Use \*\*Marginal Memory Advantage\*\*:



```text

MMA = TaskSuccess(memory\_agent) - TaskSuccess(no\_memory\_agent)

```



But that is not enough. Also track:



| Metric                            | Why it matters                                       |

| --------------------------------- | ---------------------------------------------------- |

| Task success delta                | The only metric that ultimately matters for agents   |

| Memory precision-at-use           | Whether used memories were actually relevant         |

| Evidence support rate             | Whether claims are grounded in source traces         |

| Action influence                  | Whether memory changed the decisive action           |

| Harm rate                         | How often memory made the agent worse                |

| Stale-memory error rate           | Whether invalidated memories still affect action     |

| Contradiction resolution accuracy | Whether newer or scoped facts are handled correctly  |

| Latency/token overhead            | Whether capability is worth the cost                 |

| Generalization gap                | Whether lessons transfer beyond near-duplicate tasks |

| Promotion validity                | Whether verified memories outperform unverified ones |



\### Benchmarks to use



Use existing benchmarks in tiers.



\*\*Tier 1: sanity checks, not the main claim\*\*



\* LoCoMo;

\* LongMemEval;

\* MemoryAgentBench.



These are useful for conversational memory, temporal reasoning, knowledge updates, selective forgetting, and abstention. But they are not sufficient to prove agentic memory. LongMemEval is strong for long-term chat memory; LoCoMo is useful for long dialogue memory; MemoryAgentBench gives a broader competence framing. (\[arXiv]\[6])



\*\*Tier 2: main research benchmark\*\*



\* LongMemEval-V2;

\* MemoryArena;

\* AMA-Bench;

\* Mem2ActBench.



These target the harder question: whether memory over agent trajectories improves environment-specific knowledge, interdependent task success, long-horizon agentic memory, and memory-grounded tool action. (\[arXiv]\[1])



\*\*Tier 3: custom falsification suite\*\*



Create your own small benchmark specifically designed to break shallow memory:



1\. Same semantic task, different causal rule.

2\. Same UI labels, different workflow order.

3\. Stale preference versus current preference.

4\. Assistant speculation versus tool-observed fact.

5\. Successful trace with misleading irrelevant action.

6\. Failed trace containing the crucial negative lesson.

7\. Multi-agent stale shared memory.

8\. Poisoned memory injection.

9\. Memory that should be ignored because preconditions do not apply.

10\. Temporally valid historical fact that is operationally invalid now.



This custom suite is where the project can define a new standard.



\---



\## Public thesis



The strongest public thesis:



> \*\*Memory is not storage. Memory is tested experience that improves future action.\*\*



Longer version:



> Today’s agent memory systems mostly retrieve things the agent has seen. Real agents need to learn what past experience means: which actions caused success, which assumptions failed, which facts expired, which source is authoritative, and which lesson should change the next step. Causal Experience Memory is an open-source memory compiler that turns raw trajectories into verified, evidence-backed operational knowledge.



The demo headline:



> \*\*We turned a browser agent from a forgetful intern into an experienced operator of a private web app — without fine-tuning.\*\*



The paper/blog title:



> \*\*From Recall to Experience: A Causal Memory Runtime for Long-Horizon Agents\*\*



What serious builders would pay attention to:



\* It beats RAG/graph memory on held-out action tasks, not just chat QA.

\* It shows memory harm rate, not just memory accuracy.

\* It exposes evidence for every memory-derived recommendation.

\* It handles stale and poisoned memories better than flat stores.

\* It integrates with any backend, so it is not another vector DB competitor.

\* It gives researchers a concrete IR and eval harness.

\* It makes agent learning inspectable.



The project should publish:



1\. the Experience Atom spec;

2\. the trace-to-memory compiler;

3\. the eval harness;

4\. baseline comparisons;

5\. failure case gallery;

6\. a small reproducible dataset of trajectories and held-out tasks.



\---



\## What to avoid



Avoid these traps hard.



1\. \*\*Do not build another MCP memory server.\*\* MCP is distribution plumbing. It is not the invention.



2\. \*\*Do not build another vector/graph RAG layer.\*\* You will be competing with Qdrant, Graphiti, Zep, Mem0, Supermemory, Letta, and every framework vendor.



3\. \*\*Do not lead with “universal memory.”\*\* Universal memory is usually vague product positioning. Serious research needs a narrow domain and falsifiable capability.



4\. \*\*Do not mistake developer experience for memory intelligence.\*\* SDKs, dashboards, CLI tools, connectors, and framework integrations are useful only after the primitive works.



5\. \*\*Do not optimize for LongMemEval alone.\*\* LongMemEval is important, but leaderboard gains there can still fail in agentic tasks.



6\. \*\*Do not trust self-reflection without verification.\*\* A plausible lesson is not a memory. It is a hypothesis.



7\. \*\*Do not flatten everything into summaries.\*\* Summaries destroy provenance, source role, temporal scope, and negative evidence.



8\. \*\*Do not overbuild protocol before capability.\*\* A multi-agent memory protocol is attractive, but premature unless you can demonstrate a concrete consistency failure and fix.



9\. \*\*Do not hide behind “human-like memory” metaphors.\*\* Use measurable primitives: evidence, validity, confidence, action effect, harm rate.



10\. \*\*Do not build for every agent framework.\*\* Pick one agent loop, one environment class, one hard eval.



11\. \*\*Do not ignore harmful memory.\*\* A memory system that improves average success while creating rare catastrophic stale-memory failures is not serious.



12\. \*\*Do not let the model write its own truth.\*\* Separate evidence, hypothesis, and promoted claim.



\---



\## Kill criteria



Kill or pivot the project if any of these happen.



1\. \*\*RAG parity:\*\* hybrid RAG over raw traces matches the system within 5–10% on held-out agentic tasks at comparable token/latency cost.



2\. \*\*No action delta:\*\* memory improves answer accuracy but does not improve task success or decisive action quality.



3\. \*\*Verification theater:\*\* verified memories do not outperform unverified reflections on held-out tasks.



4\. \*\*High harm rate:\*\* memory causes more than a small controlled rate of stale, false, or overgeneralized action errors.



5\. \*\*No generalization:\*\* extracted experience only helps near-duplicate tasks.



6\. \*\*Too much manual curation:\*\* the system requires humans to author the useful memories.



7\. \*\*Backend dependence:\*\* the “invention” disappears when swapping vector DBs, graph stores, or LLM providers.



8\. \*\*Latency destroys utility:\*\* memory maintenance or query time makes the agent impractical.



9\. \*\*Benchmark-only success:\*\* the system performs on LongMemEval-style QA but fails MemoryArena/LME-V2/custom action tasks.



10\. \*\*No clear primitive:\*\* after eight weeks, the project is still a pile of prompts, stores, and adapters rather than a defensible IR/lifecycle/eval.



\---



\## Final Plan 1



Build \*\*Causal Experience Memory\*\*, not a memory store.



The foundation should be:



1\. \*\*Research map:\*\* agentic memory benchmarks, workflow memory, learned memory management, temporal/provenance memory, long-context failure, multi-agent memory consistency.



2\. \*\*Invention thesis:\*\* memory is the transformation of raw trajectories into verified future action advantage.



3\. \*\*Architecture primitive:\*\* Experience Atoms and Experience Cards with evidence, temporal validity, causal claim, preconditions, exceptions, confidence, and verification status.



4\. \*\*Prototype scope:\*\* web/workflow agents in specialized environments; ingest 100–500 trajectories; improve held-out workflow/gotcha/dynamic-state tasks.



5\. \*\*Eval strategy:\*\* measure marginal memory advantage, memory harm rate, evidence support, action influence, and cost against no-memory, full-context, RAG, temporal graph, and unverified-reflection baselines.



6\. \*\*Kill criteria:\*\* kill if verified causal experience does not beat simple RAG/runbooks on held-out agentic tasks.



7\. \*\*Public narrative:\*\* “Memory is not recall. Memory is tested experience that changes future action.”



That is the project with breakout potential. Not because it is bigger than existing memory systems, but because it attacks the bottleneck they mostly route around: \*\*how an agent turns experience into reliable future competence.\*\*



\[1]: https://arxiv.org/html/2605.12493v1 "LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues"

\[2]: https://digitaleconomy.stanford.edu/publication/memoryarena-benchmarking-agent-memory-in-interdependent-multi-session-agentic-tasks/ "MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks - Stanford Digital Economy Lab"

\[3]: https://arxiv.org/html/2602.22769v3 "AMA-Bench: Evaluating Long-Horizon Memory for Agentic Applications"

\[4]: https://github.com/getzep/graphiti "GitHub - getzep/graphiti: Build Real-Time Knowledge Graphs for AI Agents · GitHub"

\[5]: https://supermemory.ai/research/ "Supermemory Research — State-of-the-Art Agent Memory"

\[6]: https://arxiv.org/abs/2410.10813?utm\_source=chatgpt.com "LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory"

\[7]: https://snap-research.github.io/locomo/ "Evaluating Very Long-Term Conversational Memory of LLM Agents"

\[8]: https://arxiv.org/html/2507.05257v2 "Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions"

\[9]: https://openreview.net/forum?id=NTAhi2JEEE "Agent Workflow Memory | OpenReview"

\[10]: https://research.google/blog/reasoningbank-enabling-agents-to-learn-from-experience/ "ReasoningBank: Enabling agents to learn from experience"

\[11]: https://arxiv.org/abs/2508.19828 "\[2508.19828] Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning"

\[12]: https://aclanthology.org/2025.findings-acl.972/ "TReMu: Towards Neuro-Symbolic Temporal Reasoning for LLM-Agents with Memory in Multi-Session Dialogues - ACL Anthology"

\[13]: https://arxiv.org/html/2605.25869v1 "Mitigating Provenance-Role Collapse in Long-Term Agents via Typed Memory Representation"

\[14]: https://arxiv.org/html/2602.19320v1 "Anatomy of Agentic Memory: Taxonomy and Empirical Analysis of Evaluation and System Limitations"

\[15]: https://arxiv.org/html/2603.10062v1 "Multi-Agent Memory from a Computer Architecture Perspective: Visions and Challenges Ahead"



