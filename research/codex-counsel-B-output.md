1. **Phase 0 — Pre-Flight Snapshot And Baseline**

   Boundary: no code or schema change. Phase 0 is complete when the live LanceDB store has a restorable snapshot, current health/stat outputs are saved, and the dedup/session behavior has a baseline. Phase 1 is unlockable only if the baseline is clean enough to compare against post-migration.

   Files in `src/` change:
   - None.

   Schema delta:
   - None.

   Migration step:
   - Snapshot: copy `~/.claude/memory/lancedb` to a timestamped sibling before any write. v3 explicitly requires snapshot before schema work and dry-run against a copy first, not live store (`research/2026-05-26-superclaude-memory-deep-review-v3-final.md:212`, `:234-236`).
   - Backfill rule: none.
   - Dry-run validation: run all later migrations only against the snapshot copy first.
   - Acceptance gate: snapshot exists, size is non-zero, and current `memory_health` has no vector-dimension or reference failures. Current health already computes vector dimensions and orphan refs in `MemoryStore.getHealth()` (`store.ts:526-580`).

   Rollback path:
   - Stop the server.
   - Rename live `lancedb` to `lancedb.failed-v03-{timestamp}`.
   - Restore the Phase 0 snapshot to `lancedb`.

   Acceptance test:
   ```powershell
   # From any PowerShell
   $src="$HOME\.claude\memory\lancedb"
   $stamp=Get-Date -Format "yyyyMMdd-HHmmss"
   $dst="$HOME\.claude\memory\lancedb.snapshot-v03-$stamp"
   Copy-Item -Recurse -LiteralPath $src -Destination $dst
   Get-ChildItem -Recurse -LiteralPath $src | Measure-Object -Property Length -Sum
   Get-ChildItem -Recurse -LiteralPath $dst | Measure-Object -Property Length -Sum
   ```
   It asserts the snapshot exists and has the same byte total as the live store.

