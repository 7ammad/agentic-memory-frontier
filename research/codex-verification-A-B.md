# A. Verification of v3

## A.Check 1 Coverage
- Q1 telemetry: ANSWERED — evidence: v3 §1 Q1 says “Adopt Codex’s 12-metric list verbatim” and adds WARN/CRITICAL thresholds plus compact-time cross-monitoring.
- Q2 TTL: ANSWERED — evidence: v3 §1 Q2 provides a per-type policy table and says the schema needs `valid_from`, `valid_to`, and `review_after`.
- Q3 agent_id: ANSWERED — evidence: v3 §1 Q3 says `agent_id = sha256(ed25519_pub)` is canonical, with `agent_alias` for display and capabilities separate.
- Q4 escalation: ANSWERED — evidence: v3 §1 Q4 says Jeffreys is the “measurement primitive” and Codex’s risk wrapper is the policy layer, then gives escalation rules.
- Q5 reward: ANSWERED — evidence: v3 §1 Q5 adopts the per-protocol reward decomposition and adds worst-decile / downstream-correctness constraints.
- No false “answered” claim found for the five v2 open questions.

## A.Check 2 Internal consistency
- Minor tension, not fatal: v3 §3 migration playbook says O11/O2 rollback can “drop column, restore from snapshot,” but later correctly says all migrations dry-run against a copy and rollback immediately on acceptance failure. For LanceDB, “drop column” is weak wording and should be removed.
- No direct contradiction found between §7 strengths and §8 gaps from the prior review logic: SC can have strong provenance/tiered-load while still lacking temporal validity, auth, visibility enforcement, and benchmarks.
- §5 backlog priorities do not conflict with §6 threat-model judgments. O1/O11/telemetry/migration are P0; O7/O9 are P1. That is defensible, though B later improves O7 ordering.

## A.Check 3 Grounding
- v3 has zero `[code: ...]` cites, so the requested 5 v3 code-cite spot checks are not possible.
- No stale `[code:]` cite found in v3 because none exist.
- `[mit12:]` cites skipped per instruction.

## A.Check 4 Missing artifacts
- Source manifest gap: v3 §7 is explicitly “v3 additions to v2’s manifest,” not a full final manifest. If v3 is meant to stand alone, it omits earlier URL/paper/doc sources from v1/v2, including GBrain, Zep, Mem0, OMEGA, A2A blog, arXiv survey/security papers, Agent-Memory-Paper-List, Atlan, and comparator-source tiers.
- Migration playbook exists, but should remove “drop column” language and consistently say snapshot restore / table-copy rollback for LanceDB.

# B. Verification of v0.3 spec

## B.Check 1 Coverage
- O1: IN SPEC — Phase 1, visibility enforcement at read paths.
- O2 refined: IN SPEC — Phase 3, `valid_from` / `valid_to` / `review_after` plus `memory_review_stale`.
- O7: IN SPEC — Phase 1, moved earlier into auth + caller identity.
- O9: IN SPEC — Phase 4, combined-filter ANN dedup hot path.
- O11: IN SPEC — Phase 1, `agent_id`, `agent_alias`, `capabilities`.
- telemetry: IN SPEC — Phase 2, `memory_health` telemetry contract and thresholds.
- migration playbook: IN SPEC — Phase 0 plus per-phase migration / dry-run / rollback / gates.
- Scope creep: no P2/P3 O-items are included for implementation. `agent_alias`, `capabilities`, and `memory_review_stale` are not scope creep; they are implied by v3 Q3/Q2.

