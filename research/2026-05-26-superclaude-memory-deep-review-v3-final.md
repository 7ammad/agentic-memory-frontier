# SuperClaude Memory Review — v3 Final Synthesis

**Author:** Claude (with Codex CLI counsel + 12 MIT-12 corpus queries)
**Date:** 2026-05-26
**Companion to:** [v1](2026-05-26-superclaude-memory-deep-review.md) (generic-rigor) and [v2](2026-05-26-superclaude-memory-deep-review-v2-mit12.md) (MIT-12 protocol applied)
**Counsel input:** [codex-counsel-output.md](codex-counsel-output.md) — full unedited 1373-word response from `codex exec` with `model_reasoning_effort=medium`, 134K tokens, 4 tool calls
**This doc's purpose:** Answer the 5 OPEN QUESTIONS from v2 (Hammad was right — MIT-12 had material on all of them), address Codex's pushback and missing item, deliver final answer.

---

## §0 What changed since v2

Hammad's call was correct: my "MIT-12 cannot answer this" framing in v2 was lazy on 4 of the 5 open questions. New evidence in this session:

| Source | Evidence | What it changes |
|---|---|---|
| 5 new MIT-12 lens queries (`08-telemetry` → `12-reward`) | 30 newly-routed corpus chunks across book-03, book-08, book-11, book-12 | All 5 open questions get corpus grounding |
| Codex CLI consult (model_reasoning_effort=medium) | 1373-word counsel response, 134K tokens, read both v1+v2 + verified 2 specific claims against SC source | Independent answers + 1 pushback + 1 missing item + ACS protocol pick |
| Direct cross-check | Murphy book-11 chunk-0053 (Jeffreys scale on Bayes factor), Reddi book-03 chunk-0524 (telemetry thresholds + defense-in-depth) | The canonical textbook primitives, not just heuristics |

Verdict on v2's OPEN QUESTIONS: 1 was genuinely beyond MIT-12 (Q1 needs SC's *actual* telemetry, which is empirical), the other 4 are answerable. v3 below.

---

## §1 Final answers to the 5 questions

Each answer has three parts: **MIT-12 grounding** (what the corpus says), **Codex counsel** (what the independent consult said), **Final judgment** (the call for SC / Codex memory / ACS).

### Q1 — Telemetry / observability

**MIT-12 grounding** [`mit12: book-03-chunk-0524 pp.1568-1570`]: Reddi's *Machine Learning Systems* names telemetry as a first-class system property, with concrete reference thresholds: *"alerts typically triggering when accuracy drops >5% or latency exceeds 200ms"*. The framing principle: *"A robust system is not one that avoids all errors, but one that fails visibly, controllably, and safely."* [`mit12: book-03-chunk-0390 pp.1180-1182`] adds **defense-in-depth monitoring**: redundant metric collectors, local persistent logging when central systems fail, cross-monitoring (monitor the monitor), heartbeat checks, separate PagerDuty fallback channels.

**Codex counsel**: 12 specific metrics (`memory_dedup_bucket_active_rows`, `memory_dedup_candidate_limit_hit`, `memory_dedup_candidates_returned` histogram, `memory_dedup_best_cosine` histogram with buckets around the 0.92/0.75 thresholds, decision counters, latency p50/p95/p99 split per phase, `memory_duplicate_fragmentation`, `memory_supersede_chain_length`, vector-shape-mismatch counter, compact reason counter) + 8 alerts. Codex's killer insight: *"The key alert is not latency. It is candidate truncation. A fast wrong dedup path is worse than a slow one because it quietly fragments memory."*

**Final judgment for SuperClaude**:

1. **Adopt Codex's 12-metric list verbatim** as the SC telemetry contract. Implement as `memory_health` extensions, not as a separate system.
2. **Bind alert thresholds to Reddi-style anchors**:
   - WARN at `bucket_active_rows > 80` (per Codex), CRITICAL at `> 100` (the actual `LIMIT 100`).
   - WARN at `save_latency_p95 > 250ms` (above Reddi's 200ms reference for ML inference).
   - CRITICAL at `vector_shape_mismatch_total / saves > 0.001` (per Codex; aligns with Reddi's "fail visibly").
3. **Add defense-in-depth that Codex missed**: a second metric collector that runs at compact time and re-derives `active_rows_total` from the table itself, not from cached counters. If the two diverge by >1%, alert. This is Reddi's cross-monitoring pattern applied to memory accounting.
4. **Implementation cost**: 2 dev-days for metrics + 1 day for the cross-check; surfaces in existing `memory_health` tool output.

**This is the most useful single addition to SC** — it makes the §2.5 hidden dedup cliff visible before it bites.

---

### Q2 — TTL policy per memory-type

**MIT-12 grounding** [`mit12: book-12-chunk-0219 pp.792-796`]: Murphy on time-varying distributions — concept drift is a structural property, not an accident, and *requires* drift-detection or per-distribution lifetime models. [`mit12: book-03-chunk-0437 pp.1311-1313`]: Reddi on benign-persistence — facts have varying lifetimes; a uniform retention policy is wrong by construction.

**Codex counsel**: Per-type model below, plus a structural insight I missed:

> *"The missing primitive is `review_after`, not just `expires_at`. Expiry is right for transient state. Review is right for durable-but-drift-prone memory."*

**Final judgment — per-type policy** (Codex's table, with corpus-grounded refinement):

| Type | Policy | Default | Mechanism |
|---|---|---|---|
| `context` | TTL | 7-14 days; session-log 3-7d unless promoted | `expires_at` |
| `blocker` | TTL + escalation | 14-30d, then stale (not silently active) | `expires_at` + status flip |
| `task` | Lifecycle-driven | active until done/cancelled; archive done after 30-90d | `task_status` transitions |
| `observation` | Medium TTL with citation override | 30-90d unless cited by a decision/lesson | `expires_at` + citation-check |
| `fact` | Validity window + review | no blind TTL; needs `valid_from`/`valid_to` + `review_after` | new columns |
| `decision` | Review + supersession trigger | review after project boundary OR 90-180d | `review_after` |
| `preference` | Decay + reinforcement | review after 180d; promote if confirmed | `review_after` + access-frequency |
| `lesson` | Long-lived with applicability conditions | review after 180-365d OR when contradicted | `review_after` + supersede |
| `procedure` | Versioned | stale on tool/version/env change | `procedure_version` |
| `identity` | Durable, high-friction | no TTL, periodic review only | `review_after` |
| `relationship` | Durable reviewable | 180-365d OR contradictory interaction | `review_after` |

**New schema additions needed** (this becomes O2 in v2's opportunity menu, refined):
- `valid_from: number` (defaults to `created_at`)
- `valid_to: number | null` (NULL = currently valid)
- `review_after: number | null` (NULL = no review needed; non-NULL = surface in `memory_review` tool when past)
- Existing `expires_at` semantics unchanged.

**Implementation cost**: 2-3 dev-days schema + 1 day for `memory_review_stale` tool. Codex's `review_after` primitive is the key idea — it lets you express "this might still be true but go check" without the brutality of TTL on a `decision`.

---

### Q3 — agent_id scheme

**MIT-12 grounding** [`mit12: book-03-chunk-0465 pp.1390-1392 + book-03-chunk-0471 pp.1405-1408`]: Reddi on identity, authentication, and provenance in ML systems — identity must be cryptographically anchored to survive any compromise of the application layer.

**Codex counsel** (decisive):

> *"Pick public-key fingerprint as the canonical identity. `agent_id = sha256(ed25519_public_key)` ... `agent_alias = claude | codex | superbrembo | cursor-agent | human:hammad` as display metadata. Capabilities as separate grants/tokens, not identity. Optional signed messages for ACS writes."*

Codex's rejection of alternatives is sharp:
- Free string: spoofable
- Enum: fine for UI, bad for security, brittle as agents multiply
- Capability token: authorizes an action but is not a stable historical author
- DID: overkill unless crossing machines/orgs
- **Public-key fingerprint**: stable, local-first, auditable, compatible with future signing, cheap

**Final judgment**:

1. **Adopt Codex's scheme**: `agent_id = sha256(ed25519_pub)` as the canonical column; `agent_alias` for display.
2. **Anchor to SPIFFE precedent** (industry standard for service identity using SVIDs with cryptographic provenance). If you want a richer identity framework later, SPIFFE/SPIRE is the obvious upgrade path; the sha256 fingerprint is forward-compatible with SVID URIs.
3. **Backfill**: existing SC rows get `agent_id = "legacy-claude-local"` + `agent_alias = "claude"`. Keypair generation per agent at first run.
4. **Capabilities live in a separate column** (`capabilities: string[]` or normalized into a join table). Codex's "do not overload `scope` for identity" is right — `scope` answers "where does this apply?", `agent_id` answers "who asserted this?", `capabilities` answers "what is this caller allowed to do?".

**Implementation cost**: 1 dev-day schema + keygen + backfill. Signing is deferred to ACS work (not needed for single-host SC).

---

### Q4 — ACS disagreement escalation threshold

**MIT-12 grounding** [`mit12: book-11-chunk-0053 pp.209-213`]: Murphy gives the canonical answer. **Jeffreys scale of evidence for interpreting Bayes factors**:

| Bayes factor BF₁,₀ | Interpretation |
|---|---|
| BF > 100 | Decisive evidence for M₁ |
| BF > 10 | Strong evidence for M₁ |
| 3 < BF < 10 | Moderate evidence for M₁ |
| 1 < BF < 3 | Weak evidence for M₁ |
| ⅓ < BF < 1 | Weak evidence for M₀ |
| 1/10 < BF < ⅓ | Moderate evidence for M₀ |
| BF < 1/10 | Strong evidence for M₀ |
| BF < 1/100 | Decisive evidence for M₀ |

[`mit12: book-12-chunk-0325 pp.1149-1153`]: Decision under uncertainty — when both M₀ and M₁ have meaningful posterior mass, the optimal policy is *defer* (gather more info or escalate), not pick. This is the **decision-theoretic justification for escalation as a third action**.

**Codex counsel**: Risk-weighted scoring function over 7 inputs (confidence, evidence quality, reversibility, impact, criticality, uncertainty, disagreement) with specific thresholds (risk<0.3 auto-resolve, risk≥0.7 escalate, disagreement≥0.6 always escalate, low-confidence both<0.55 escalate, irreversible/destructive/security always escalate).

**Final judgment** — combine Jeffreys (for the disagreement primitive) with Codex's risk wrapper (for the policy layer):

```python
# Primitive: Jeffreys-scale interpretation of disagreement
def disagreement_strength(claude_conf, codex_conf, semantic_conflict):
    # M0 = "agents agree" (semantic_conflict ≈ 0)
    # M1 = "agents disagree" (semantic_conflict ≈ 1)
    bayes_factor = (semantic_conflict * max(claude_conf, codex_conf)) / \
                   max(1 - semantic_conflict, 0.01)
    if bayes_factor > 100: return "decisive"
    if bayes_factor > 10:  return "strong"
    if bayes_factor > 3:   return "moderate"
    return "weak"

# Policy: risk-weighted escalation (per Codex)
def should_escalate(claim_a, claim_b, context):
    # ALWAYS escalate (hard rules)
    if context.irreversible: return True
    if context.security_sensitive: return True
    if context.touches_secrets: return True

    # Jeffreys-grounded escalation
    strength = disagreement_strength(claim_a.confidence, claim_b.confidence, semantic_conflict(claim_a, claim_b))
    if strength == "decisive": return True
    if strength == "strong" and context.risk >= 0.3: return True
    if strength == "moderate" and context.risk >= 0.7: return True

    # Both-low-confidence rule (Codex)
    if max(claim_a.confidence, claim_b.confidence) < 0.55: return True

    # Otherwise: one bounded reconciliation round, then re-evaluate
    return False  # auto-attempt reconciliation
```

The Jeffreys scale is the **measurement primitive** (how much disagreement?), Codex's risk wrapper is the **policy** (when does disagreement matter enough to escalate?). Without Jeffreys you're picking thresholds arbitrarily. Without Codex's risk wrapper, you escalate every weak disagreement which trains the user to ignore escalations.

**Implementation cost**: Disagreement primitive is straightforward; calibrating `semantic_conflict()` is the harder problem (semantic similarity isn't the same as semantic conflict — two statements can be similar but contradictory). Defer to ACS sub-project; bias toward sensitivity over specificity initially.

---

### Q5 — Mixed-motive reward structure for ACS

**MIT-12 grounding** [`mit12: book-08-chunk-0008 pp.39-42`]: General-sum reward is "among the most challenging tasks in MARL" — mixed-motive scenarios. [`mit12: book-07-chunk-0091 pp.333-336`]: Distributional RL on **risk-sensitive reward** — optimizing for the mean is wrong when worst-case outcomes have asymmetric cost; need to reward calibrated tail behavior. [`mit12: book-08-chunk-0083 pp.284-288`]: Multi-agent credit assignment requires per-agent value decomposition; rewarding the joint outcome alone produces free-riding.

**Codex counsel** (the per-protocol decomposition is the heart of this):

| Protocol | Agent A reward | Agent B reward | Shared reward | Gamed by |
|---|---|---|---|---|
| **2nd opinion** | clear claim + assumptions + evidence | find material errors / missing cases / bad assumptions, or independently confirm | better user decision with less uncertainty | performative contrarianism; shallow agreement; overconfident restatement; citing irrelevant theory |
| **Red-team** | correct impl + minimal regression + honest known risks | valid high-severity findings + reproducible + no noise | shipped safer system | issue inflation; nitpicking; blocking forever; severity exaggeration; builder hiding uncertainty |
| **Hand-off** | complete + compact + executable state transfer | successful continuation with minimal re-read | no lost context, no duplicated work | verbose dumps; fake completeness; burying blockers; receiver blaming prior agent instead of validating |

Plus shared scoring across all three: **reward calibrated uncertainty, reward evidence density, penalize unsupported certainty, penalize unnecessary escalation, penalize silent auto-resolution after material disagreement, track downstream correction rate**.

**Final judgment**:

1. **Adopt Codex's per-protocol decomposition verbatim** as the ACS reward contract.
2. **Add a distributional metric** per book-07: don't just track average disagreement-resolution outcome; track the **worst-decile** outcome. If 10% of "auto-resolved" decisions turn out wrong, the auto-resolution policy is broken even if the average looks fine.
3. **Codex's most important warning**: *"The most dangerous gaming pattern is agents optimizing for looking useful to the user instead of preserving truth. That creates false confidence, inflated findings, and premature consensus."* This must be the dominant design constraint. Concretely: **reward downstream correctness, not real-time praise**. A protocol where users immediately rate "good answer" trains both agents to optimize for user-pleasing, not truth.

**Implementation cost**: Reward structure is a design artifact, not code. Bake into ACS protocol spec when sub-project D opens.

---

## §2 Codex's pushback — accepted and integrated

Codex's pushback:

> *"V2 leans too hard on the Dec-POMDP/MARL analogy as if it is structurally exact. It is useful framing, but the actual SC system is not learning a policy, estimating a value function, or optimizing a formally specified reward. It is a hand-coded memory service used by prompted LLM agents. Calling LIMIT 100 an `I_max` bound is insightful; saying the structure is 'the same' risks laundering a design metaphor into a proof. Better wording: MIT-12 gives a disciplined analogy and vocabulary for bounded coordination. It does not justify the actual thresholds, protocols, or priorities without telemetry."*

**Accepted.** v2's §1 INFERENCE says: *"This is not a vague analogy — it is the same structure."* That's overclaim. The right framing: *"Dec-POMDP gives the vocabulary and the principled question (what's your κ_max policy?). It does not justify the answer (LIMIT 100, ORDER BY arbitrary). The answer needs empirical validation via telemetry (Q1)."*

If v2 is consulted in the future, treat the §1 framing as a useful pedagogical analogy, not a proof. The Dec-POMDP κ_max comparison is *suggestive*, not *exact*.

---

## §3 Codex's missing item — Migration and Rollback (new section, was absent from v2)

Codex's catch was sharp: v2 recommends 12 schema-altering changes (`agent_id`, `valid_from/valid_to`, `review_after`, `visibility` enforcement, hard-delete, contradiction surfacing, typed edges, ...) without a migration playbook. For a live personal memory store with months of accumulated rows, that's malpractice.

### Migration playbook (gated by O11 first, then O1, O2 in order)

| Step | What | Pre-check | Post-check | Rollback |
|---|---|---|---|---|
| 1 | **Snapshot the LanceDB store** before any change | `du -sh ~/.claude/memory/lancedb` (size sanity); `memory_health` returns clean | snapshot exists at `~/.claude/memory/lancedb.snapshot-2026-05-26/` | `mv lancedb.snapshot-2026-05-26 lancedb` |
| 2 | **Add `agent_id` column** (O11), backfill to `"legacy-claude-local"` | row count matches expected (run `memory_stats`) | `memory_stats` shows same row count; new column present with backfill values | restore from Phase 0 snapshot (LanceDB schema evolution is snapshot-based — `ALTER TABLE DROP COLUMN` is unsafe on a rewritten table; do not attempt partial column deletion) |
| 3 | **Enforce `visibility`** (O1) | every row has `visibility ∈ {private, shared}` (default `private` for legacy) | `memory_search` returns no rows the caller shouldn't see (dry-run with synthetic non-owner) | revert search-path code, no schema change needed |
| 4 | **Add `valid_from / valid_to / review_after`** (O2 refined) | per-type defaults defined (see §1 Q2) | spot-check 10 random rows from each type | restore from snapshot taken before this step (same rationale as step 2 — snapshot-based, not column-drop) |
| 5 | **HTTP auth** (O7) | bearer token env var set | failed token requests return 401, succeed return 200 | remove auth middleware |
| 6 | **Migrate dedup hot path** (O9) | run new dedup against historical writes; record disagreements with old | disagreement rate < 0.5% on identical-input writes; investigated each | restore old `findCandidates` path |

### Acceptance test ("Do not corrupt Hammad's memory")

Before any migration is declared "done":

```
1. Random-sample 100 active rows from before-migration snapshot
2. For each, verify content is recoverable after migration (verbatim match)
3. Run memory_search on 20 well-known queries (e.g., "anti-slop", "MIT12 protocol", "openclaw")
   — top result must be identical to pre-migration top result
4. memory_load_session must return 5 tiers in the same order as pre-migration
5. memory_health must return clean (no orphan supersedes/superseded_by)
```

If any of these fail: rollback immediately, investigate, do not declare migrated.

### Dry-run requirement

Every migration above runs first against a **copy** of the live store, not the live store. The copy is the snapshot from step 1. Migration of the live store only happens after the dry-run + acceptance tests pass on the copy.

---

## §4 ACS protocol — final decision

Per Codex's recommendation, anchored by the §11 design principles from v2:

### Decision: **A2A outer + MCP inner**

| Layer | Protocol | Purpose | Rationale |
|---|---|---|---|
| Tool access (per-agent) | **MCP** | Claude reads tools, Codex reads tools, each agent's memory MCP | MCP is the dominant agent-to-tool protocol; 97M downloads; under Linux Foundation |
| Agent-to-agent communication | **A2A v1.0** | second-opinion requests, red-team challenges, hand-offs, clarifications, decision-recording | A2A is the right abstraction shape: Agent Cards for capability discovery, JSON-RPC 2.0 + SSE for streaming, designed for peer agents with own reasoning |

**Rejected alternatives**:
- **MCP elicitation only**: MCP is agent-to-tool; treating Claude as a "tool" for Codex (or vice versa) loses the peer-agent semantics. Elicitation handles "tool needs user input"; it does not handle "agent challenges agent's reasoning".
- **Custom JSON-RPC**: tempting but reinvents capability discovery, auth, streaming, task state, message schemas, versioning. A2A already exists and is governed.

### Starter message subset (5 messages, from Codex)

Begin with this minimal vocabulary, add only when needed:

| Message | From → To | Payload |
|---|---|---|
| `second_opinion.request` | Claude → Codex (or reverse) | `{topic, claim, evidence, requested_focus}` |
| `review.findings` | Reviewer → Author | `{findings[], severity, reproduction, false_positive_risk}` |
| `handoff.state` | Sender → Receiver | `{task_state, completed_steps, open_questions, recommended_next}` |
| `clarification.request` | Either → Either | `{question, context, blocking}` |
| `decision.recorded` | Either → both memories | `{decision, options_considered, reversibility, agent_id, signed?}` |

Boring and inspectable beats clever. Add `red_team.challenge`, `red_team.defense`, etc. only when first 5 are validated in practice.

### Auth & identity (per §1 Q3)

- Each agent generates ed25519 keypair on first run
- `agent_id = sha256(pub_key)`
- A2A Agent Card advertises `agent_id` + `agent_alias` + capabilities
- ACS messages MAY be signed (defer signing until threat model demands it — for trusted-local first deployment, attribution alone is enough)
- HTTP transport behind localhost (or Unix socket per v2 O12) until a second host needs access

---

## §5 What to actually do next — ordered backlog

Combining v2's opportunity menu + Codex counsel + this v3 synthesis, the ordered priority for **SuperClaude memory upgrade** (sub-project B's pre-work):

| Priority | Item | From | Cost | Why this order |
|---|---|---|---|---|
| **P0** | O1 visibility enforcement | v2 §9, Codex Q3 | 1 dev-day | Gating for any multi-agent future |
| **P0** | O11 `agent_id` column + sha256(pk) | v2 §9, Codex Q3 | 1 dev-day | Schema foundation; can't backfill cleanly later |
| **P0** | Telemetry (Q1 final answer) | v3 §1 Q1, Codex + Reddi | 2-3 dev-days | Makes the dedup cliff visible *before* it bites |
| **P0** | Migration playbook + snapshot tooling | v3 §3 (Codex catch) | 1 dev-day | All P1+ changes depend on this existing |
| **P1** | O2 refined (`valid_from/valid_to/review_after` per type) | v3 §1 Q2, Codex's `review_after` | 3-4 dev-days | Closes benign-persistence; biggest correctness win |
| **P1** | O7 HTTP auth (bearer token from env) | v2 §9 | 0.5 dev-day | Closes the localhost-listener gap |
| **P1** | O9 index-the-dedup-hot-path | v2 §9, grounded by Q1 telemetry | 1-2 dev-days | Defer until telemetry shows you're near `LIMIT 100` |
| **P2** | O3 ReasoningBank schema enforcement for `type='lesson'` | v2 §9 | 0.5 dev-day | Hardens the CLAUDE.md protocol |
| **P2** | O5 contradiction surfacing in `memory_compact` | v2 §9 | 1 dev-day | Hygiene improvement |
| **P2** | O6 run LongMemEval, publish score | v2 §9 | 2-3 dev-days | Strategic — number > no number |
| **P3** | O4 typed-edge table for `relationship` rows | v2 §9 | 3-4 dev-days | Graph capability — defer until specific need |
| **P3** | O8 `memory_purge` hard delete | v2 §9 | 0.5 dev-day | GDPR-class — defer until PII handling matters |
| **P3** | O12 socket-instead-of-HTTP transport | v2 §9 | 1 dev-day | Defense-in-depth; defer unless second host joins |

For **sub-project C (Codex memory)**: build on the P0+P1 SC schema. Same row shape (modulo `agent_id`-derived defaults), same dedup discipline, same lifecycle policies. Same MCP tool surface re-implemented in whatever Codex's runtime supports.

For **sub-project D (ACS)**: A2A outer + MCP inner, 5-message starter vocabulary, public-key fingerprint identity. Reward structure per §1 Q5. Escalation threshold per §1 Q4 (Jeffreys-grounded primitive + Codex risk wrapper).

---

## §6 Honest meta-note on this session

What Hammad got right by pushing back:
1. **MIT-12 had material on 4/5 "open" questions.** The corpus is dense; my "this is out of corpus" defaults were lazy.
2. **Codex as model counsel pays off.** 134K tokens of focused independent review caught the migration-strategy gap and pushed back on the Dec-POMDP overclaim — both real fixes.
3. **The pattern (corpus deep-dive + cross-model consult) is the right shape for high-stakes design work.** Both checks together caught things neither would alone.

What this session demonstrates for future SC-vs-Codex workflows:
- Either agent acting solo will miss things the other catches.
- The "consult Codex" pattern was easy to invoke (`/codex consult ...`) and fast (~2 min including reading 100KB of docs).
- The corpus dive was easy to extend (5 new queries took 2 minutes in background).
- **The expensive thing was admitting I was wrong on the framing.** The corrected v3 is materially better; the cost was one user pushback and ~10 minutes of additional reads.

This is the operating mode for the ACS once it ships: each agent should be cheap to consult, the consult should be high-bandwidth (full docs in context, not summaries), and the consulting agent should be expected to push back, not just confirm.

---

## §7 Source manifest — v3-only additions (see v2 §10 for full prior manifest)

> **Scope note**: this section lists ONLY the sources added in v3 (5 new MIT-12 queries + Codex counsel). For the full source manifest covering v1/v2 (GBrain, Zep, Mem0, OMEGA, Letta, A2A protocol, arXiv:2603.07670 survey, arXiv:2604.16548 security, arXiv:2509.25140 ReasoningBank, Agent-Memory-Paper-List, all comparator URLs and source tiers), see [v2 §10 Limitations & Methodology](2026-05-26-superclaude-memory-deep-review-v2-mit12.md). v3 is the synthesized FINAL answer; v2 is the standalone source-of-truth manifest. Treat them together as the canonical pair.


**5 new MIT-12 lens queries** (UTF-8 versions, all at `C:\Dev\research\MIT\MIT 12 Research\tools\.runtime\queries\`):
- `08-telemetry-u8.txt` (architecture lens, 6 chunks from book-03)
- `09-decay-u8.txt` (uncertainty lens, chunks from book-12, book-03, book-04)
- `10-identity-u8.txt` (multi_agent lens, chunks from book-03)
- `11-escalation-u8.txt` (uncertainty lens, chunks from book-11, book-12)
- `12-reward-u8.txt` (multi_agent lens, chunks from book-07, book-08, book-06, book-04)

**Codex CLI output**: [codex-counsel-output.md](codex-counsel-output.md) (1373 words, sections A1-A5, B, C, D verbatim)

**Specific chunks cited in this doc**:
- `book-03-chunk-0524 pp.1568-1570` — telemetry framing + "fail visibly, controllably, safely"
- `book-03-chunk-0390 pp.1180-1182` — defense-in-depth monitoring
- `book-03-chunk-0437 pp.1311-1313` — benign-persistence framing
- `book-03-chunk-0465 pp.1390-1392` + `book-03-chunk-0471 pp.1405-1408` — identity/auth/trust
- `book-11-chunk-0053 pp.209-213` — **Jeffreys scale for Bayes factors** (the key escalation primitive)
- `book-12-chunk-0219 pp.792-796` — time-varying distributions
- `book-12-chunk-0325 pp.1149-1153` — decision-under-uncertainty defer-vs-act
- `book-07-chunk-0091 pp.333-336` — risk-sensitive reward (distributional)
- `book-08-chunk-0008 pp.39-42` — general-sum reward (mixed-motive)
- `book-08-chunk-0083 pp.284-288` — multi-agent credit assignment

---

*End of v3 final synthesis.*
