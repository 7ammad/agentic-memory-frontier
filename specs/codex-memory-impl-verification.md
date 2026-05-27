# Codex C Impl Verification

_Msg lengths: [141, 308, 232, 7034]_

---

# Check 1 Coverage

| Item | Verdict | Evidence |
|---|---:|---|
| Identity bootstrap: ed25519 keypair, `agent_id = sha256(pub)`, `agent_alias = "codex"` | IMPLEMENTED | `identity.ts:57` generates ed25519; `identity.ts:60-62` extracts/stores pub/priv raw buffers; `identity.ts:43` hashes; `identity.ts:112` derives `agent_id`; `identity.ts:36` defaults alias to `codex`. |
| Manifest with `schema_version=0.3.0` + supported range gate | IMPLEMENTED | `manifest.ts:23-24` declares `0.3.0` and `<0.4.0`; `manifest.ts:51-55` checks range; `manifest.ts:81` writes `schema_version`; `manifest.ts:102-107` rejects unsupported versions with `MANIFEST_VERSION_UNSUPPORTED`. |
| LanceDB store with v0.3 row shape, seed-and-delete pattern | PARTIAL | `store.ts:84-85` seed-and-deletes table; `schema.ts:98,118-123` seed contains 1024 vector and six v0.3 fields; `store.ts:119-124` saves all six fields. Partial because existing tables are opened without row-shape validation/migration. |
| BGE-M3 1024-dim embeddings via `@openclaw/local-embeddings` | IMPLEMENTED | `embeddings.ts:16-17` re-exports `EMBEDDING_DIM` from `@openclaw/local-embeddings`; `embeddings.ts:19` declares `BGE-M3`; `schema.ts:98` fixes seed vector length to 1024; tests assert `EMBEDDING_DIM === 1024` at `c-phase1-acceptance.test.ts:80-81`. |
| `ScMemoryBridge`: direct LanceDB cross-read, `visibility='shared'`, `sc:{id}`, preserve `agent_id` | IMPLEMENTED | `sc-bridge.ts:72-88` connects/opens SC table; `sc-bridge.ts:161-165` filters active + shared; `sc-bridge.ts:185` prefixes `sc:`; `sc-bridge.ts:195` maps `agent_id`. |
| 10 MCP tools | PARTIAL | All 10 memory tools are listed at `index.ts:115-125` and `index.ts:158-202`. Partial because the server also exposes `acs_send`/`acs_inbox` at `index.ts:130,148`, so this is not an exact 10-tool Phase 1 surface. |
| `memory_search` returns two ranked lists, local + `sc_shared`, with provenance | IMPLEMENTED | `store.ts:135-139` return shape is `{ local, sc_shared }`; `store.ts:175` returns both; local mapping uses provenance, SC mapping sets `provenance: "sc-shared"`. |
| `sc:` ID mutation rejection with `READ_ONLY_BRIDGE_ID` | PARTIAL | Store rejects in `update`, `softDelete`, and `taskUpdate` at `store.ts:281,308,406`. Partial because it throws plain `Error`; `index.ts:93-104` has the spec-shaped `McpError` helper, but it is unused, and tool cases call store methods directly at `index.ts:330-371`. |
| Bridge availability: probe, `last_probe_at`, `last_error`, lazy retry cooldown | IMPLEMENTED | `sc-bridge.ts:56-57` fields; `sc-bridge.ts:72-91` probe; `sc-bridge.ts:98-99` status; `sc-bridge.ts:22,107-111` 60s lazy retry cooldown; `index.ts:83` startup probe. |
| HTTP layer: `/.well-known/agent-card.json` + `/health` | IMPLEMENTED | `http-server.ts:31-42` serves `/health`; `http-server.ts:44-75` serves agent card; `index.ts:400-401` starts HTTP layer. |
| 8-test acceptance battery per spec §8.5 | PARTIAL | File has 11 tests, but several are weakened from spec: T1 uses `score >= 0.5` not `>= 0.85` at `c-phase1-acceptance.test.ts:75`; T3 allows bridge unavailable at `:84-93`; T4 does not actually set non-existent `SC_MEMORY_DB_PATH` at `:95-109`; T8 tests 10 local concurrent saves, not SC writing 100 rows while Codex searches, at `:164-181`. |

