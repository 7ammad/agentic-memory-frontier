# SuperClaude Memory — Deep Technical Review

**Author:** Claude (reviewing for Hammad)
**Date:** 2026-05-26
**Scope:** Architecture review of SuperClaude memory MCP + property-based comparison against ten contemporary agentic memory systems + literature grounding from 2025–2026 primary sources.
**Out of scope:** Designing the Codex memory system, designing the ACS inter-agent channel, modifying SuperClaude. Those are downstream projects this doc is meant to inform.

---

## §0 Methodology

### Source tiers

Every comparison cell and every architectural claim in this doc carries a source tier. The tiers are not editorial; they constrain what claims can be made from each.

| Tier | Definition | What claims it supports |
|---|---|---|
| `[verified]` | Read primary source (code, paper §, official spec) in this session. Citation: `file:line` or `arXiv:NNNN §X`. | "X does Y" — direct claim. |
| `[doc-verified]` | Read official vendor documentation. Citation: doc URL + extraction prompt. | "X documents that it does Y" — vendor's claim, not independent verification. |
| `[survey-only]` | Only third-party summary read. Citation: blog/comparison URL + tier note. | "X is reported to do Y" — explicitly hedged. |

If a cell has no tier, it's a typo — bug me. The point of tagging is that the next reader can ratchet `[survey-only]` cells up to `[doc-verified]` or `[verified]` by spending 30 minutes per row.

### What this review CAN establish

1. SuperClaude's architecture as it exists in `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\src\` on 2026-05-26 — fully verified, since I read the source.
2. Each comparator system's *claimed* architecture per its public docs/papers/repos — verified to the tier listed.
3. Property deltas where both sides are `[verified]` or `[doc-verified]`.
4. A taxonomy under which the field can be compared on testable axes.

### What this review CAN NOT establish (without further work)

