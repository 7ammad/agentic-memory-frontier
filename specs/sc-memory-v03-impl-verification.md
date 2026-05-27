# Codex Strict-Review — B Implementation (SC v0.3 Phase 1)

_Agent msg lengths: [209, 305, 349, 8750]_

---

# Check 1 Coverage — per item

| Item | Verdict | Evidence |
|---|---:|---|
| `agent_id` column on `MemoryRow` with sha256(ed25519_pub), default `LEGACY_AGENT_ID` | PARTIAL | Spec requires required row field and legacy backfill (`spec:41`, `spec:152`, `spec:160`). `schema.ts` makes it optional (`schema.ts:111`) and defines `LEGACY_AGENT_ID` (`schema.ts:120`). `identity.ts` computes `sha256(pub)` (`identity.ts:54`) from generated ed25519 keypair (`identity.ts:71`). New rows populate it (`store.ts:247`, `store.ts:282`, `store.ts:315`). Existing rows are not eagerly migrated. |
| `agent_alias` column | PARTIAL | Spec requires required field/default (`spec:42`, `spec:153`, `spec:161`). `schema.ts` makes it optional (`schema.ts:112`), default helper fills it (`schema.ts:168-169`), new rows write it (`store.ts:247-249`, `store.ts:282-286`). No physical migration. |
| `capabilities` column JSON-serialized | PARTIAL | Spec requires JSON array string/default (`spec:43`, `spec:154`, `spec:162`). `schema.ts` optional field (`schema.ts:113`), helper default (`schema.ts:170`), new rows stringify (`store.ts:249`, `store.ts:284-286`). No parse/validation enforcement beyond optional input. |
| `valid_from`, `valid_to`, `review_after` columns | PARTIAL | Spec’s final row shape requires them (`spec:44-46`), but detailed temporal semantics are Phase 3 (`spec:248-263`). `schema.ts` adds optional fields (`schema.ts:114-116`) and helper defaults (`schema.ts:171-173`). New rows write them (`store.ts:251-253`, `store.ts:288-290`, `store.ts:317-320`). No per-type backfill or `memory_review_stale`. |
| Visibility filter enforced at every read path: semantic, structured, loadSession | PARTIAL | Filters are applied in `semanticSearch` (`store.ts:350-353`), `structuredSearch` (`store.ts:404-407`), and `loadSession` via `visFilter` (`store.ts:503-506`). But `applyVisibilityFilter` exposes all legacy private rows to any non-empty caller (`store.ts:46`), violating synthetic non-owner requirements (`spec:168`, `spec:171`). `memory_task_list` is also a required read path (`spec:59`, `spec:171`) and is unfiltered. |
| HTTP auth on `/mcp` and `/notify` | IMPLEMENTED, with constraint | `http-server.ts` enables auth only when `CLAUDE_MEMORY_AUTH_TOKEN` is set (`http-server.ts:343-346`), checks `/notify` (`http-server.ts:427-428`) and `/mcp` (`http-server.ts:434-435`), and rejects 401 (`http-server.ts:364-366`). Constraint: unset token bypasses auth (`http-server.ts:354`), while spec also calls for feature flag/release enforcement (`spec:409`). |
| `notify-handler` preserves inbound `agent_id` | IMPLEMENTED | Payload schema requires `agent_id` (`notify-handler.ts:22-25`) and `store.save()` receives `agent_id: payload.agent_id` (`notify-handler.ts:120-131`). It also sets bridge visibility shared (`notify-handler.ts:126-127`). |
| Schema migration/backfill | MISSING | Spec requires migration/backfill rules (`spec:157-164`) and synthetic caller validation (`spec:168-171`). Implementation has lazy helper (`schema.ts:165-173`), but `store.ts` only imports `applyV03Defaults` (`store.ts:9`) and does not call it on read paths. There is no migration runner in the listed files. |

# Check 2 Internal Consistency

- `applyV03Defaults()` is documented as “Use this on every read path” (`schema.ts:110`, `schema.ts:165-173`), but `store.ts` imports it only and never calls it (`store.ts:9`). The implementation instead uses ad hoc defaults in filters.
- `normalizeMemoryRow()` drops all v0.3 fields during upserts: its returned object ends at `task_data` and omits `agent_id`, `agent_alias`, `capabilities`, `valid_from`, `valid_to`, `review_after` (`store.ts:1068-1105`). Updates, raw updates, and supersede marking can therefore strip v0.3 metadata.
- Legacy visibility logic contradicts the spec’s non-owner test. `applyVisibilityFilter()` returns legacy private rows to any non-empty caller (`store.ts:46`), but the spec says synthetic non-owner should see only shared rows (`spec:168`, `spec:171`).
- HTTP auth does not map bearer token to `caller_agent_id` as the spec says (`spec:142`). Store reads always use local `getIdentity()` (`store.ts:350`, `store.ts:404`, `store.ts:499-503`), so cross-agent caller identity is not actually injected.
- `memory_task_list` is a required read path in the canonical filter (`spec:59`, `spec:171`), but `taskList()` queries active tasks and maps results without visibility or temporal filtering (`store.ts:674-711`).
- The test file header claims visibility and notify tests (`b-phase1.test.ts:9-10`), but the actual tests only cover identity and `applyV03Defaults` (`b-phase1.test.ts:32`, `:41`, `:49`, `:58`, `:67`, `:102`).
- ACS is explicitly out of scope for v0.3 (`spec:31`), but `index.ts` adds `acs_send` and `acs_inbox` (`index.ts:360-430`). That may be useful, but it is outside the Phase 1 spec boundary.

