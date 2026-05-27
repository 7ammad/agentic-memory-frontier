**A1 Telemetry**

Track the dedup path as a first-class production subsystem, not just `memory_save` latency.

Metrics:
- `memory_dedup_bucket_active_rows{type,scope}`: exact count of active rows per `(type, scope)`.
- `memory_dedup_candidate_limit_hit{type,scope}`: boolean/count when active rows > 100.
- `memory_dedup_candidates_returned`: histogram, especially 0, 1-20, 21-80, 81-100.
- `memory_dedup_best_cosine`: histogram with buckets around `0.70`, `0.75`, `0.85`, `0.92`, `0.97`.
- `memory_dedup_decision_total{decision=skip|supersede|create}`.
- `memory_dedup_latency_ms`: p50/p95/p99, split into candidate query, embedding, cosine scan, write/update.
- `memory_save_latency_ms`: end-to-end.
- `memory_duplicate_fragmentation`: count of active pairs/clusters above cosine `0.92` that were not deduped.
- `memory_supersede_chain_length`: histogram by latest row.
- `memory_active_rows_total{type,scope,status}`.
- `memory_vector_shape_mismatch_total`: because soft vector normalization can hide corruption.
- `memory_compact_archived_total{reason=expired|demoted|purged}`.

Alerts:
- Warning: any `(type, scope)` bucket > 80 active rows.
- Critical: any bucket > 100 active rows, because correctness silently degrades, not just performance.
- Warning: `candidate_limit_hit > 0` for 3 consecutive compaction/save windows.
- Critical: active duplicate cluster count above cosine `0.92` grows by > 10% day-over-day.
- Warning: `memory_save_latency_ms p95 > 250ms` for 15 min.
- Critical: `memory_save_latency_ms p99 > 1s` for 15 min.
- Warning: `create / (skip + supersede + create)` ratio jumps 2x baseline for a stable bucket.
- Critical: embedding failures or vector-shape mismatches > 0.1% of saves.

The key alert is not latency. It is candidate truncation. A fast wrong dedup path is worse than a slow one because it quietly fragments memory.

**A2 TTL Per Type**

Use different staleness models. TTL is only one mechanism; some types need validity windows, review dates, or supersession, not expiry.

- `context`: short TTL. Default 7-14 days. Session logs maybe 3-7 days unless promoted.
- `blocker`: short active TTL with escalation. Default 14-30 days; after that mark stale, not silently active.
- `task`: lifecycle-driven, not pure TTL. Active until done/cancelled; stale review after 7 days no update; archive done tasks after 30-90 days.
- `observation`: medium TTL. Default 30-90 days unless cited by a decision/lesson. Observations are often local snapshots.
- `fact`: no blind TTL. Needs `valid_from`, optional `valid_to`, source, confidence, and review interval. World/vendor facts need aggressive review; stable personal facts do not.
- `decision`: no TTL, but requires supersession and review trigger. Review after project boundary, major dependency change, or 90-180 days.
- `preference`: decays unless reinforced. Review after 180 days; promote if repeatedly confirmed. Preferences drift.
- `lesson`: long-lived but not immortal. Review after 180-365 days or when contradicted by later failures. Lessons should have applicability conditions.
- `procedure`: versioned. Stale on tool/version/env change. Review after 90-180 days if not executed recently.
- `identity`: durable, no normal TTL, but high-friction updates and periodic review. This is identity/control-plane memory.
- `relationship`: durable but reviewable. Review after 180-365 days or on contradictory interaction evidence.

The missing primitive is `review_after`, not just `expires_at`. Expiry is right for transient state. Review is right for durable-but-drift-prone memory.

**A3 agent_id Scheme**

Pick public-key fingerprint as the canonical identity.

Use:
- `agent_id = sha256(ed25519_public_key)` or equivalent stable fingerprint.
- `agent_alias = claude | codex | superbrembo | cursor-agent | human:hammad` as display metadata.
- Capabilities as separate grants/tokens, not identity.
- Optional signed messages for ACS writes.
- Backfill legacy SC rows as `agent_alias=claude`, `agent_id=legacy-claude-local` or a generated migration principal.

Why:
- Free string: spoofable and eventually messy.
- Enum: fine for UI, bad as security identity and brittle when agents multiply.
- Capability token: authorizes an action but is not a stable historical author.
- DID: likely overkill unless crossing machines/orgs.
- Public-key fingerprint: stable, local-first, auditable, compatible with future signing, cheap to implement.

Do not overload `scope` for identity. Scope answers “where does this apply?” Agent ID answers “who asserted this?”

**A4 ACS Escalation Threshold**

Use a risk-weighted disagreement function, not one fixed threshold.

Represent each agent output as:
- recommendation
- confidence `c`
- evidence quality `e`
- reversibility `r`
- impact `i`
- domain criticality `k`
- uncertainty/unknowns `u`

Compute:

```text
risk = max(i, k) * r
disagreement = semantic_conflict(recommendation_a, recommendation_b)
confidence_gap = abs(c_a - c_b)
evidence_gap = abs(e_a - e_b)

escalate_score =
  0.35 * disagreement +
  0.25 * risk +
  0.15 * max(u_a, u_b) +
  0.15 * (1 - max(e_a, e_b)) +
  0.10 * close_call_penalty
```

Rules:
- Auto-resolve if `risk < 0.3`, `disagreement < 0.3`, and one agent has materially better evidence.
- Escalate if `risk >= 0.7` and `disagreement >= 0.25`.
- Escalate if `disagreement >= 0.6` regardless of risk.
- Escalate if both agents are low-confidence: `max(c_a, c_b) < 0.55`.
- Escalate if the proposed action is destructive, external, irreversible, legal/commercial, security-sensitive, or touches secrets.
- Auto-pick higher-confidence result only when confidence gap `>= 0.25` and evidence quality gap supports it.
- Otherwise run one bounded reconciliation round, then escalate if still unresolved.

For Hammad’s workflows, I would bias escalation toward human only when the decision is irreversible or user-facing. For routine implementation disagreements, force one reconciliation pass first.

**A5 Mixed-Motive Reward**

Do not reward agents for “winning.” Reward protocol outcomes.

2nd opinion:
- Claude reward: produce a clear claim, assumptions, and evidence.
- Codex reward: find material errors, missing cases, bad assumptions, or confirm with independent reasoning.
- Shared reward: user gets a better decision with less uncertainty.
- Gamed by: performative contrarianism, shallow agreement, overconfident “independent” restatement, citing irrelevant theory.

Red-team:
- Builder reward: correct implementation, minimal regression, honest known risks.
- Red-team reward: valid high-severity findings, reproducible evidence, no noise.
- Shared reward: shipped safer system.
- Gamed by: issue inflation, nitpicking, blocking forever, severity exaggeration, builder hiding uncertainty.

Hand-off:
- Sender reward: complete, compact, executable state transfer.
- Receiver reward: successful continuation with minimal reread.
- Shared reward: no lost context, no duplicated work.
- Gamed by: verbose dumps, fake completeness, burying blockers, receiver blaming prior agent instead of validating.

Second-opinion/red-team/handoff protocols need different scoring:
- Reward calibrated uncertainty.
- Reward evidence density.
- Penalize unsupported certainty.
- Penalize unnecessary escalation.
- Penalize silent auto-resolution after material disagreement.
- Track downstream correction rate: how often did the accepted agent turn out wrong?

The most dangerous gaming pattern is agents optimizing for looking useful to the user instead of preserving truth. That creates false confidence, inflated findings, and premature consensus.

**B Pushback On V2**

V2 leans too hard on the Dec-POMDP/MARL analogy as if it is structurally exact.

It is useful framing, but the actual SC system is not learning a policy, estimating a value function, or optimizing a formally specified reward. It is a hand-coded memory service used by prompted LLM agents. Calling `LIMIT 100` an `I_max` bound is insightful; saying the structure is “the same” risks laundering a design metaphor into a proof.

Better wording: MIT-12 gives a disciplined analogy and vocabulary for bounded coordination. It does not justify the actual thresholds, protocols, or priorities without telemetry.

**C Missing From V2**

Migration and rollback strategy.

The review recommends `agent_id`, visibility enforcement, temporal validity, hard delete, and possibly indexed dedup. Those are schema and semantics changes to a live personal memory store. V2 should include:
- migration order
- backfill policy
- compatibility with old rows
- dry-run validators
- rollback path
- integrity checks before/after migration
- snapshot/backup requirement
- “do not corrupt Hammad’s memory” acceptance tests

For this system, data migration risk is not plumbing. It is the blast radius.

**D ACS: A2A vs MCP Elicitation vs Custom JSON-RPC**

Pick A2A as the outer protocol, with MCP kept for tool access.

Reason:
- MCP is agent-to-tool. It is not the right abstraction for peer agents negotiating tasks, handoffs, disagreement, capabilities, and attribution.
- MCP elicitation is useful when a tool needs user input. It is not a full inter-agent protocol.
- Custom JSON-RPC is tempting but will recreate capability discovery, auth, streaming, task state, message schemas, and versioning.
- A2A already maps to the problem shape: agent cards, capability discovery, task/message exchange, streaming, and agent-to-agent semantics.

Recommended architecture:
- A2A for Claude-Codex communication.
- MCP for each agent’s tools and memory server.
- Public-key `agent_id` for ACS identity.
- Capability grants for what one agent may ask another to do.
- Shared memory writes only through explicit, attributed messages.
- No direct “both agents write everything into one store” as v1. That is communication-by-side-effect and will be hard to debug.

Start with a small A2A subset: `second_opinion.request`, `review.findings`, `handoff.state`, `clarification.request`, `decision.recorded`. Keep it boring and inspectable.