## B.Check 2 Internal consistency
- Real contradiction: Phase 3 schema says `review_after` constraint is `0 or > now at write time`, but Phase 3 backfill intentionally sets `review_after = created_at + N days`. For old rows, that can be in the past, and `memory_review_stale` depends on past review dates. Patch the constraint to allow backfill/persisted stale-review rows.
- Minor terminology mismatch: spec repeatedly says “12-metric telemetry contract,” but Phase 2 acceptance says 13 metrics because it splits the active-row cross-check into separate gauges. Not fatal, but normalize wording to “12-metric contract plus cross-check gauges” or “13 health fields.”
- Overclaim: §3 gotcha #4 says “Phase 1 acceptance test explicitly preserves these rows” for malformed vectors. Phase 1 acceptance test does not list that assertion. Vector mismatch preservation appears in Phase 2/4, not Phase 1.
- §1 architecture summary and §2 phase plan mostly match: schema deltas in §1 are added in Phase 1 + Phase 3; read-path filter in §1 matches Phase 1 + Phase 3 + Phase 4.

## B.Check 3 Grounding
- `src/schema.ts:84-108`: PASS — `MemoryRow` has the listed existing row fields and no `agent_id`.
- `src/schema.ts:112-137`: PASS — `seedMemoryRow()` carries all current LanceDB columns.
- `src/config.ts:23-28, 52-58`: PASS — config has PMM `agentId` only and no HTTP bearer token.
- `src/http-server.ts:343-421`: PASS — `/health`, `/notify`, and `/mcp` are routed without bearer auth checks.
- `src/store.ts:425-455`: PASS — `loadSession()` direct queries start there and do not filter visibility.
- `src/notify-handler.ts:22-31` + `118-127`: PASS — inbound schema has `agent_id`; `store.save()` call drops it.
- `src/pmm-bridge.ts:36-55` + `214-231`: PASS — PMM row has `agent_id`; `mapRow()` omits it.
- `src/store.ts:730-760`: PASS — dedup fetches `LIMIT 100` then loops JS cosine.
- No wrong/stale code cite found in the sampled B cites.

## B.Check 4 Missing artifacts
- Phase 0: snapshot yes; dry-run env/server yes; rollback marked “none required” because no changes; acceptance script yes. Missing exact MCP `memory_health` capture command/script, but spec explicitly names it as a Phase 0 deliverable.
- Phase 1: snapshot yes; dry-run yes; rollback yes; acceptance command yes; feature flags yes.
- Phase 2: snapshot not required, acceptable for metrics-only; dry-run yes; rollback yes; acceptance command yes; no feature flag, acceptable.
- Phase 3: fresh snapshot yes; dry-run yes; rollback yes; acceptance command yes; feature flag yes.
- Phase 4: fresh snapshot yes; dry-run/replay yes; rollback yes; acceptance command yes; feature flag yes; LanceDB combined-filter ANN dependency check yes.
- Missing/weak item: Phase 0 should name the actual `memory_health` capture script path or command, not only describe it.

# C. PATCHES NEEDED
1. v0.3 spec / Phase 3 schema delta: change `review_after` constraint from “0 or > now at write time” to allow persisted/backfilled stale dates; otherwise `memory_review_stale` contradicts the migration model.
2. v0.3 spec / §3 gotcha #4: remove or move “Phase 1 acceptance test explicitly preserves these rows.” Add vector-shape preservation to Phase 1 acceptance, or say Phase 2/4 cover it.
3. v0.3 spec / telemetry wording: reconcile “12-metric contract” vs “13 metrics.” Pick one naming convention and use it consistently.
4. v0.3 spec / Phase 0 acceptance: add the exact canonical MCP `memory_health` capture command or script path.
5. v3 / §7 Source manifest: either rename it clearly as “v3-only additions” or append the earlier v1/v2 URL/paper/doc source manifest so the final synthesis is standalone.
6. v3 / §3 migration playbook: remove “drop column” rollback wording for LanceDB; make snapshot/table restore the sole rollback primitive.

# D. READINESS VERDICT
- A: PATCH-FIRST — content answers the five questions, but the final source manifest / rollback wording should be patched before treating v3 as the durable final artifact.
- B: PATCH-FIRST — scope is correct and code grounding passes, but the `review_after` constraint contradiction and Phase 1 vector-preservation overclaim need patching before sub-project C starts.
- Both are close, but not clean READY until the small patches above are made.