# Check 3 Grounding — Spot-Checks

- PASS — `identity.ts` uses Node crypto ed25519: imports `generateKeyPairSync` from `node:crypto` (`identity.ts:20`) and calls `generateKeyPairSync("ed25519")` (`identity.ts:71`).
- PASS — `identity.ts` derives `agent_id` from sha256 public key: `createHash("sha256").update(input).digest("hex")` (`identity.ts:54`).
- PASS — `schema.ts` v0.3 fields are OPTIONAL, not required: `agent_id?`, `agent_alias?`, `capabilities?`, `valid_from?`, `valid_to?`, `review_after?` (`schema.ts:111-116`).
- PASS — `store.ts` create-new and supersede paths populate v0.3 fields: supersede row sets `agent_id`/`agent_alias`/`capabilities`/validity fields (`store.ts:247-253`); createNew resolves and writes them (`store.ts:282-290`, `store.ts:315-320`).
- PASS — `notify-handler.ts` passes `payload.agent_id` into `store.save()` (`notify-handler.ts:120-131`).
- PASS — `http-server.ts` uses constant-time-ish compare: length check, XOR diff loop, `diff === 0` (`http-server.ts:358-361`).
- FAIL — `applyV03Defaults()` is not applied on read. It appears only in the import list (`store.ts:9`), not in the actual read paths.
- FAIL — `memory_task_list` lacks the required visibility/validity filter (`store.ts:674-711` vs `spec:59`, `spec:171`).

# Check 4 Missing Artifacts

- No eager migration runner/backfill for existing LanceDB rows. The implementation appears intended to be lazy, but even the lazy helper is not actually applied in `store.ts`.
- No acceptance tests for HTTP auth on `/mcp` or `/notify`, despite spec gate (`spec:187-192`, `spec:427`).
- No tests for `semanticSearch`, `structuredSearch`, `loadSession`, or `memory_task_list` hiding private rows from synthetic non-owner.
- No tests for `notify-handler` agent attribution preservation, despite header claiming it.
- No tests that saved rows include `agent_id`, `agent_alias`, and `capabilities`.
- No tests for `valid_to` temporal filtering on search/session results.
- No tests for `Agent Card` endpoint shape.
- No evidence in the listed files of PMM bridge `agent_id` preservation, which the spec includes in Phase 1 (`spec:146`, `spec:193`). I did not read `pmm-bridge.ts` because it was not in the allowed implementation list.
- Auth rejection is implemented when token is set: missing/invalid auth reaches `rejectUnauthorized()` on `/notify` and `/mcp` (`http-server.ts:427-435`). But if `CLAUDE_MEMORY_AUTH_TOKEN` is unset, auth bypasses by design (`http-server.ts:354`).
- Agent Card endpoint exists (`http-server.ts:386-407`), but its ACS payload is not covered by tests and uses fixed ACS URLs on `18801` while the HTTP server uses configurable `PORT`.

# Patches Needed

1. Mechanical — Apply `applyV03Defaults()` consistently in all read and update normalization paths, or remove the claim that lazy migration is applied on read.
2. Mechanical — Preserve v0.3 fields in `normalizeMemoryRow()` so updates/upserts do not strip identity and temporal metadata.
3. Judgment-call/security — Fix legacy visibility semantics. Synthetic non-owner must not see legacy private rows unless explicitly treated as owner through a real caller identity model.
4. Judgment-call/security — Implement actual caller identity propagation from authenticated transport to store reads, or document that Phase 1 only supports local-agent auth and not cross-agent visibility yet.
5. Mechanical — Add visibility and temporal filtering to `taskList()`.
6. Mechanical — Add acceptance tests for auth rejection, search/session/task visibility, notify attribution, saved row metadata, temporal filtering, and agent-card endpoint.
7. Judgment-call — Decide whether Phase 1 requires eager backfill. The spec describes backfill/migration; current implementation is lazy and incomplete. If lazy is accepted, the spec or release notes should explicitly downgrade that requirement.

# Readiness Verdict: PATCH-FIRST