2. **Phase 1 — Migration Harness + Authenticated Caller Identity + O11/O1 Foundation**

   Boundary: this phase makes “who is calling?” and “what may they see?” explicit before adding higher-level memory semantics. Phase 1 is complete when every row has `agent_id`, `agent_alias`, and valid `visibility`, and all search/session/task paths enforce visibility from a caller context. Phase 2 is unlockable because telemetry then measures the correct security boundary, not the old open-query behavior.

   Files in `src/` change:
   - `schema.ts`: extend `MemoryRow`, `seedMemoryRow()`, `MemorySaveInput`, possibly `MemorySearchInput` with caller/debug options if needed. Current stored row shape has `visibility` but no `agent_id`/alias (`schema.ts:84-108`), and the seed row must carry every LanceDB column (`schema.ts:112-137`).
   - `config.ts`: add `auth.httpBearerToken`, `identity.agentPublicKey`, `identity.agentId`, `identity.agentAlias`. Current config has only PMM `agentId` and no HTTP auth token (`config.ts:23-28`, `:52-58`).
   - `http-server.ts`: enforce bearer auth on `/mcp` and `/notify`; map bearer token or local config to `caller_agent_id`. Current HTTP server accepts `/health`, `/notify`, and `/mcp` without auth (`http-server.ts:343-421`).
   - `index.ts` and `http-server.ts`: pass caller identity into tool handlers. Current `memory_search` calls `store.hybridSearch`/`semanticSearch`/`structuredSearch` with only user filters (`index.ts:91-110`; `http-server.ts:104-142`).
   - `store.ts`: add caller-aware filters to `save`, `semanticSearch`, `structuredSearch`, `hybridSearch`, `loadSession`, `taskList`, `update`, and touch access. Current session load queries do not filter visibility (`store.ts:425-455`), and current semantic search filters only `status = 'active'` before post-filtering (`store.ts:283-304`).
   - `notify-handler.ts`: preserve inbound `agent_id` instead of dropping it. The notify schema receives `agent_id` (`notify-handler.ts:22-31`), but `store.save()` currently receives no agent identity (`notify-handler.ts:118-127`).
   - `pmm-bridge.ts`: map PMM `agent_id` and visibility semantics into returned rows or apply shared-only policy for bridge results. PMM rows already have `agent_id` (`pmm-bridge.ts:36-55`) but `mapRow()` drops it (`pmm-bridge.ts:214-231`).

   Schema delta:
   - Add `agent_id: string`.
     - Default/backfill: `"legacy-claude-local"` for existing SC rows, per v3 (`research/...v3-final.md:100-103`, `:213`).
     - Future value: lowercase hex `sha256(ed25519_public_key)`, 64 chars.
     - Constraint in Zod/runtime: `legacy-*` or `/^[a-f0-9]{64}$/`.
   - Add `agent_alias: string`.
     - Default/backfill: `"claude"` for existing SC rows.
   - Add `capabilities: string`.
     - JSON-serialized array, default `"[]"`; v3 says capabilities must not be overloaded into `scope` (`research/...v3-final.md:100-103`).
   - Keep existing `visibility: "private" | "shared"` but enforce runtime enum on reads/writes. Existing `visibility` is only a stored field and tool input today (`schema.ts:94`, `:148`, `index.ts:61`, `:146`).
   - Index/filter expectation:
     - All read paths must apply:
       ```sql
       status = 'active'
       AND (visibility = 'shared' OR agent_id = '{caller_agent_id}')
       ```
     - Scope remains separate:
       ```sql
       AND (scope = 'global' OR scope = '{requested_scope}')
       ```
     - Do not treat `scope` as identity; v3 explicitly separates scope, agent identity, and capabilities (`research/...v3-final.md:100-103`).

   Migration step:
   - Snapshot: use Phase 0 snapshot.
   - Backfill rule:
     - If row lacks `agent_id`: `legacy-claude-local`.
     - If row lacks `agent_alias`: `claude`.
     - If row lacks `capabilities`: `"[]"`.
     - If row lacks/has invalid `visibility`: `private`, except bridge/PMM-origin rows may be `shared` if `source_type = "bridge"` and content was already exposed through notify.
   - Dry-run validation:
     - Row count unchanged from `memory_stats`; v3 makes row count preservation the O11 post-check (`research/...v3-final.md:213`).
     - Every row has valid identity fields.
     - Synthetic caller `agent_id = "test-non-owner"` sees only `visibility='shared'`.
     - Owner caller sees private legacy rows.
   - Acceptance gate:
     - `memory_search`, `memory_load_session`, and `memory_task_list` return zero private rows for synthetic non-owner.
     - `memory_load_session` preserves tier order from the baseline, because v3 names that as a migration invariant (`research/...v3-final.md:224-229`).

   Rollback path:
   - Code rollback: revert auth/caller/visibility code and restart.
   - Data rollback: restore Phase 0 snapshot. Do not attempt partial column deletion in LanceDB if rewritten files were produced; full snapshot restore is cleaner.

   Acceptance test:
   ```powershell
   pnpm test -- --run v03-identity-visibility
   ```
   It should assert:
   - saved rows include `agent_id`, `agent_alias`, `capabilities`;
   - legacy rows are backfilled;
   - `memory_search`, `memory_load_session`, and `memory_task_list` hide private rows from non-owner;
   - `/mcp` without `Authorization: Bearer $SUPERCLAUDE_MEMORY_TOKEN` returns `401`;
   - `/mcp` with the token succeeds.

