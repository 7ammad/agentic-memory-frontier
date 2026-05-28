\## Verdict



I would \*\*approve the direction, but not the plan as-is\*\*.



The thesis is strong: CEM should not be “memory storage”; it should be \*\*verified experience that measurably improves future action\*\*. The plan correctly centers the missing second clause: causal read-path + proof through Marginal Memory Advantage, not just write-path cleanliness. The repo README already frames the project around CEM-0 as a kernel that ingests traces, extracts typed memories, validates/quarantines them, promotes experience cards, and returns action briefs rather than raw memory dumps. (\[GitHub]\[1])



The current plan is good as a \*\*program charter\*\*. It is not yet sharp enough as an \*\*execution plan\*\* because it still leaves the hard parts under-specified: the experiment contract, schema changes, causal attribution discipline, baseline definitions, leakage controls, and exact promotion semantics.



My recommendation: \*\*keep Approach C / eval-first\*\*, but upgrade the plan into a pre-registered proof program with a tighter CEM-1 milestone.



\---



\# 1. What is already strong



\## 1.1 The thesis is correctly framed



The plan’s core bet is the right one:



> Prevent bad memories from becoming trusted experience, then prove that verified experience changes what agents do.



That is materially better than building another vector memory wrapper. The plan correctly identifies that the project’s current write path is only half the invention, while the unbuilt read-path and proof loop are the actual frontier. The plan states that components 4–7 remain the unfinished program weight: consolidation, verification/promotion, causal read-path, and evaluation harness. (\[GitHub]\[2])



\## 1.2 Eval-first is the right sequencing



The plan’s Phase 0 says the first deliverable should be the proving-ground spine: seeded environment, baseline ladder, MMA harness, and falsification suite, with no capability change shipped until the measuring instrument exists. That is the right call. Without that, every later improvement can become a vibes-based “memory helped” claim. (\[GitHub]\[2])



\## 1.3 The current weaknesses are mostly identified honestly



The plan correctly points out three concrete implementation gaps:



The current `promote()` path flips atoms/cards to `verified` without probe-earned verification. The code confirms this: `promote()` validates/quarantines candidates, but then directly sets `atom.promotion\_status = "verified"` when merging or creating a card. (\[GitHub]\[3])



The current action brief path does not produce a real expected action delta. The code returns `expected\_action\_delta=None`. (\[GitHub]\[3])



The current card scorer is lexical overlap, not action-value retrieval. The `score\_card()` function builds a haystack from task fields, splits title/use/template text into terms, and counts matching terms longer than three characters. (\[GitHub]\[3])



Those are exactly the right failure points to attack.



\---



\# 2. Main critique: the plan is directionally right but experimentally underpowered



\## 2.1 `expected\_action\_delta` must not be filled from observational action-influence logs alone



The plan says Phase 1 can populate `expected\_action\_delta` from the action-influence outcome loop until component 5 produces probe-measured lift. That is dangerous.



A post-brief outcome is \*\*not\*\* a counterfactual. If the agent reads a card and succeeds, you do not know whether the card caused success. The task may have been easy, the base model may have succeeded anyway, or the brief may have merely co-occurred with success.



Enhancement: split the field into three concepts:



```text

observed\_post\_brief\_delta        # what happened after the brief was read

estimated\_action\_delta           # model/scorer estimate, explicitly uncertain

verified\_action\_lift             # probe/ablation-backed causal estimate

```



Only `verified\_action\_lift` should be allowed to drive `promotion\_status="verified"` or be presented as proof. Before probes exist, `expected\_action\_delta` should either remain `None` or be marked with `lift\_source="observational\_unverified"`.



\## 2.2 Phase order needs one adjustment: minimal consolidation must precede verification



The current sequence is:



```text

Phase 0 — eval harness

Phase 1 — causal read-path

Phase 2 — verification \& promotion

Phase 3 — consolidation depth

```