1. Empirical performance — I did not run LongMemEval, MemBench, or any other benchmark. Cited scores are vendor self-reports.
2. Real-world failure rates — failure modes listed are derived from architecture analysis + the security survey [arXiv:2604.16548](https://arxiv.org/abs/2604.16548), not from fuzzing or red-teaming.
3. Production cost — no system was load-tested.
4. Comparative quality at the LLM-output level — that requires A/B trials.

### Replicability recipe

Every URL is in §10. Every SuperClaude code citation is `[code: src/file.ts:line]` reproducible by reading `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\src\<file>`. Every paper citation is `[paper: arXiv:NNNN §X]`. A third party with the same source access could reproduce every cell in §4 in ≤4 hours.

---

## §1 Problem formulation — what is agent memory, formally

Before comparing implementations, define the object.

**Agent memory M is a 4-tuple ⟨S, W, R, L⟩:**
- **S** — *state space.* The set of representations the memory can hold. For dense-vector systems: ℝ^d. For graph systems: a typed property graph G = (V, E, attrs). For SQL-only systems: relational rows. For markdown-first (GBrain): a tree of markdown files plus derived indices over them.
- **W** — *write semantics.* The function `(trajectory τ, current_state s) → (new_state s')`. Includes: extraction policy (what gets pulled out of τ), dedup policy (when do similar writes collapse), provenance policy (what gets attached to the write).
- **R** — *read semantics.* The function `(query q, current_state s) → (context c)`. Includes: scoring function, ranking, filtering, hydration of structured fields.
- **L** — *lifecycle policy.* The function `state s × time t → state s'`. Covers TTL, decay, promotion on access, demotion on staleness, hard delete vs. soft archive, supersession chains.

**The objective the agent optimizes over M:**

> Maximize the agent's expected task success on future trajectories drawn from some distribution D, subject to a fixed compute budget per task and a fixed storage budget over time.

Every system in §4 is an attempt to approximate the optimum of this objective under different assumptions about D, the compute budget shape, the storage shape, and the failure-cost asymmetry between false positives (wrong context returned) and false negatives (relevant memory missed).

This framing matters because it gives the comparison its axes. A system optimized for "single-user dialogue assistant" (Mem0's design point) will look different from one optimized for "research agent over a 50K-page knowledge base" (GBrain's design point) — and "better" without naming the distribution D is vapid.

SuperClaude's *implicit* D is "one developer's multi-project life, accumulating decisions, lessons, preferences, and active tasks over months", with compute budget ~10 MCP tool calls per session start and storage budget on the order of 10⁴ active rows. Most of what follows can be read as: "is the architecture's shape well-matched to that D?"

---

## §2 SuperClaude architecture — source-grounded deep dive

Everything below is `[verified]` from source under `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\src\`.

### 2.1 Storage substrate

- **Engine:** LanceDB, single embedded vector store at `~/.claude/memory/lancedb`. Lazy initialization on first tool call to avoid Claude Code startup timeout [code: src/store.ts:131-160].
- **Table:** single table `agent_memories` [code: src/store.ts:119]. Created from a seed row at first run, then seed is deleted [code: src/store.ts:153-159].
- **Row schema (21 columns):** `id, content, vector, type, scope, priority, topics (JSON-string array), status, visibility, created_at, updated_at, accessed_at, access_count, expires_at, supersedes, superseded_by, source_session, source_type, media_type, media_path, media_description, task_data (JSON-string)` [code: src/schema.ts:84-108].

### 2.2 Embedding

- **Model:** BGE-M3, **1024 dims**, via `@openclaw/local-embeddings` [code: src/schema.ts:114].
- **Asymmetric:** `embedText(text, "passage")` for writes, `embedText(text, "query")` for reads [code: src/store.ts:170, 281] — the standard BGE-M3 trick.
- **Vector normalization on read:** `normalizeVector()` pads/truncates to expected dim if a row's vector is off-shape [code: src/store.ts:1028-1039], which is a soft failure mode rather than a hard one.

### 2.3 Type system (the schema's "ontology")

- **11 types:** `decision, fact, preference, lesson, context, observation, identity, relationship, procedure, blocker, task` [code: src/schema.ts:5-17].
- **4 priorities:** `critical, high, normal, low` [code: src/schema.ts:21-26].
- **3 statuses:** `active, archived, superseded` [code: src/schema.ts:30-34].
- **7 source types:** `conversation, observation, ingestion, compaction, correction, media, bridge` [code: src/schema.ts:38-46].
- **5 task statuses:** `pending, in_progress, blocked, done, cancelled` [code: src/schema.ts:50-56].

The type system is the most opinionated part of the design. Most other systems in §4 store everything as either "messages" or "facts"; SuperClaude pre-commits to a richer taxonomy on the assumption that retrieval downstream will be type-aware. This pays off in `loadSession` (§2.7) and `taskList`, and it's why ReasoningBank's `lesson` mapping fits cleanly (§5.1).

### 2.4 Search modes

Three modes [code: src/store.ts:274-380]:

| Mode | Mechanism | Complexity (per call) |
|---|---|---|
| `semantic` | `tbl.vectorSearch(queryVector).limit(k×3).filter(status='active')` then post-filter on scope/type/priority/topics | **O(log N) ANN** via LanceDB index + **O(k×d)** post-scoring; d=1024 |
| `structured` | `tbl.query().where(status='active' AND ...).limit(k×3)` then JSON-string topic post-filter | **O(N_filtered)** — scans rows matching where clause |
| `hybrid` | `Promise.all([semanticSearch, structuredSearch])` → merge into Map by id, structured-only hits get score×0.6 | **2× semantic cost + O(k)** merge |

**Hybrid scoring detail:** semantic results keep their (1 / (1 + distance)) score; structured-only hits enter at 0.6 of their score=1.0 [code: src/store.ts:367-380]. This is a fixed discount, not learned. A row that is structurally a perfect match but semantically off-distribution gets boosted into top-k at 0.6 weight — useful for the "I tagged this with topic=X, find it" case.

### 2.5 Dedup-on-write

This is the single most architecturally distinctive piece [code: src/store.ts:164-233].

```
for (input):
  candidates = WHERE type=input.type AND scope=input.scope AND status='active' LIMIT 100
  if candidates empty:
    create new
  else:
    queryVec = embed(input.content, "passage")
    best = argmax cosine(queryVec, c.vector) over candidates
    if best.score > 0.92: skip + bump access_count of best   [DEDUP]
    elif best.score > 0.75: create new + mark best.status='superseded' + best.superseded_by=newId   [SUPERSEDE]
    else: create new
```

**Hidden complexity cost:** the dedup path **bypasses the ANN index**. It does a `LIMIT 100` SQL filter then full O(N×d) cosine scan in JS. For a (type, scope) bucket with 100 active rows: 100 × 1024 = ~100K float operations per save. Current scale is fine. At 10K rows per (type, scope) it would slow to 10M ops/save (~50ms in JS) and the `LIMIT 100` would silently start dropping candidates, producing false-positive "no duplicate" results and a slowly fragmenting store.

**The supersede mechanism is the architectural prize.** Every change creates a new row with `supersedes = oldId` and marks `oldId.status='superseded', superseded_by=newId` [code: src/store.ts:188-223, 763-769]. The old row is *not deleted*. You get a built-in audit trail for free. ReasoningBank's "supersede, don't duplicate" protocol (in CLAUDE.md, derived from arXiv:2509.25140) maps directly onto this. None of the other systems in §4 do this by default — Zep's bi-temporal model is the closest analog.

### 2.6 Lifecycle

`memory_compact` runs four operations [code: src/lifecycle.ts via index.ts:246-258]:

1. **Expire** — `context` and `blocker` types have TTLs (`computeExpiry` at src/store.ts:801), past which they're archived.
2. **Promote** — high-access-frequency rows can be promoted in priority.
3. **Demote** — stale rows can be demoted.
4. **Purge** — old `superseded` and `archived` rows past retention are hard-deleted.

`access_count` is bumped on retrieval, not on `loadSession` (the comment at src/store.ts:493-495 explicitly notes that bulk-bumping on session load creates self-reinforcing loops keeping stale rows promoted).

### 2.7 Session load — the tiered context primer

`loadSession(scope?)` returns up to 38 rows in this priority order [code: src/store.ts:425-498]:

1. **Tier 0** — Up to 2 `context`-typed rows with topic `session-log` (the "last session handoff" rows).
2. **Tier 1** — Up to 15 `critical` priority, non-task, active rows.
3. **Tier 2** — Up to 10 `high` priority, non-task, scoped to (global ∪ scope) rows.
4. **Tier 3** — Up to 8 active `task` rows, most-recently-updated first.
5. **Tier 4** — Up to 3 non-session-log `context` rows.

This is the most important UX detail. The tiering is what makes "type a slash command and have the agent know what's going on" actually work. Most systems in §4 have no equivalent — they expose `search` and let the agent figure out what to load.

### 2.8 Transport

- **HTTP:** Hono server at `http://127.0.0.1:18800/mcp` for Claude Code [config: settings.json].
- **Stdio:** Direct stdio transport for Cursor [code: src/index.ts:324-326].
- **Why both:** the SOP at `~/.claude/memory/SOP-superclaude-memory-mcp.md` explains: Claude Code inside Cursor was hitting `MCP error -32000` because `node` wasn't on PATH in the extension host. The HTTP server sidesteps this by making the server its own process.

### 2.9 Tool surface — 10 MCP tools

`memory_save, memory_search, memory_update, memory_delete, memory_load_session, memory_stats, memory_health, memory_compact, memory_task_list, memory_task_update` [code: src/index.ts:52-321].

The split between `memory_*` and `memory_task_*` reflects the type system's privileging of `task` as a sub-domain with its own dedicated structured-data field (`task_data` Zod schema at src/schema.ts:62-78).

### 2.10 Concurrency

- `touchQueue` is a single async-serialized queue for `accessed_at`/`access_count` updates [code: src/store.ts:127, 848-855]. This prevents lost-update races on concurrent reads of the same row.
- `initPromise` deduplicates concurrent `init()` calls [code: src/store.ts:133-141].
- `tbl.update({where, valuesSql})` is preferred over read-modify-write for the touch path; falls back to upsert on older LanceDB versions [code: src/store.ts:775-799]. Honest engineering.

### 2.11 Bridge

`pmm-bridge.ts` exists in the source tree (listed in §10 sources). I didn't deep-read it for this review, but its presence is significant: it's prior art for "another system feeding memories into this store". When you eventually design the Codex memory system, the bridge pattern (rather than a new MCP) is one valid architectural option.

---

## §3 Property-based taxonomy

Categories like "graph systems vs vector systems" are loose. Properties are testable. The 12 properties below each have a measurement protocol — for any system, a third party can extract the value from public source.

| # | Property | Values | Measurement protocol |
|---|---|---|---|
| 1 | **Persistence model** | ephemeral / session / cross-session / temporal-versioned | Does state survive (a) process restart, (b) session boundary, (c) does it record valid_from/valid_to per fact? |
| 2 | **Consistency model** | eventual / monotonic-read / linearizable | Can two concurrent reads observe non-monotonic state? Read source for the write path. |
| 3 | **Representation substrate** | dense-vector / graph / SQL / hybrid / markdown-first | Inspect storage layer schema. |
| 4 | **Dedup policy** | none / threshold-similarity / structural-key / human-curated | Read the save/add path. Note threshold if applicable. |
| 5 | **Lifecycle policy** | none / TTL / access-frequency / human / learned | Read the lifecycle/maintenance code. Note what triggers state change. |
| 6 | **Multi-tenancy** | single-user / RBAC / capability-based / shared-with-trust-policy | Read access control source. |
| 7 | **Trust model** | blind / source-tagged / signed / consensus | What fields capture provenance? Can a write be rejected based on provenance? |
| 8 | **Provenance** | untracked / source-session-tagged / fully-versioned | Per row, can you recover (a) who wrote it, (b) when, (c) what produced it, (d) what it superseded? |
| 9 | **Adversarial robustness** | undefined / input-validated / formally-verified | Test: SQL-injection on filter inputs; embedding manipulation; oversize content. |
| 10 | **Read cost** | O-notation + units | Read path big-O over N (total rows), k (top-k), d (embedding dim). Include index assumptions. |
| 11 | **Write cost** | O-notation + units | Write path big-O. Include dedup cost separately. |
| 12 | **Distillation policy** | none / human / prompt-enforced / learned | Does the system *transform* trajectories into compact memories, or just store raw? |

These 12 are not exhaustive but they're sufficient to distinguish every system in §4. A 13th worth flagging: **semantic-update semantics** — what happens when a new write *contradicts* an existing fact rather than just resembling it. Most systems treat contradiction as another vector. Zep's bi-temporal model handles it by closing the validity window on the old fact. SuperClaude's `supersedes` chain handles it correctly *only when* the new and old rows are semantically close enough to trigger supersession (cosine > 0.75) — otherwise the contradiction lives silently. Worth a property #13 in a future revision.

---

## §4 Comparison matrix

Conventions: each cell is `value [tier]` where tier is `[v]`/`[d]`/`[s]` for `[verified]`/`[doc-verified]`/`[survey-only]`. Failure mode column lists the most plausible architectural failure under adversarial or scale-stress input.

### 4.1 Core comparison (properties 1–6)

| System | Persistence | Consistency | Representation | Dedup | Lifecycle | Multi-tenancy |
|---|---|---|---|---|---|---|
| **SuperClaude** | cross-session [v] | monotonic-read via supersede chain [v] | dense-vector + structured columns [v] | threshold-similarity, 0.92/0.75 dual [v] | TTL + access-frequency + manual compact [v] | single-user [v] |
| **GBrain** | cross-session, git+DB [d] | eventual (git is async-synced) [d] | markdown-first + pgvector + typed graph [d] | suspected-contradictions surfaced, not auto-merged [d] | cron enrichment + soft-delete on git rm [d] | shared-with-trust-policy (per-remote: rw/ro/deny) [d] |
| **Mem0** | cross-session [d] | eventual [d] | hybrid vector+keyword+entity [d] | single-pass ADD-only extraction [d] | none documented [s] | actor-tagged (user_id, agent_id) [d] |
| **Letta / MemGPT** | cross-session [s] | monotonic [s] | tiered: core + archival + recall; "MemFS" git-tracked [d] | LLM-driven self-edits [s] | tier-promotion via LLM decisions [s] | single-agent [s] |
| **Zep / Graphiti** | temporal-versioned [d] | bi-temporal (valid_from/valid_to) [d] | typed knowledge graph + vector [d] | fact-edge invalidation on contradiction [d] | edge invalidation; no TTL documented [d] | per-user graphs + thread scoping [d] |
| **Cognee** | cross-session [s] | eventual [s] | knowledge graph over chunks [s] | graph-merge on entity match [s] | none documented [s] | air-gapped enterprise mode [s] |
| **A-MEM** | cross-session [s] | eventual [s] | Zettelkasten-style auto-linked notes [s] | link-formation on similarity [s] | not documented [s] | single-user [s] |
| **Memori** | cross-session [s] | linearizable (SQL) [s] | SQL-first, no vector DB [s] | structural-key (presumed) [s] | not documented [s] | single-user [s] |
| **OMEGA** | cross-session [d] | linearizable (SQLite) [d] | SQLite + ONNX embeddings; hybrid semantic+BM25 [d] | not documented [s] | not documented [s] | Pro tier: multi-agent coord [d] |
| **Hindsight** | cross-session [s] | eventual [s] | retain/recall/reflect framework [d via paper:arXiv:2512.12818] | not documented in survey [s] | reflective consolidation [d] | single-user [s] |
| **MIRIX** | cross-session [d via paper:arXiv:2507.07957] | eventual [s] | multi-agent shared memory [d] | not documented [s] | not documented [s] | **multi-agent first-class** [d] |

### 4.2 Trust, provenance, robustness, cost, distillation (properties 7–12)

| System | Trust | Provenance | Adv. robustness | Read cost | Write cost | Distillation |
|---|---|---|---|---|---|---|
| **SuperClaude** | source-tagged (`source_type, source_session`) [v] | fully-versioned (supersede chain + timestamps) [v] | input-validated: SAFE_STRING_REGEX, escapeStr; no auth on HTTP listener [v] | O(log N) ANN + O(k·d) [v] | O(N_cand · d) dedup scan + O(d) embed; **N_cand capped at 100** [v] | none — distillation lives in CLAUDE.md prompts, not code [v] |
| **GBrain** | source-tagged + git-history [d] | git-history backed, plus typed edges [d] | OAuth + DCR + scope-gated [d] | hybrid: vector + BM25 + RRF, sub-linear [d] | put + auto-link (zero-LLM) [d] | none — emergent via graph linking [d] |
| **Mem0** | actor-tagged (user_id/agent_id), inferences flagged [d] | metadata-rich [d] | docs reference enterprise encryption [d] | multi-signal: semantic + keyword + entity [d] | single-pass ADD-only (no read-before-write) [d] | extracted facts, not strategies [d] |
| **Letta** | tiered context [s] | MemFS = git-tracked [d] | not documented [s] | tier-aware, LLM-decided [s] | LLM-driven edits [s] | **strong: agent self-edits core memory** [d] |
| **Zep / Graphiti** | typed entities w/ properties [d] | bi-temporal: valid_from/valid_to per edge [d] | API-level auth [d] | graph.search + thread.get_user_context [d] | entity extraction + edge ingestion [d] | partial: fact extraction; not strategy [d] |
| **Cognee** | source-tagged [s] | KG node lineage [s] | air-gap is the security story [s] | KG traversal + vector [s] | KG construction is the write cost [s] | KG-as-distillation [s] |
| **A-MEM** | per-note [s] | timestamp + links [s] | not documented [s] | similarity-walk over links [s] | append + auto-link [s] | emergent via Zettelkasten links [s] |
| **Memori** | row-level [s] | SQL constraints + audit cols [s] | SQL injection surface [s] | SQL indexes [s] | SQL insert [s] | none [s] |
| **OMEGA** | row-level + AES-256 encrypted-at-rest [d] | not detailed in survey [s] | local-only + encryption [d] | hybrid semantic+BM25 top-5..10 [d] | not detailed [s] | "category-tuned answer prompts" [d] — partial |
| **Hindsight** | not documented [s] | reflective entries log past interactions [d] | not documented [s] | reflective retrieval [d] | retain phase [d] | **strong: reflect phase** [d] |
| **MIRIX** | per-agent attribution [d] | not detailed [s] | not detailed [s] | multi-agent shared lookup [d] | shared write w/ attribution [d] | shared distillation across agents [d] |

### 4.3 Failure modes — what breaks each system under adversarial input

| System | Most plausible failure mode | Trigger |
|---|---|---|
| **SuperClaude** | Dedup false-negative + silent store fragmentation | Single (type, scope) bucket exceeds ~100 active rows. `findCandidates LIMIT 100` silently drops candidates → "no duplicate" responses become wrong → store fragments [code: src/store.ts:735]. |
| **SuperClaude** | HTTP listener has no auth — anything on localhost can read/write | `127.0.0.1:18800` is open to any process on the box. A malicious local process can `memory_save` poison rows or `memory_search` exfiltrate. Acceptable risk for single-user dev box; not acceptable for shared host. |
| **GBrain** | Contradictions accumulate because they're surfaced, not resolved | Cron flags conflicts; user/agent must resolve. At scale, the conflict queue can grow unbounded. |
| **Mem0** | Stale fact returned as current | Mem0's own production-gaps post identifies "memory staleness: high-relevance facts become confidently wrong after user circumstances change" as unresolved. |
| **Letta** | LLM self-edits can corrupt core memory | The strength (LLM-driven memory editing) is also the failure mode — a hallucinated edit can pollute the source-of-truth context. |
| **Zep** | Fact invalidation depends on contradiction detection accuracy | If new write doesn't trigger the contradiction rule, old fact stays valid → conflicting facts coexist with overlapping validity windows. |
| **Mem0/Letta/Zep** | Cross-session identity resolution breaks | Mem0's own analysis flags this as unsolved across the field — multi-device or anonymous sessions defeat `user_id` keying. |
| **OMEGA** | "Category-tuned answer prompts" implies prompt-rigid retrieval | Out-of-distribution queries (no matching category) may fall back to weaker default. |

### 4.4 Reading the matrix

**SuperClaude's distinctive profile is the (provenance × dedup × tiered-load) triple.** None of the other systems combines all three. GBrain wins on multi-tenancy + trust policy. Zep wins on temporal modeling. Letta wins on distillation (self-editing). Mem0 wins on raw retrieval performance per benchmark. MIRIX wins on multi-agent first-class. OMEGA wins on LongMemEval score with local-only constraints. SuperClaude wins on **audit trail integrity** — the supersede chain is unmatched.

The honest gap: SuperClaude has *no* multi-agent semantics, *no* temporal validity, *no* enforced distillation, and *no* trust model beyond "you ran the process". For a single-user developer assistant, these are acceptable. For the ACS project (Claude↔Codex with red-team and 2nd-opinion patterns), they become blockers.

---

## §5 Latest research findings — primary sources only

### 5.1 ReasoningBank ([arXiv:2509.25140](https://arxiv.org/abs/2509.25140), Google Research, Sept 2025)

**Memory item schema:** Each entry has exactly **three fields: `title, description, content`** [paper: §3.2 + Figure 2]. Lightweight strategy capsules, not fact stores.

**Closed-loop process:** distill → retrieve → interact → induce → consolidate. The agent retrieves relevant items before interacting, then constructs new items from both successful and failed trajectories [paper: §3.2].

**Failure trajectories matter.** Ablation in §5.2 shows that incorporating failure trajectories for memory induction is a measurable contributor to performance — not just a nice-to-have. Most existing memory systems store only successes.

**MaTTS — Memory-aware Test-Time Scaling:**

- **Parallel (k trajectories):** Generate k independent rollouts of the same task. Self-contrast across them curates reliable memory [paper: §3.3 + Figure 3b]. "Reliable" because what's invariant across k attempts is likelier to be a real pattern than a single-run artifact.
- **Sequential (k refinement steps):** Iteratively self-refine within a single trajectory. The *intermediate notes* generated during self-refinement become memory signals — they capture corrections and insights that don't survive into the final solution [paper: §3.3 + Figure 3c, citing Madaan et al. 2023 self-refine].

**Headline numbers:** +34.2% relative effectiveness, −16% interaction steps on WebArena-Admin vs. memory-free baseline [paper: abstract].

**Mapping to SuperClaude:**

| ReasoningBank | SuperClaude analog | Gap |
|---|---|---|
| `{title, description, content}` schema | `type='lesson'` + `content` (free-form) + `topics[]` | SC content is unstructured; the 3-field schema is more retrievable |
| Closed-loop distillation in code | Distillation lives in CLAUDE.md prompt only | **No code enforcement** — user can save raw conversation text as a "lesson" and nothing rejects it |
| Failure trajectories used | `source_type: 'correction'` exists | Schema field exists; pipeline doesn't enforce its use |
| MaTTS Parallel/Sequential | None | Out of scope for a memory MCP — needs orchestrator support |
| Self-judge before save | None | Honor system via CLAUDE.md ritual |

### 5.2 Memory survey ([arXiv:2603.07670](https://arxiv.org/abs/2603.07670), March 2026)

**Taxonomy:** Three dimensions — *temporal scope* × *representational substrate* × *control policy*. Memory operations form a **write-manage-read loop** coupled with perception and action.

**Five open frontiers** the survey calls out:

1. **Continual consolidation** — how to merge experiences over time without catastrophic forgetting or unbounded growth.
2. **Causally grounded retrieval** — retrieving not by similarity but by causal relevance.
3. **Trustworthy reflection** — self-judgments that don't compound errors.
4. **Learned forgetting** — policies for what to forget, learned from outcomes.
5. **Multimodal embodied memory** — beyond text, including action traces and sensor data.

**SuperClaude's standing on each frontier:**

1. Continual consolidation: partial via `memory_compact` (mechanism present, policy is heuristic).
2. Causally grounded retrieval: not addressed.
3. Trustworthy reflection: deferred to CLAUDE.md prompts.
4. Learned forgetting: not addressed — TTLs are hand-set per type.
5. Multimodal: schema has `media_*` fields, no pipeline.

### 5.3 Security survey ([arXiv:2604.16548](https://arxiv.org/abs/2604.16548), April 2026)

**Attack surface taxonomy:** write-time integrity, retrieve-time integrity, confidentiality, availability, store/forget, benign-persistence. The survey notes literature concentrates on write/retrieve integrity; the other four are sparsely studied.

**Benign-persistence** is the most interesting one for SuperClaude — facts that *were* true become silently stale and are returned as authoritative. This is what Mem0's production-gaps post calls out as unsolved across the field, and what Zep's bi-temporal model partially addresses.

### 5.4 Multi-agent memory papers

- **MIRIX** ([arXiv:2507.07957](https://arxiv.org/abs/2507.07957), July 2025) — multi-agent memory sharing as a first-class primitive. Relevant if Codex memory needs to read SC memory.
- **G-Memory** ([arXiv:2506.07398](https://arxiv.org/abs/2506.07398), June 2025) — hierarchical structures capturing agent interactions in multi-agent setups. Hierarchy could map onto SC's scope ("global" vs "project:X" vs eventually "agent:claude"/"agent:codex").
- **Nemori** ([arXiv:2508.03341](https://arxiv.org/abs/2508.03341), September 2025) — cognitive-science-inspired self-organization.
- **O-Mem** ([arXiv:2511.13593](https://arxiv.org/abs/2511.13593), November 2025) — unified factual + experiential + working memory.
- **Hindsight** ([arXiv:2512.12818](https://arxiv.org/abs/2512.12818), December 2025) — retain/recall/reflect framework. 91.4% on LongMemEval per third-party leaderboard [survey: omegamax.co/compare].
- **EverMemOS** ([arXiv:2601.02163](https://arxiv.org/abs/2601.02163), January 2026) — OS-level memory abstraction.
- **MAGMA** ([arXiv:2601.03236](https://arxiv.org/abs/2601.03236), January 2026) — multi-graph framework.

### 5.5 Inter-agent protocols (relevant for future ACS work, out of scope here)

Google's **A2A protocol** ([protocol overview, survey-only](https://www.gravitee.io/blog/googles-agent-to-agent-a2a-and-anthropics-model-context-protocol-mcp)) is now at v1.0 with 150+ orgs, complementary to MCP: MCP = agent↔tool, A2A = agent↔agent. Uses HTTP + SSE + JSON-RPC 2.0 + Agent Cards for capability discovery. MCP/A2A/ACP are under Linux Foundation. When the ACS sub-project is scoped, A2A is the obvious wire-protocol reference rather than reinventing JSON-RPC.

---

## §6 Threat model applied to SuperClaude

Applying the [arXiv:2604.16548](https://arxiv.org/abs/2604.16548) attack-surface taxonomy directly to SuperClaude as deployed today:

| Surface | SuperClaude exposure | Existing mitigation | Residual risk |
|---|---|---|---|
| **Write-time integrity (poisoning)** | Any caller of `memory_save` can plant content. No content validation beyond Zod type+length checks [code: src/index.ts:55-67]. | None on content; type system constrains structure not meaning. | **High.** A compromised tool or hostile MCP client can inject `priority: 'critical'` content that biases every `loadSession` afterward. |
| **Retrieve-time integrity (injection)** | Query text goes to embedder, no further sanitization. Filter values pass `SAFE_STRING_REGEX` + `escapeStr` [code: src/store.ts:24-34]. | SQL-injection protection on filters. None on query semantics. | **Low for SQL injection, medium for context manipulation.** An attacker who can plant a row can also craft it to surface for specific future queries. |
| **Confidentiality** | All rows readable by any caller of `memory_search`. `visibility: 'private' \| 'shared'` field exists but is not enforced anywhere I can grep in the source [code: src/store.ts grep `visibility`]. | Visibility column exists; **enforcement missing**. | **High if multi-tenant.** Today: single-user, low. With Codex memory + ACS sharing: critical. |
| **Availability** | LanceDB single-table, single-machine. No replication. | None. | **Low for personal use, total loss possible on disk corruption.** Backups would need to be a separate workflow. |
| **Store/forget violations** | `softDelete` only flips `status='archived'`; row content remains [code: src/store.ts:419-421]. Hard purge only via `memory_compact` of old `superseded/archived` rows. | Compaction exists; no GDPR-grade hard-delete-on-demand. | **Medium.** A `memory_delete` does not actually delete content. |
| **Benign-persistence (stale-as-current)** | TTL exists for `context` and `blocker` only [code: src/store.ts:801-807]. Decisions, facts, lessons, preferences have *no expiry*. | None. | **High over time.** A `decision` made in 2024 is returned with equal authority in 2026. |

**The headline residual risk** is the combination of (no auth on HTTP listener) × (visibility field is unenforced). For single-user single-machine use, this is fine because the threat model assumes the user is the only caller. The instant a second agent (Codex) or a second host joins, this becomes a P0.

---

## §7 Strengths — property deltas vs field median

These are SC's *wins*, expressed as deltas vs the median of the 11-system comparison set in §4. "Vs median" means "more than 5 of the 10 other systems lack this property at the level SC implements it".

1. **Provenance: fully-versioned with audit trail.** Median: source-tagged only. SC's `supersedes ↔ superseded_by` chain plus 4 timestamps + `source_session` + `source_type` is richer than 9/10 comparators. Only Zep's bi-temporal edges + GBrain's git history come close.
2. **Tiered session-load primitive.** Median: none — `search` is the only entry point. SC's 5-tier `loadSession` is unique to SC and OpenClaw. It's the difference between "agent has to guess what to load" and "agent gets the right context primed automatically".
3. **Type-as-ontology.** Median: messages + facts. SC's 11 types pre-commit to a taxonomy that pays off in `loadSession` and `task` handling. Most comparators store everything as one shape and try to type-classify at read time.
4. **Dual-threshold dedup with supersession.** Median: single-threshold or none. SC's (0.92 skip / 0.75 supersede / else create) is the most nuanced policy in the set and produces the audit trail as a side effect.
5. **Local-first sovereignty with semantic search.** Median: vendor cloud or local-only-no-vector. SC is fully local with full semantic search. Only OMEGA, Memori (no vector), and self-hosted GBrain match.
6. **Lazy init + serialized touch queue.** Median: synchronous init. SC's lazy-init pattern (avoiding MCP startup timeout) and async-serialized access-bump queue are honest production engineering most comparators don't bother with.
7. **ReasoningBank-protocol-compatible schema.** Median: not compatible. SC's `source_type: 'correction'` and supersede mechanics map onto ReasoningBank's rituals naturally. The mapping isn't enforced in code but the schema doesn't fight you.

---

## §8 Gaps — property deltas vs field leaders

These are SC's *losses*. Each names the leader and quantifies the delta.

1. **No temporal validity model.** Leader: Zep/Graphiti — `valid_from`/`valid_to` per fact edge with explicit invalidation on contradiction [doc: help.getzep.com/concepts]. SC delta: facts have one `created_at`, no notion of "valid until when". Benign-persistence risk follows directly.
2. **No multi-tenancy or trust policy.** Leader: GBrain — per-remote `read-write`/`read-only`/`deny` policy + OAuth + scope-gated access [doc: gstack USING_GBRAIN_WITH_GSTACK.md]. SC delta: zero access control beyond process boundary. Blocker for ACS work.
3. **No multi-agent shared memory semantics.** Leader: MIRIX [paper: arXiv:2507.07957]. SC delta: `visibility: 'shared'` field exists but no enforcement, no read scoping, no agent attribution. Blocker for Claude↔Codex.
4. **No code-enforced distillation.** Leader: Letta (self-editing core memory) or ReasoningBank (closed-loop ritual). SC delta: distillation lives in CLAUDE.md prose. A `memory_save({type:'lesson', content:'i did the thing'})` is accepted regardless of whether it follows the TITLE/APPLICABILITY/GUARDRAIL schema.
5. **No graph or causal retrieval.** Leader: GBrain (typed edges + multi-hop), Cognee (KG-first), Zep (graph). SC delta: pure dense-vector + scalar filters. Cannot answer "what decisions depend on this fact?" without manual `relationship`-type rows.
6. **No MaTTS / test-time scaling.** Leader: ReasoningBank [paper: arXiv:2509.25140]. SC delta: requires orchestrator support outside the MCP, so this is an *architecture-level* gap not a memory-system bug — but the +34.2% effectiveness from MaTTS is real and unrealized.
7. **No published benchmark score.** Leader: OMEGA 95.4% on LongMemEval [survey: omegamax.co/compare]. SC delta: never run. Without this, performance claims are unfalsifiable.
8. **HTTP listener has no auth.** Leader: GBrain (OAuth + DCR + scope-gated). SC delta: anything on localhost can read/write. Acceptable for current use; not for multi-host.
9. **No GDPR-grade hard delete.** Leader: Mem0 (explicit retention/deletion APIs documented). SC delta: `memory_delete` is soft-only.
10. **No contradiction surfacing.** Leader: GBrain (`eval suspected-contradictions` job). SC delta: contradictory rows silently coexist unless their cosine > 0.75.

---

## §9 Decision-theoretic opportunity menu

These are *options*, not commitments. Framing: each entry = {property delta} × {impl cost} × {expected value} × {risk}. Use as scoping input when designing the Codex memory system (current sub-project C) and the ACS channel (current sub-project D). Order is rough-merit, not strict.

| # | Option | Property delta | Impl cost | Expected value | Risk |
|---|---|---|---|---|---|
| **O1** | Enforce `visibility: 'private'\|'shared'` in `memory_search` based on caller identity | Closes #2 (multi-tenancy) at the read path | 1 dev-day in `store.ts` + caller-identity protocol on MCP/HTTP | **High** for any multi-agent future; **necessary** for ACS | New auth surface to maintain. |
| **O2** | Add `valid_from` / `valid_to` columns + contradiction-on-supersede logic | Closes #1 (temporal validity), partially closes #6 (benign-persistence) | 2–3 dev-days: schema migration + write-path update; harder if existing rows need defaults | **High** for any system tracking "facts about the world" rather than just lessons | Schema migration needs care — existing rows. |
| **O3** | Add code-enforced ReasoningBank distillation: reject `type='lesson'` saves that don't pass a schema validator (TITLE/APPLICABILITY/GUARDRAIL/STRATEGY) | Closes #4 (enforced distillation) | 0.5 dev-day: Zod sub-schema for lesson content + reject path | **High** signal-to-noise; aligns code with CLAUDE.md protocol | Friction for legitimate one-off lessons that don't fit schema — may need bypass flag. |
| **O4** | Add typed-edge table for `relationship` rows; expose `memory_graph_query` MCP tool | Partial close of #5 (graph) — gets multi-hop without full KG migration | 3–4 dev-days: new table + traversal + tool | **Medium-High** for understanding decision chains; **High** if Codex needs to ask "what does Claude know about X?" | LanceDB doesn't have native graph indices; adjacency table is workable but not fast. |
| **O5** | Implement contradiction surfacing as a `memory_compact` step | Closes #10, partial close of #6 | 1 dev-day: pairwise cosine pass on candidate clusters + flagged-status | **Medium**; visibility without auto-resolution is the cheap+correct first step | False-positive contradiction flags consume attention. |
| **O6** | Run LongMemEval against SC; publish score | Closes #7 | 2–3 dev-days: harness + dataset loader + score reporting | **High strategic** — without a number, no claim is testable | Score might be embarrassing. (That's also the value — falsifiable claim.) |
| **O7** | Add HTTP auth (bearer token from env var; OAuth deferred) | Closes #8 minimally | 0.5 dev-day: middleware in Hono server | **High** the moment a second host joins | Token rotation story needed. |
| **O8** | Implement hard-delete via `memory_purge({id})` separate from soft `memory_delete` | Closes #9 | 0.5 dev-day | **Medium** today, **High** if PII handling ever matters | Lose audit trail for the deleted row — by design. |
| **O9** | Index the dedup hot path: replace `LIMIT 100 + JS cosine` with an ANN call constrained to (type, scope) | Closes the hidden scaling cliff in §2.5 | 1–2 dev-days: see LanceDB filter+vector combined query | **Low today** (under threshold), **High at 10K+ rows per scope** | Need to verify LanceDB combined-filter-vector behavior. |
| **O10** | Add MaTTS-Parallel as a session protocol: run k=3 attempts, self-contrast, distill what's stable | Closes #6 (MaTTS) | 5+ dev-days, mostly *outside* the MCP (orchestrator-level) | **High** based on ReasoningBank's +34.2% number | Requires orchestrator changes — bigger than a memory upgrade. |
| **O11** | Add `agent_id` column + scope `agent:<name>` semantics; index on it | Foundation for #3 (multi-agent) | 1 dev-day: schema + scope conventions | **Critical-path** if Codex memory and SC memory ever read each other | Schema migration. |
| **O12** | Replace HTTP-on-localhost with a Unix-domain socket or named pipe | Partial close of #8 — removes network surface entirely | 1 dev-day + Hono adapter | **Medium**: stronger isolation than auth tokens | Cursor/IDE clients may not support socket transport easily. |

**For sub-project C (Codex memory) scoping**, the relevant subset of this menu is: O1, O2, O7, O11 are *necessary* for the Codex memory to interoperate with SC memory. O3 is *recommended* if Codex is meant to follow the same ReasoningBank rituals. O6 is *recommended* so both systems can be A/B tested.

**For sub-project D (ACS channel) scoping**, O1, O7, O11 are *prerequisites*. The channel itself is a separate design (A2A protocol is the obvious reference per §5.5), but the memory layer it bridges between must have agent-identity and access control before the channel can be safely designed.

---

## §10 Limitations & replicability recipe

### What this review CANNOT establish

1. **Empirical performance.** No benchmark was run. Cited LongMemEval scores are vendor self-reports per [survey: omegamax.co/compare], not third-party measurement. Mem0's own [State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026) reports 94.4 self-evaluated.
2. **Real failure rates.** §6 threat model is architectural, not empirical. No fuzzing, no red-team.
3. **Cost.** No load test, no token-cost-per-1K-operations comparison.
4. **Quality of LLM outputs downstream.** The whole point of memory is to improve future task performance; this review compares architectures, not outcomes.

### Source tier audit

`[verified]` claims (read source in this session):
- All of §2 (SuperClaude architecture) — `src/{index,store,schema,config,lifecycle}.ts`
- ReasoningBank schema and MaTTS structure — [arXiv:2509.25140 §3.2, §3.3, Figures 2-3](https://arxiv.org/abs/2509.25140)

`[doc-verified]` claims (read official docs):
- GBrain architecture — [github.com/garrytan/gbrain](https://github.com/garrytan/gbrain) README + [USING_GBRAIN_WITH_GSTACK.md](https://github.com/garrytan/gstack/blob/main/USING_GBRAIN_WITH_GSTACK.md)
- Zep concepts — [help.getzep.com/concepts](https://help.getzep.com/concepts)
- OMEGA comparison — [omegamax.co/compare](https://omegamax.co/compare)
- Mem0 architecture and gaps — [mem0.ai/blog/state-of-ai-agent-memory-2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- Memory survey taxonomy — [arXiv:2603.07670](https://arxiv.org/abs/2603.07670)
- Security survey — [arXiv:2604.16548](https://arxiv.org/abs/2604.16548)
- A2A protocol overview — [gravitee.io blog](https://www.gravitee.io/blog/googles-agent-to-agent-a2a-and-anthropics-model-context-protocol-mcp)
- Recent paper list — [Shichun-Liu/Agent-Memory-Paper-List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)

`[survey-only]` claims (third-party summaries only):
- Letta architecture details — only [doc-verified] from MemFS mention; tiered model details are `[s]`
- Cognee, A-MEM, Memori specifics — only via [atlan.com/know/best-ai-agent-memory-frameworks-2026/](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/) and [omegamax.co/compare](https://omegamax.co/compare)
- MIRIX, G-Memory, Hindsight, Nemori, O-Mem, EverMemOS, MAGMA — read titles + abstracts from [Shichun-Liu/Agent-Memory-Paper-List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List); not full papers
- Hindsight 91.4% benchmark score — [survey: omegamax.co/compare], not independent
- LongMemEval scores generally — third-party leaderboard, not independent runs

### Replicability recipe

A third party can reproduce every cell in §4 within ~4 hours by:
1. Cloning `C:\Users\7amma\.claude\mcp-servers\superclaude-memory` and reading `src/{index,store,schema,config,lifecycle}.ts`.
2. Reading each comparator's documentation URL above.
3. For papers, reading the arXiv abstract + §3 of each cited paper.
4. Promoting `[survey-only]` cells to `[doc-verified]` by reading the relevant project's docs directly.

### Suggested ratchets

If anyone (likely future-me) wants to make this doc materially stronger:
1. **Run LongMemEval against SuperClaude** (O6 above). Pins a number.
2. **Read Letta source** (`github.com/letta-ai/letta`) to upgrade its row from `[survey-only]` to `[verified]`.
3. **Read MIRIX paper §3-4** to verify multi-agent specifics.
4. **Read GBrain `src/core/engine.ts`** to enumerate the actual 47 BrainEngine operations rather than the inferred grouping in §4.

---

## Appendix — Cross-cutting findings

These are observations that didn't fit cleanly under any single section but bear on future scoping.

**A. The schema is doing more work than the search modes.** SC's distinctiveness is more in *what it stores* (11 types, supersede chain, source tags, task substructure) than *how it searches* (vanilla hybrid). When designing the Codex memory, copying the search modes is easy; copying the *schema discipline* is the harder part to get right.

**B. The CLAUDE.md ReasoningBank protocol is the actual distillation layer.** The MCP doesn't enforce it. This is a working pattern (the prose is the policy, the schema is the substrate) but it's *fragile* — a different agent or a different prompt can bypass it. Code-level enforcement (O3) hardens this for free.

**C. `pmm-bridge.ts` is the prior-art template for cross-system memory.** Worth a deep-read before designing how Codex memory talks to SC memory. The bridge pattern (translate-and-forward) may beat a brand-new MCP for the simplest version of multi-agent shared memory.

**D. The A2A protocol exists and is governed by Linux Foundation.** When the ACS channel is scoped, the question "do we invent a wire protocol or adopt A2A" should not be left implicit. A2A handles capability discovery (Agent Cards), authentication, and streaming via SSE — three things you would otherwise re-invent.

**E. The biggest single risk in SC's current architecture is the dedup hot path's `LIMIT 100`** [code: src/store.ts:735]. Below 100 active rows per (type, scope), behavior is correct. Above, dedup silently degrades and the store fragments invisibly. This is the single-day fix on the menu with the highest payoff (O9).

---

*End of review.*