3. **Phase 2 — P0 Telemetry Contract In `memory_health`**

   Boundary: Phase 2 is observability only. No behavior change except collecting and reporting metrics. It is complete when `memory_health` exposes the 12-metric contract and alert statuses, with a compact-time cross-check. Phase 3 is unlockable because validity/review migrations can then be watched for corruption and latency regression.

   Files in `src/` change:
   - `store.ts`: instrument save/dedup/search/update/load-session phases. Current dedup path is `save()` → `findCandidates()` → `findBestMatch()` (`store.ts:168-183`, `:730-760`).
   - `store.ts`: extend `MemoryHealth`; current health has row counts, vector dimensions, references, and storage metadata only (`store.ts:93-113`, `:526-580`).
   - `lifecycle.ts`: add compact-time independent recount. Current compact already scans all active rows in a single pass (`lifecycle.ts:48-101`), which is the right place for Reddi-style cross-monitoring.
   - `index.ts` and `http-server.ts`: return extended health from `memory_health`; current tool just returns `store.getHealth()` (`index.ts:230-240`; `http-server.ts:254-258`).
   - `config.ts`: add telemetry thresholds/env overrides if needed.

   Schema delta:
   - No required table column.
   - Optional local persistent telemetry log file outside LanceDB, e.g. `~/.claude/memory/telemetry.jsonl`, because Reddi’s defense-in-depth note in v3 calls for local persistent logging if central systems fail (`research/...v3-final.md:31`).
   - Add health output fields:
     - `memory_dedup_bucket_active_rows`
     - `memory_dedup_candidate_limit_hit`
     - `memory_dedup_candidates_returned`
     - `memory_dedup_best_cosine`
     - decision counters: `created`, `skipped_duplicate`, `superseded`
     - latency p50/p95/p99 split by phase: embed, candidate query, cosine/ANN, write, total save
     - `memory_duplicate_fragmentation`
     - `memory_supersede_chain_length`
     - `vector_shape_mismatch_total`
     - `compact_reason_total`
     - compact cross-check: `active_rows_counter`, `active_rows_table_scan`, `active_rows_divergence_ratio`
   - Alert thresholds:
     - WARN bucket active rows `>80`, CRITICAL `>100`, anchored to the current `LIMIT 100` candidate cap (`store.ts:730-737`; v3 `research/...v3-final.md:37-42`).
     - WARN save latency p95 `>250ms`, explicitly above Reddi’s 200ms reference (`research/...v3-final.md:31`, `:38-41`).
     - CRITICAL vector shape mismatch ratio `>0.001` (`research/...v3-final.md:41`).
     - WARN/CRITICAL any metric-collector divergence `>1%`, per v3’s defense-in-depth cross-monitoring requirement (`research/...v3-final.md:42`).
     - Reddi source anchors: `book-03-chunk-0524 pp.1568-1570` for telemetry thresholds/fail-visible framing and `book-03-chunk-0390 pp.1180-1182` for defense-in-depth monitoring (`research/...v3-final.md:31`, `:334-335`).

   Migration step:
   - Snapshot: not required for metrics-only code, but keep Phase 0 snapshot as rollback anchor.
   - Backfill rule: initialize counters from a table scan, not from zero, to avoid false “healthy” metrics.
   - Dry-run validation:
     - Run old and new `memory_health` on the snapshot copy.
     - Confirm existing health fields are unchanged.
   - Acceptance gate:
     - `memory_health` includes all 12 metrics, alert statuses, and no NaN/null latencies after at least one save/search/load-session run.
     - Compact cross-check divergence is `<=1%`.

   Rollback path:
   - Revert telemetry code only.
   - Leave any telemetry JSONL file unused; it is append-only and not part of serving correctness.

   Acceptance test:
   ```powershell
   pnpm test -- --run v03-telemetry-health
   ```
   It should assert:
   - `memory_health` returns legacy health keys plus new telemetry keys;
   - candidate limit hit toggles when a fixture bucket exceeds 100;
   - p95 alert fires above 250ms;
   - vector mismatch alert fires above ratio threshold;
   - compact recount divergence above 1% produces an alert.