The problem: verification operates on the thing being promoted. If Phase 2 verifies weak, duplicated, over-specific, or poorly abstracted cards, then Phase 3 later changes the memory object after verification. That breaks the meaning of “verified.”



Better sequencing:



```text

Phase 0 — Proving-ground spine

Phase 1 — Read-path instrumentation + influence ledger

Phase 1.5 — Minimal card identity/consolidation contract

Phase 2 — Probe-gated promotion

Phase 3 — Deep consolidation and supersession

Phase 4 — External benchmark runs

```



Phase 1.5 does not need full abstraction. It needs enough card identity stability that a probe result attaches to a durable card, not a disposable intermediate object.



\## 2.3 The schema is not ready for the plan’s claims



The current models expose `ExperienceAtom`, `ExperienceCard`, `TaskContext`, and `ActionBrief`. `ActionBrief` has `expected\_action\_delta`, but no `brief\_id`, `influence\_id`, scorer version, score breakdown, confidence interval, or lift source. `ExperienceCard` has `tested\_by\_probe\_ids`, but no measured lift, probe summary, deactivation reason, supersession state, or retrieval/action influence counters. (\[GitHub]\[4])



Plan enhancement: add explicit runtime evidence models rather than stuffing everything into cards.



Required new primitives:



```python

class ActionBriefRecord:

&#x20;   brief\_id: str

&#x20;   task\_id: str | None

&#x20;   generated\_at: datetime

&#x20;   scorer\_version: str

&#x20;   candidate\_card\_ids: list\[str]

&#x20;   selected\_card\_ids: list\[str]

&#x20;   score\_breakdown\_by\_card: dict\[str, dict\[str, float]]

&#x20;   expected\_action\_delta: float | None

&#x20;   expected\_action\_delta\_ci: tuple\[float, float] | None

&#x20;   expected\_action\_delta\_source: Literal\[

&#x20;       "none",

&#x20;       "observational\_unverified",

&#x20;       "probe\_verified",

&#x20;       "heldout\_eval"

&#x20;   ]



class ActionInfluenceEvent:

&#x20;   influence\_id: str

&#x20;   brief\_id: str

&#x20;   task\_id: str | None

&#x20;   card\_ids\_read: list\[str]

&#x20;   action\_taken: str | None

&#x20;   outcome\_score: float | None

&#x20;   baseline\_outcome\_score: float | None

&#x20;   observed\_delta: float | None

&#x20;   counterfactual\_method: Literal\[

&#x20;       "none",

&#x20;       "paired\_no\_memory",

&#x20;       "replay\_ablation",

&#x20;       "heldout\_probe"

&#x20;   ]



class VerificationProbe:

&#x20;   probe\_id: str

&#x20;   card\_id: str

&#x20;   task\_id: str

&#x20;   probe\_type: Literal\[

&#x20;       "heldout\_task",

&#x20;       "replay\_ablation",

&#x20;       "negative\_control",

&#x20;       "staleness\_probe",

&#x20;       "contradiction\_probe"

&#x20;   ]

&#x20;   threshold: float

&#x20;   baseline\_policy: str

&#x20;   memory\_policy: str



class VerificationResult:

&#x20;   probe\_id: str

&#x20;   card\_id: str

&#x20;   passed: bool

&#x20;   memory\_score: float

&#x20;   baseline\_score: float

&#x20;   lift: float

&#x20;   lift\_ci: tuple\[float, float] | None

&#x20;   failure\_reason: str | None

```



Without these, the system can report “verified” but cannot prove what was verified, against what baseline, under which scorer, and with what variance.



\## 2.4 The baseline ladder needs operational definitions



The plan lists no-memory, full-context, summary, vector RAG, time-aware RAG, temporal graph, unverified reflection, and human runbook. That is right directionally, but too loose.



Each baseline needs a fixed implementation contract:



```text

no\_memory:

&#x20; Agent receives only current task context.



full\_context:

&#x20; Agent receives all allowed prior trace material within the same token/cost budget policy.



summary:

&#x20; Agent receives generated summaries from prior traces.

&#x20; Summary generator version fixed.



vector\_rag:

&#x20; Retrieve top-k chunks by embedding similarity.

&#x20; Same token budget as CEM brief.



time\_aware\_rag:

&#x20; Vector RAG plus valid\_from/valid\_until filtering.



temporal\_graph:

&#x20; Graph retrieval over entity/event/time links.

&#x20; No causal scorer.



unverified\_reflection:

&#x20; Store free-form reflections without validation/promotion gate.



human\_runbook:

&#x20; Upper-bound / ceiling baseline, not a must-beat v1 baseline.

```



Important correction: \*\*human runbook should be a ceiling, not a required baseline to beat\*\*. If the plan requires CEM to beat a good human-authored runbook immediately, it may kill a valid technical path for the wrong reason. CEM should beat the automated baselines first, then measure distance to human runbook.



\## 2.5 External benchmark mapping should be claim-specific



The plan lists HaluMem, MemoryArena, LongMemEval-V2, and AgingBench together. They are not equivalent.



Use them this way:



| Benchmark      | Use in this program                                                                                         | Not enough for                                  |

| -------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |

| HaluMem        | Write integrity: extraction, updating, memory QA, hallucination propagation                                 | Primary action-success MMA                      |

| MemoryArena    | Main external memory-action benchmark; multi-session tasks where later behavior depends on prior experience | Fine-grained write-path hallucination diagnosis |

| LongMemEval-V2 | Environment experience / evidence retrieval / “experienced colleague” behavior                              | Direct online task execution unless wrapped     |

| AgingBench     | Staleness, revision, lifespan degradation, maintenance aging                                                | First proof of CEM’s basic action advantage     |



HaluMem decomposes memory evaluation into extraction, updating, and memory QA, which fits the write-path and hallucination-resistance side. (\[arXiv]\[5]) MemoryArena is closer to the MMA claim because it evaluates memory use in interdependent multi-session agentic tasks. (\[arXiv]\[6]) LongMemEval-V2 focuses on whether agents acquire environment-specific experience across long histories and web-agent trajectories. (\[arXiv]\[7]) AgingBench is best used for lifespan/staleness/revision diagnostics, not first proof of the read path. (\[arXiv]\[8])



\## 2.6 The “current state” section should be corrected



The plan says the external benchmark runners summarize datasets and reuse synthetic delta. That is partly stale or too broad. The repo’s external benchmark decision doc says local adapters/runners already exist for HaluMem, MemoryArena-style data, and LongMemEval-V2-style data, but explicitly says these are not full benchmark results. (\[GitHub]\[9])



Replace the current state line for component 7 with:



```text

7 Evaluation Harness:

Partial. Synthetic corruption eval exists. Local external dataset adapters/runners exist for HaluMem, MemoryArena-style tasks, and LongMemEval-V2-style tasks, but they are adapter/proxy/reporting layers. Missing: locked held-out exam, paired baseline ladder, true action-loop MMA, confidence intervals, leakage controls, and full external benchmark scores.

```



That is more accurate and gives implementation a cleaner target.



\---



\# 3. Enhanced plan: CEM-1 Proof Program



I would rename the immediate program from “full CEM program” to:



> \*\*CEM-1 Proof Program: prove verified experience improves future action under a locked evaluation contract.\*\*



That avoids overbuilding while preserving ambition.



\## 3.1 Program objective



Build the smallest kernel + evaluation harness that can make or falsify this claim:



```text

CEM-1 converts prior agent traces into verified, evidence-backed, temporally scoped Experience Cards that improve held-out task success over no-memory, summary memory, vector RAG, time-aware RAG, and unverified reflection baselines.

```



Primary proof:



```text

MMA = mean\_i(TaskSuccess\_i(CEM) - TaskSuccess\_i(no\_memory))

```



Secondary proof:



```text

CEM\_delta\_vs\_baseline\_j =

&#x20; mean\_i(TaskSuccess\_i(CEM) - TaskSuccess\_i(baseline\_j))

```



Minimum success threshold:



```text

MMA > 0

and

MMA lower 95% CI > 0 on the locked held-out set

and

CEM beats lexical/word-overlap retrieval by ≥ 5 percentage points

and

no injected negative-control memory is promoted to verified

```



If the held-out set is small, require transparent reporting rather than overclaiming:



```text

MMA > 0 with CI reported, but marked "directional" until n is large enough.

```



\## 3.2 Revised phase plan



\### Phase 0 — Locked proving-ground spine



Deliverable: a reproducible experiment harness that can score memory configurations before any new memory capability ships.



Build:



```text

ExperimentSpec

BaselineConfig

RunResult

ComparisonReport

MMAReport

FalsificationReport

```



Required files:



```text

packages/cem-eval/src/cem\_eval/experiment.py

packages/cem-eval/src/cem\_eval/mma.py

packages/cem-eval/src/cem\_eval/baselines.py

packages/cem-eval/src/cem\_eval/seeded\_env.py

tests/eval/test\_mma\_harness.py

docs/eval/phase-0-preregistered-exam.md

```



Hard requirements:



```text

\- fixed train/dev/held-out split

\- fixed random seeds

\- paired task runs

\- no-memory baseline always reported

\- lexical-overlap baseline always reported

\- confidence intervals reported

\- memory harm reported

\- cost/latency reported

\- task leakage guard

\- canary negative controls

```



Definition of done:



```text

python -m pytest

python scripts/run\_synthetic\_eval.py

python scripts/run\_mma\_exam.py --config docs/eval/phase-0-preregistered-exam.yaml

```



Output must include:



```text

no\_memory\_success

cem\_success

mma

mma\_ci

baseline\_ladder

memory\_harm\_rate

false\_promotion\_count

cost\_per\_task

latency\_per\_task

```



\### Phase 1 — Read-path instrumentation before read-path intelligence



Do not jump straight to clever retrieval. First make retrieval measurable.



Build:



```text

brief\_id

influence\_id

ActionBriefRecord

ActionInfluenceEvent

score\_breakdown\_by\_card

scorer\_version

retrieval\_count

last\_retrieved\_at

```



Change `retrieve\_action\_brief()` semantics:



```text

retrieve\_action\_brief(task, max\_cards) -> ActionBrief



must:

&#x20; - create a brief\_id

&#x20; - log candidate card IDs

&#x20; - log selected card IDs

&#x20; - log feature scores

&#x20; - return influence\_id

&#x20; - never invent expected\_action\_delta

```



Definition of done:



```text

\- every returned ActionBrief has a persisted ActionBriefRecord

\- every brief can later be closed with an ActionInfluenceEvent

\- expected\_action\_delta remains None unless sourced from probe/ablation result

\- score\_card no longer returns an opaque int

```



\### Phase 2 — Transparent action-value scorer



Replace lexical overlap with a two-stage retriever:



```text

Stage A — candidate generation:

&#x20; - domain/task-family filter

&#x20; - temporal validity filter

&#x20; - precondition cue match

&#x20; - lexical/embedding recall candidate pool



Stage B — action-value reranker:

&#x20; score =

&#x20;   + precondition\_match

&#x20;   + domain\_task\_fit

&#x20;   + evidence\_support

&#x20;   + verified\_lift\_prior

&#x20;   + recency\_validity

&#x20;   - contradiction\_penalty

&#x20;   - staleness\_penalty

&#x20;   - exception\_boundary\_penalty

&#x20;   - overgeneralization\_penalty

```