# Check 2 Internal Consistency

- `store.ts` header says “search + save scaffolded” and “full surface ... to be completed,” but the same file implements load session, update, delete, compact, stats, task list, and task update. This is stale implementation-status text.
- `index.ts` header says only `memory_save + memory_search` are wired and the remaining 8 are TODO-stubbed, but `index.ts:325-371` wires the remaining memory tools.
- `index.ts` defines a spec-compliant `rejectScId` MCP error helper at `index.ts:93-104`, but mutation handlers do not call it; they rely on store-level plain `Error`s.
- `schema.ts` comment says the six v0.3 fields are first-class, populated fields, but the `MemoryRow` interface marks them optional at `schema.ts:83-88`. Runtime save populates them, but the type contract is looser than the implementation/spec.
- Test comments claim strict acceptance tests, but actual tests are looser than the spec battery in T1/T3/T4/T8.

# Check 3 Grounding

- PASS: Bridge `filterAndMap` enforces `visibility='shared'`: `sc-bridge.ts:165`.
- PASS: Bridge prefixes SC IDs: `sc-bridge.ts:185`.
- PASS: Bridge preserves `agent_id`: `sc-bridge.ts:195`.
- PASS: `Store.save` populates all six v0.3 fields from identity/input/defaults: `store.ts:119-124`.
- PASS: `update`, `delete`, and `taskUpdate` reject `sc:` IDs: `store.ts:281`, `store.ts:308`, `store.ts:406`.
- FAIL: Rejection does not match the required MCP error JSON contract. Store throws plain `Error`; `CallTool` catch wraps it as `"Error in ${name}: ..."` rather than the specified `{"code":"READ_ONLY_BRIDGE_ID",...}` payload.
- PASS: HTTP agent card includes `extensions.acs.ed25519_pub_key`: `http-server.ts:55-62`.
- PASS: `memory_search` returns separate `local` and `sc_shared` lists: `store.ts:135-139`, `store.ts:175`.
- FAIL: `memory_task_list` does not include SC shared tasks; `store.ts:370-401` only queries local table and never calls the bridge.

# Check 4 Missing Artifacts

- Spec-accurate 8-test acceptance battery is missing. Current file has 11 tests but weakens or substitutes multiple required checks.
- `memory_task_list` SC shared task inclusion is missing.
- Spec-shaped `READ_ONLY_BRIDGE_ID` MCP error path is missing in the active tool handlers.
- Existing-table v0.3 schema validation or migration guard is missing.
- `~/.codex/config.toml` MCP registration artifact is not present in the reviewed files.
- Snapshot/backup routine is not implemented in the reviewed files.
- Rollback runbook artifact from the spec is not present in the reviewed files.

# Patches needed

1. Wire `rejectScId` into `memory_update`, `memory_delete`, and `memory_task_update` before calling store methods, or convert store errors into the exact JSON `READ_ONLY_BRIDGE_ID` MCP error contract.
2. Add bridge-backed SC shared tasks to `memory_task_list`, returning provenance and keeping SC rows read-only.
3. Replace the acceptance test substitutions with the actual §8.5 checks: T1 `>=0.85`, T3 requires an SC shared row and `bridge.available === true`, T4 uses a non-existent SC path/fresh bridge, T5 seeds/verifies private leak prevention, T8 runs SC-write/Codex-search concurrency.
4. Remove or correct stale “scaffolded/TODO” comments in `store.ts` and `index.ts`.
5. Validate existing LanceDB table shape on open, especially presence of the six v0.3 fields, or fail fast with a clear schema error.
6. Decide whether ACS tools belong in this Phase 1 server. If Phase 1 is meant to mirror exactly 10 SC-compatible memory tools, move `acs_send`/`acs_inbox` out or gate them behind a later phase/config.
7. Add the missing operational artifacts: config registration block, snapshot/backup routine, and rollback runbook.

# Readiness verdict: PATCH-FIRST