4. **Phase 3 — O2 Refined Validity And Review Semantics**

   Boundary: Phase 3 adds temporal correctness without changing dedup search architecture. It is complete when every row has validity/review fields, lifecycle respects `valid_to`, and stale-review rows are discoverable without expiring durable memories. Phase 4 is unlockable because dedup restructuring can then preserve the final v0.3 row shape.

   Files in `src/` change:
   - `schema.ts`: add `valid_from`, `valid_to`, `review_after` to `MemoryRow`, seed row, save/update schemas. v3 names these exact columns (`research/...v3-final.md:73-76`).
   - `store.ts`: set defaults in `createNew()`, preserve/update fields in `update()`, include them in `normalizeRow()`/result mapping. Current `createNew()` constructs the stored row around `expires_at`, supersession, source/media/task fields (`store.ts:237-269`).
   - `lifecycle.ts`: treat `valid_to < now` as invalid/archived only where policy says so; keep `review_after` as surfacing, not expiry. Current lifecycle only checks `expires_at` for archival (`lifecycle.ts:62-70`).
   - `index.ts` and `http-server.ts`: add `memory_review_stale` tool or extend `memory_health` with stale review counts. v3 estimates one day for `memory_review_stale` (`research/...v3-final.md:79`).
   - `pmm-bridge.ts`: if PMM lacks these fields, map defaults in bridge results so mixed session load remains stable.

   Schema delta:
   - Add `valid_from: number`.
     - Default: `created_at`.
     - Constraint: finite unix ms; `valid_from <= valid_to` when `valid_to != 0/null`.
   - Add `valid_to: number`.
     - Use `0` as LanceDB-friendly “currently valid” sentinel if nullable columns are awkward; otherwise `null`.
     - Default: `0`.
   - Add `review_after: number`.
     - Use `0` for “no review scheduled”.
     - Per-type default from v3 §1 Q2:
       - `fact`: `valid_from=created_at`, `valid_to=0`, review when drift-prone if known.
       - `decision`: `review_after = created_at + 90-180d`.
       - `preference`: `review_after = created_at + 180d`.
       - `lesson`: `review_after = created_at + 180-365d`.
       - `identity`: no TTL; periodic review only.
       - `relationship`: `review_after = created_at + 180-365d`.
       - `context`/`blocker`: keep existing `expires_at` semantics.
     - V3’s core distinction: `review_after` means “check this,” not “delete this” (`research/...v3-final.md:55`, `:73-79`).
   - Index/filter expectation:
     - Normal reads exclude invalid rows:
       ```sql
       status = 'active' AND (valid_to = 0 OR valid_to >= now)
       ```
     - `memory_review_stale` returns:
       ```sql
       status = 'active' AND review_after > 0 AND review_after <= now
       ```

   Migration step:
   - Snapshot: copy live store again before O2, even if Phase 0 exists.
   - Backfill rule:
     - `valid_from = created_at || updated_at || now`.
     - `valid_to = expires_at` only for `context`/`blocker` where `expires_at > 0`; otherwise `0`.
     - `review_after` by type using the table above.
   - Dry-run validation:
     - Spot-check 10 rows per type, as v3 requires (`research/...v3-final.md:215`).
     - Confirm no active row disappears from `memory_load_session` unless `valid_to` is already in the past.
   - Acceptance gate:
     - Row count unchanged.
     - No row has `valid_to < valid_from` except `valid_to = 0`.
     - `memory_review_stale` returns only rows with `review_after <= now`.
     - `expires_at` behavior for context/blocker remains unchanged.

   Rollback path:
   - Prefer snapshot restore.
   - Code-only rollback is possible if new columns are ignored, but do not declare rollback complete until session load/search match Phase 0 baseline.

   Acceptance test:
   ```powershell
   pnpm test -- --run v03-validity-review
   ```
   It should assert:
   - backfill defaults by memory type;
   - `review_after` does not archive rows;
   - `valid_to` filters normal search/session results;
   - lifecycle expiry still archives only `expires_at` rows unless policy explicitly maps them.