The initial scorer should be a transparent feature ranker, not a learned model. The plan already recommends that, and I agree. But the score must output a feature breakdown, not a single number.



Example score record:



```json

{

&#x20; "card\_id": "card\_123",

&#x20; "total\_score": 0.72,

&#x20; "features": {

&#x20;   "precondition\_match": 0.24,

&#x20;   "domain\_task\_fit": 0.15,

&#x20;   "evidence\_support": 0.10,

&#x20;   "verified\_lift\_prior": 0.00,

&#x20;   "recency\_validity": 0.08,

&#x20;   "contradiction\_penalty": 0.00,

&#x20;   "staleness\_penalty": 0.00,

&#x20;   "exception\_boundary\_penalty": -0.02

&#x20; },

&#x20; "scorer\_version": "cem-action-ranker-v0"

}

```



Phase 2 success is not “better-looking briefs.” It is:



```text

CEM action-value scorer beats lexical-overlap retrieval by ≥ 5pp task success on held-out tasks.

```



\### Phase 3 — Probe-gated promotion



Change promotion semantics.



Current behavior:



```text

validate(atom)

promote(atom) -> verified card

```



Required behavior:



```text

validate(atom) -> proposed | candidate | quarantined

promote(atom) -> candidate card only

verify\_card(card, probe) -> verified | deprecated | quarantined

```



Promotion should no longer mean “verified.” It should mean “eligible candidate card exists.”



New lifecycle:



```text

proposed atom

&#x20; -> candidate atom

&#x20; -> candidate card

&#x20; -> probe scheduled

&#x20; -> probe passed

&#x20; -> verified card

&#x20; -> retrieval eligible for verified-lift scoring

```



Negative control rule:



```text

Known-false, stale, contradictory, or poisoned memory may become proposed/candidate for testing,

but must never become verified.

```



Definition of done:



```text

\- no direct assignment to promotion\_status="verified" outside verification result handler

\- every verified card has at least one passing VerificationResult

\- every verified card exposes measured lift or explicitly states "verification type: non-lift integrity probe"

\- negative-control probe leaks fail the suite

```



\### Phase 4 — Minimal consolidation before deep abstraction



Consolidation should be split into two levels.



Level 1: identity-safe consolidation.



```text

\- merge exact or near-exact duplicate atoms

\- preserve all source spans

\- preserve all source atom IDs

\- never generalize beyond evidence

\- create stable card identity

```



Level 2: abstraction.



```text

\- abstract repeated patterns

\- produce generalized use\_when/do/check\_first

\- require source-span support for each generalized claim

\- test abstraction against held-out probes

```



Do not verify an abstraction just because its source atoms were verified. The abstraction itself needs support.



\### Phase 5 — External benchmark execution



Do not treat all benchmarks as one gate.



Use this gate structure:



```text

Gate A — internal seeded MMA:

&#x20; primary proof of action advantage



Gate B — HaluMem:

&#x20; write-path hallucination / update / QA integrity



Gate C — MemoryArena:

&#x20; external memory-action transfer



Gate D — LongMemEval-V2:

&#x20; environment-experience retrieval and evidence quality



Gate E — AgingBench:

&#x20; staleness, revision, lifespan degradation

```



The repo already says the current external adapters are not full benchmark results, only local ingestion/scoring/reporting layers. (\[GitHub]\[9]) The enhanced plan should therefore say: “Phase 5 runs full benchmark comparisons,” not merely “integrate adapters.”



\---



\# 4. Add this acceptance contract to the plan



Use this as the upgraded Definition of Done:



```text

CEM-1 is complete only when all of the following are true:



1\. The Phase 0 exam is locked before scorer tuning.

2\. The no-memory baseline, lexical-overlap baseline, summary baseline, vector RAG baseline, time-aware RAG baseline, and unverified-reflection baseline are run under the same task set and reporting contract.

3\. MMA is reported as a paired task-level delta with n, confidence interval, cost, and latency.

4\. CEM beats no-memory on held-out tasks.

5\. CEM beats lexical-overlap retrieval by at least 5pp task success on held-out tasks.

6\. No injected known-false / stale / contradictory / poisoned memory is promoted to verified.

7\. Every verified card has a stored verification result.

8\. Every Action Brief has a persisted brief record and influence ID.

9\. `expected\_action\_delta` is never populated from unpaired observation without `source="observational\_unverified"`.

10\. Full pytest, synthetic eval, and MMA exam pass with committed machine-readable reports.

11\. If MMA ≤ 0 after the pre-registered tuning budget, the program reports failure rather than changing the exam.

```



\---



\# 5. Specific edits I would make to the existing document



\## Replace the status metadata



Current doc says:



```text

Status: draft for review (uncommitted until Hammad approves)

```



But the file is visible on the repo’s `main` branch. (\[GitHub]\[2])



Replace with:



```text

Status: draft on main, pending Hammad review before implementation lock

```



\## Replace “expected\_action\_delta is populated from action-influence outcome loop”



Replace with:



```text

In Phase 1, action-influence logging records observed post-brief outcomes, but these are not treated as causal lift. `expected\_action\_delta` remains null unless sourced from a paired probe, replay ablation, or held-out eval. Observational outcomes may be stored separately as `observed\_post\_brief\_delta` with `lift\_source="observational\_unverified"`.

```



\## Replace “Promotion gate” section



Current plan says candidate-to-verified requires a verification probe, which is correct, but the implementation language should force API separation.



Add:



```text

`promote()` must stop meaning "mark verified." It creates or updates a candidate Experience Card. Only `verify\_card()` or `apply\_verification\_result()` may set `promotion\_status="verified"`.

```



\## Add schema migration section



Add:



```text

Required schema/model extensions:

\- ActionBrief.brief\_id

\- ActionBrief.influence\_id

\- ActionBrief.scorer\_version

\- ActionBrief.expected\_action\_delta\_source

\- ActionBrief.score\_breakdown\_by\_card

\- ExperienceCard.measured\_lift

\- ExperienceCard.measured\_lift\_ci

\- ExperienceCard.verification\_result\_ids

\- ExperienceCard.deactivated\_at

\- ExperienceCard.deactivated\_reason

\- ExperienceCard.superseded\_by\_card\_ids

\- ActionBriefRecord

\- ActionInfluenceEvent

\- VerificationProbe

\- VerificationResult

```



Because the current store serializes model payloads into SQLite tables, defaulted fields can probably be introduced without complex relational migration at first, but query/index needs will eventually require explicit tables for probes, brief records, and influence events. The current storage layer uses payload tables for traces, atoms, cards, validations, and validation decisions. (\[GitHub]\[10])



\## Add leakage controls



Add:



```text

Leakage controls:

\- Memory source traces and held-out task answers must be disjoint.

\- Held-out tasks may share environment rules/patterns but not exact task statements or answer artifacts.

\- Baselines receive the same task context budget unless explicitly marked as an upper-bound baseline.

\- Human runbook is reported as an upper bound, not a required CEM-1 beat target.

\- Tuning occurs only on dev split; held-out split is evaluated once per locked release candidate.

```



\## Upgrade fake-green checks



The current no-fake-green idea catches literal `True` checks, but that is insufficient.



Add:



```text

Every monitor/eval gate must include a failure canary. The test suite intentionally injects one known-bad condition and asserts that the gate fails. Static checks against literal `True` are useful but not enough.

```



\---



\# 6. Highest-priority implementation backlog



\## P0 — Make verification impossible to fake



```text

\- Refactor promote() so it cannot set verified.

\- Add verify\_card()/apply\_verification\_result().

\- Add VerificationProbe + VerificationResult models.

\- Add test: direct promote() never yields verified.

\- Add test: known-false memory cannot be verified.

```