5. **Phase 4 — O9 Dedup Hot-Path ANN Restructure**

   Boundary: Phase 4 is the only phase that changes dedup decision behavior. It is deliberately last because telemetry from Phase 2 must be available first. It is complete when the old `LIMIT 100 + JS cosine` path is replaced by a combined-filter ANN query, and old/new disagreement is below the v3 gate. Phase 4 unlocks v0.3 release candidate.

   Files in `src/` change:
   - `store.ts`: replace `findCandidates()` and most of `findBestMatch()`. Current implementation fetches first 100 active rows by `type + scope`, then loops in JS cosine (`store.ts:730-760`). This is the cliff v3 calls out (`research/...v3-final.md:287-291`).
   - `store.ts`: instrument old-vs-new dual-run metrics during rollout.
   - `config.ts`: add `SUPERCLAUDE_DEDUP_MODE=old|dual|ann`, default `dual` for one release candidate.
   - `index.ts`/`http-server.ts`: expose dedup mode and disagreement metrics in `memory_health`.

   Schema delta:
   - No row column required.
   - Index requirement:
     - Use LanceDB vector search with combined scalar filter:
       ```ts
       tbl.vectorSearch(queryVector)
         .filter(
           "type = '...' AND scope = '...' AND status = 'active' " +
           "AND (visibility = 'shared' OR agent_id = '...') " +
           "AND (valid_to = 0 OR valid_to >= now)"
         )
         .limit(k)
       ```
     - Do not fetch arbitrary 100 rows and cosine them in JS.
   - If LanceDB cannot push down all scalar filters into ANN for the current version, keep dual-mode and raise this as a dependency blocker rather than shipping a fake O9.

   Migration step:
   - Snapshot: not schema-required, but snapshot before release candidate because dedup can create/supersede rows.
   - Backfill rule: none.
   - Dry-run validation:
     - Replay historical writes from the snapshot copy through old and new dedup.
     - Record `old_action`, `new_action`, `old_best_id`, `new_best_id`, `old_score`, `new_score`.
   - Acceptance gate:
     - v3’s gate: disagreement rate `<0.5%` on identical-input writes, with each disagreement investigated (`research/...v3-final.md:217`).
     - Candidate limit hit metric falls to zero or becomes irrelevant because candidate truncation is no longer the governing bound.
     - Search/session top-result migration invariant still holds for the 20 known queries (`research/...v3-final.md:224-229`).

   Rollback path:
   - Set `SUPERCLAUDE_DEDUP_MODE=old` and restart.
   - If bad supersedes were written, restore the pre-Phase-4 snapshot. Do not try to manually unwind supersession chains unless the exact affected IDs are known.

   Acceptance test:
   ```powershell
   $env:SUPERCLAUDE_DEDUP_MODE="dual"
   pnpm test -- --run v03-dedup-ann-dual
   ```
   It should assert:
   - combined-filter ANN returns candidates scoped by type, scope, visibility, validity, and status;
   - old/new disagreement is below 0.5% on fixtures/replay;
   - vector-shape mismatch rows are skipped visibly and counted;
   - no unauthorized private row is touched by dedup or access bump.

**B. Gotchas V3 Missed**

1. `visibility` cannot be enforced without caller identity. V3 lists O1 before O7, but current HTTP has no auth and no caller context (`http-server.ts:343-421`). Current MCP tools also pass only user filters to the store (`index.ts:91-110`). So O1 and O11 need a minimal auth/caller-context slice earlier than v3 implies.

2. `memory_load_session` is its own leakage path. It does direct table queries for context, critical, high-priority scoped rows, and tasks (`store.ts:425-455` and following), not a shared search helper. Visibility/validity filters must be added to each tier, plus PMM bridge session loading (`pmm-bridge.ts:148-196`).

3. `notify-handler` already receives `agent_id` but discards it when saving. The inbound schema includes `agent_id` (`notify-handler.ts:22-31`), while `store.save()` gets only content/type/scope/priority/topics/source/visibility/task data (`notify-handler.ts:118-127`). If not fixed, bridge-origin memories will be falsely attributed to the local default agent.

4. Vector-shape mismatches can silently evade migration tests. Current health counts invalid vector dimensions (`store.ts:546-580`) and dedup skips mismatched candidate vectors (`store.ts:749-752`). Backfill must not rewrite or drop rows just because vectors are malformed; it should count them, preserve content, and let telemetry alert.

5. LanceDB schema evolution is not a normal SQL `ALTER TABLE` plan. The current table is created by adding a seed row and deleting it (`store.ts:156-158`; schema seed at `schema.ts:112-137`). Adding columns probably means rewriting/upserting rows or table recreation in practice, so rollback should be snapshot-based, not “drop column” as a primary plan.

**C. Versioning Strategy**

Use one PR per phase, except Phase 1 should combine auth, caller identity, O11, and O1 because partial visibility enforcement without caller identity is misleading.

Recommended PRs:
1. `v0.3-phase0-preflight-docs-and-scripts`
2. `v0.3-phase1-auth-identity-visibility`
3. `v0.3-phase2-telemetry-health`
4. `v0.3-phase3-validity-review`
5. `v0.3-phase4-dedup-ann`

Feature flags:
- `SUPERCLAUDE_VISIBILITY_ENFORCEMENT=report|enforce`, default `report` in dry-run, `enforce` after tests.
- `SUPERCLAUDE_REQUIRE_HTTP_AUTH=false|true`, default `false` only for local dry-run, `true` before release.
- `SUPERCLAUDE_DEDUP_MODE=old|dual|ann`, default `dual` for Phase 4 RC.
- `SUPERCLAUDE_TEMPORAL_FILTERS=report|enforce`, default `report` for O2 dry-run.

Running old version while v0.3 ships:
- Yes, but do it against a parallel store copy, not the same LanceDB directory.
- Old server: live `~/.claude/memory/lancedb`.
- v0.3 dry-run server: `SUPERCLAUDE_DB_PATH=~/.claude/memory/lancedb.snapshot-v03-{timestamp}` and different port, e.g. `MEMORY_PORT=18801`.
- Do not dual-write personal memory until Phase 1 and Phase 2 are stable; dual-run should be read/replay/compare first. If dual-write is later needed, write to v0.3 copy only and promote it by directory swap after acceptance.

**D. Risk I’d Raise**

I would push back on v3’s order putting O7 HTTP auth as P1 after O1/O11. O1 visibility enforcement is not meaningful until the server can identify the caller. Current `/mcp` and `/notify` endpoints accept requests without auth (`http-server.ts:343-421`), and the current store APIs have no caller identity parameter. Move a minimal O7 slice into Phase 1: bearer token from env, caller identity resolution, and 401 on missing/invalid token for `/mcp` and `/notify`. Keep advanced capability grants deferred, but do not ship “visibility enforcement” on an unauthenticated caller model.

**E. Concrete Phase 0 Commands To Run Today**

```powershell
# 1. Set paths
$live="$HOME\.claude\memory\lancedb"
$stamp=Get-Date -Format "yyyyMMdd-HHmmss"
$snapshot="$HOME\.claude\memory\lancedb.snapshot-v03-$stamp"
$baseline="$HOME\.claude\memory\v03-baseline-$stamp"
New-Item -ItemType Directory -Force -Path $baseline | Out-Null

# 2. Snapshot the live LanceDB store
Copy-Item -Recurse -LiteralPath $live -Destination $snapshot

# 3. Record size/file-count baseline for live and snapshot
Get-ChildItem -Recurse -LiteralPath $live |
  Measure-Object -Property Length -Sum |
  ConvertTo-Json -Depth 4 |
  Set-Content -Encoding UTF8 "$baseline\live-size.json"

Get-ChildItem -Recurse -LiteralPath $snapshot |
  Measure-Object -Property Length -Sum |
  ConvertTo-Json -Depth 4 |
  Set-Content -Encoding UTF8 "$baseline\snapshot-size.json"

# 4. Record table file manifest for rollback comparison
Get-ChildItem -Recurse -LiteralPath $live |
  Select-Object FullName,Length,LastWriteTimeUtc |
  ConvertTo-Json -Depth 4 |
  Set-Content -Encoding UTF8 "$baseline\live-manifest.json"

# 5. If the HTTP server is running, capture current health endpoint
curl.exe -s http://127.0.0.1:18800/health > "$baseline\http-health.json"

# 6. Prepare v0.3 dry-run env against the snapshot copy, not live
"SUPERCLAUDE_DB_PATH=$snapshot" | Set-Content -Encoding UTF8 "$baseline\dry-run-env.txt"
"MEMORY_PORT=18801" | Add-Content -Encoding UTF8 "$baseline\dry-run-env.txt"

# 7. Verify snapshot exists and is non-empty
Test-Path $snapshot
(Get-ChildItem -Recurse -LiteralPath $snapshot | Measure-Object).Count
```

The missing Phase 0 command is a clean `memory_health` JSON capture through MCP. The current simple HTTP `/health` only reports process/session state (`http-server.ts:347-354`), while real memory health is an MCP tool (`index.ts:230-240`; `http-server.ts:254-258`). Add a small scripted MCP health call in Phase 0 tooling, then use it as the canonical pre/post migration baseline.