\## P0 — Build the MMA harness before retrieval changes



```text

\- Implement ExperimentSpec.

\- Implement no-memory and lexical-overlap baselines.

\- Implement paired task scoring.

\- Implement confidence interval reporting.

\- Implement memory harm rate.

\- Write locked Phase 0 exam config.

```



\## P0 — Add action influence ledger



```text

\- Add brief\_id and influence\_id.

\- Persist ActionBriefRecord.

\- Add close\_action\_influence(influence\_id, action, outcome).

\- Report unclosed influence count.

```



\## P1 — Replace scorer



```text

\- Keep lexical scorer as baseline.

\- Add feature scorer with score breakdown.

\- Add temporal/staleness/contradiction penalties.

\- Add precondition matching.

\- Report CEM scorer vs lexical scorer.

```



\## P1 — Minimal card identity/consolidation



```text

\- Stable card fingerprint.

\- Dedup exact/near-exact atom claims.

\- Preserve all source spans.

\- Prevent generalized card verification unless abstraction itself has support.

```



\## P2 — External benchmark execution



```text

\- Run real HaluMem dataset against baselines.

\- Run MemoryArena action-loop subset.

\- Run LongMemEval-V2 evidence retrieval subset.

\- Add AgingBench only after staleness/supersession mechanics exist.

```



\---



\# 7. Final judgment



The plan should move forward, but with one hard rule:



> Do not let the system claim “verified,” “causal,” or “expected action delta” until the experiment machinery can prove the claim.



The best version of this program is not “build the full memory platform.” It is:



```text

CEM-1 Proof Program:

a small kernel + ruthless eval harness that proves whether verified experience creates marginal action advantage.

```



That is the right wedge, the right research claim, and the right product foundation.



\[1]: https://github.com/7ammad/agentic-memory-frontier "GitHub - 7ammad/agentic-memory-frontier: Research and design workspace for a frontier agentic memory system · GitHub"

\[2]: https://github.com/7ammad/agentic-memory-frontier/blob/main/docs/2026-05-28-causal-experience-memory-full-program-design.md "agentic-memory-frontier/docs/2026-05-28-causal-experience-memory-full-program-design.md at main · 7ammad/agentic-memory-frontier · GitHub"

\[3]: https://github.com/7ammad/agentic-memory-frontier/blob/main/packages/cem-core/src/cem\_core/kernel.py "agentic-memory-frontier/packages/cem-core/src/cem\_core/kernel.py at main · 7ammad/agentic-memory-frontier · GitHub"

\[4]: https://github.com/7ammad/agentic-memory-frontier/blob/main/packages/cem-core/src/cem\_core/models.py "agentic-memory-frontier/packages/cem-core/src/cem\_core/models.py at main · 7ammad/agentic-memory-frontier · GitHub"

\[5]: https://arxiv.org/abs/2511.03506?utm\_source=chatgpt.com "HaluMem: Evaluating Hallucinations in Memory Systems of Agents"

\[6]: https://arxiv.org/abs/2602.16313?utm\_source=chatgpt.com "MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks"

\[7]: https://arxiv.org/abs/2605.12493?utm\_source=chatgpt.com "LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues"

\[8]: https://arxiv.org/abs/2605.26302?utm\_source=chatgpt.com "Your Agents Are Aging Too: Agent Lifespan Engineering for Deployed Systems"

\[9]: https://github.com/7ammad/agentic-memory-frontier/blob/main/docs/cem-0-external-benchmark-decision.md "agentic-memory-frontier/docs/cem-0-external-benchmark-decision.md at main · 7ammad/agentic-memory-frontier · GitHub"

\[10]: https://github.com/7ammad/agentic-memory-frontier/blob/main/packages/cem-core/src/cem\_core/storage.py "agentic-memory-frontier/packages/cem-core/src/cem\_core/storage.py at main · 7ammad/agentic-memory-frontier · GitHub"



