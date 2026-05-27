# Codex Memory MCP — System Design Spec (Sub-Project C)

**Project:** Agentic Memory System
**Date:** 2026-05-26
**Status:** DRAFT — awaiting Step 6 codex strict-review verification
**Deliverable target:** this file
**Inputs:** sub-project A (v3 review at `research/2026-05-26-superclaude-memory-deep-review-v3-final.md`), sub-project B (v0.3 spec at `specs/2026-05-26-sc-memory-v0.3-upgrade-spec.md`), codex counsel at `research/codex-counsel-C-output.md`, 6 MIT-12 lens packets at `C:\Dev\research\MIT\MIT 12 Research\tools\.runtime\queries\codex-memory-C\`.
**Sequencing:** B verified-READY → C (this) → D (ACS), strict order per [mem_0f8bfb76] mandatory verification rule.

---

## 1. Executive Verdict

Build the Codex memory MCP as a **Node/TypeScript twin** of SuperClaude memory, using **LanceDB-Node** at `C:\Users\7amma\.codex\memory\lancedb\`, sharing the **v0.3 Phase 1 schema** for day-1 interop. The cross-store bridge for Phase 1 is **direct LanceDB read-only access** to SC's LanceDB at `C:\Users\7amma\.claude\memory\lancedb\`, opened as a second table from the Codex process. In Dec-POMDP terms this is "free communication" — the cheapest cross-agent channel both theoretically (MMDP/MPOMDP complexity class instead of Dec-MDP NEXP) and operationally (no HTTP, no auth bootstrapping, no transport-layer drift).

`memory_load_session` pulls from **both stores**: Codex local rows where `(visibility='shared' OR agent_id=codex_id)`, plus SC rows where `visibility='shared'`, with **visibility re-checked on the Codex read side** (the notify-handler gotcha from sub-project B applies symmetrically). Mutating tools — `memory_save`, `memory_update`, `memory_delete`, `memory_compact`, `memory_task_update` — operate **only on the Codex local store** in Phase 1.

Bootstrap is clean-slate. There is no `~/.codex/memory/` directory today; the two automations (`mtm-lead-generation-scout`, `sonoa-lead-generation-scout`) are not memory state and should not be migrated blindly. Phase 1 ships 10 tools mirroring SC for compatibility floor; Phase 2 adds `memory_review_stale` once SC's v0.3 temporal columns are live (codex's pushback was correct — see §5.6).

The **missing artifact** in both Hammad's locked constraints and codex's design is a **backup/restore + schema-version protocol**. By the time Codex memory accumulates rows worth keeping, schema decisions are correction cascades waiting to happen. Add a `manifest.json` beside `lancedb/` recording `schema_version` + identity public key, expose `schema_version` via `memory_health`, and snapshot before any schema rewrite. Treat this as Phase 0 — alongside bootstrap, not after.

---

## 2. Architecture and current-state assessment

### 2.1 The proven shape — SC memory MCP

SC memory's TypeScript implementation already establishes the runtime shape Codex needs. The MCP server is `Server`-class based, registers tools via `setRequestHandler`, uses stdio transport for direct invocation and Streamable HTTP for cross-process A2A [code: index.ts:3-5], [code: http-server.ts:18-20]. LanceDB is initialized lazily — `getStore()` is called per-request to avoid blocking startup [code: index.ts:40-44] — and the store opens or creates `agent_memories` with a 1024-dim vector schema seeded then deleted to fix the column type [code: store.ts:46-49, 150-158]. The 1024-dim choice is BGE-M3 and is hard-fixed at the config layer [code: config.ts:9-11]. Embeddings come from a shared local package exporting `embedText`/`embedBatch`/`EMBEDDING_DIM` [code: embeddings.ts:6-10]; no API key, no network dependency, model loaded on first use [code: http-server.ts:424].

SC currently exposes 10 tools registered in `index.ts`: `memory_save`, `memory_search`, `memory_load_session`, `memory_update`, `memory_delete`, `memory_compact`, `memory_health`, `memory_stats`, `memory_task_list`, `memory_task_update` [code: index.ts:51, 78, 136, 164, 181, 211, 230, 245, 260, 291]. The v0.3 spec adds an 11th (`memory_review_stale`) in Phase 3 once temporal columns are live.

### 2.2 The proven bridge pattern — pmm-bridge

The prior-art bridge is `PmmBridge` in `pmm-bridge.ts`, which exists exactly because SC needed to read OpenClaw PMM's separate LanceDB table from the same Node process. The pattern is: lazy-import LanceDB, attempt to connect to a second filesystem path, open a named table, expose `available=false` as the failure state when init fails [code: pmm-bridge.ts:64, 73-76]. When unavailable, query methods return `[]` rather than throwing [code: pmm-bridge.ts:112-113]. This is the exact shape Codex's `ScMemoryBridge` should take.

There is one **known gotcha** in the current PMM bridge that Codex's design must fix: the mapper drops `agent_id` when crossing the boundary [code: pmm-bridge.ts:214, 218, 231]. The notify-handler exhibits a related issue — inbound payload carries `agent_id` [code: notify-handler.ts:22, 25] but the save path drops identity and hardcodes `visibility='shared'` [code: notify-handler.ts:118, 124-126]. The general principle (validated by sub-project B's verification gate) is: **visibility must be re-checked on the receiving read side, never assumed from the writing side**. Codex's bridge must preserve `agent_id` end-to-end and apply the full visibility predicate at read time.

### 2.3 The locked schema — v0.3 Phase 1 (from sub-project B)

Per [mem_63263e0e] the v0.3 row shape adds six columns to `MemoryRow` at [code: schema.ts:84]: `agent_id` (sha256 ed25519 pub key, 64-char lowercase hex), `agent_alias` (e.g. `"codex"`), `capabilities` (JSON-serialized array), `valid_from` (defaults to `created_at`), `valid_to` (0 = currently valid), `review_after` (0 = no review). `visibility` is existing but ENFORCED via canonical filter at every read path:

```sql
status = 'active'
AND (visibility = 'shared' OR agent_id = '{caller}')
AND (valid_to = 0 OR valid_to >= {now})
AND (scope = 'global' OR scope = '{requested}')
```

Codex must inherit this filter shape exactly. For SC-cross-reads through the bridge, the filter tightens to `visibility = 'shared'` only (Codex is not the SC owner; the `agent_id = caller` clause does not apply).

### 2.4 What is NOT in Codex's runtime yet

The `~/.codex/` directory contains `config.toml`, `config-BACKUP.toml`, `plugins/` (cached plugin bundles including Vercel skills), `automations/` (two lead-generation-scout configs), `browser/sessions/`, and `.tmp/`. There is **no** `~/.codex/skills/` or `~/.codex/memory/` — clean slate for memory. The `automations/` configs are persistent automation state, not memory rows, and should not be migrated as part of Codex memory bootstrap (they may be ingestion candidates later — flagged in §5.5).

---

## 3. Gap analysis (ranked by blast radius)

| # | Gap | Blast radius | Phase |
|---|-----|--------------|-------|
| G1 | No identity infrastructure for Codex — `agent_id` cannot be derived without ed25519 keypair | All cross-agent operations break without identity | 1 |
| G2 | No backup/restore protocol — first non-trivial schema change is irreversible if rows accumulated first | Loss of all Codex memory if migration fails mid-flight | 0/1 |
| G3 | No cross-store visibility re-check on read side — SC PMM bridge has this bug today | Private SC rows could leak into Codex on a misconfigured save | 1 (mandatory) |
| G4 | No `schema_version` in health/manifest — future v0.4 changes will silently desync stores | Drift between SC and Codex schemas degrades cross-store semantic search | 1 (cheap to add) |
| G5 | No bridge availability telemetry — caller can't tell if "no SC results" means empty or bridge down | Silent failures during multi-agent handoffs | 2 |
| G6 | No key rotation procedure for ed25519 identity | Compromised key forces full provenance reset | 3 |
| G7 | `memory_review_stale` not in initial tool surface — codex's pushback | Codex misses temporal validity hygiene once v0.3 is live | 2 |

Gaps G1, G2, G3, G4 must be addressed in Phase 1. G5, G6, G7 can defer to Phase 2/3.

---

## 4. Codex counsel — verbatim reference

See `research/codex-counsel-C-output.md` for the full 15,279-character output (codex exec 0.128.0, model_reasoning_effort=medium, ~150K tokens). Headline summary:

- **Q1 substrate**: LanceDB-Node — no impedance mismatch, can cross-read SC's table from same process.
- **Q2 runtime**: Node/TypeScript — proven shape, can vendor SC's `embeddings` package, smaller op-delta than Python/FastMCP.
- **Q3 bridge**: Direct LanceDB cross-read for Phase 1. HTTP localhost is deferred until SC's v0.3 auth is shipped (current `/notify` and `/mcp` paths are unauthenticated [code: http-server.ts:359, 360, 365, 376]).
- **Q4 tool surface**: Mirror 10. Mutating tools reject `sc:` IDs. `memory_load_session` reads from both stores.
- **Q5 migration**: Clean-slate bootstrap. Do not run SC's flat-file migration script — its paths are `.claude`-rooted [code: migration.ts:15-19].
- **Q6 pushback**: "Mirror SC's 10 tools" is fine as Phase 1 floor but should not permanently exclude `memory_review_stale`.
- **Q7 missing**: Backup/restore + schema-version protocol.

This synthesis preserves all five concrete recommendations, adopts the Q6 pushback into the Phase plan, and elevates the Q7 missing item to Phase 0/1 alongside bootstrap.

---

## 5. Final answers — SOURCE FACT / INFERENCE / JUDGMENT / OPEN QUESTION

### 5.1 Storage substrate (Q1) — JUDGMENT: LanceDB-Node

This is a vendor-fact + operational call, not a theory call. MIT-12 doesn't have substrate-level recommendations for vector stores; the protocol's "Do Not Use For" boundary correctly excludes vendor SDK choice. Codex's read of SC source provides the grounded answer:

- SC opens `agent_memories` with a 1024-length zero vector (`const dim = 1024; vector: Array.from({length: dim}, () => 0)`) and seeds-then-deletes a row to fix the schema [code: store.ts:150-158, schema.ts:112-117], with the dimension constant fixed at `EMBEDDING_DIM=1024` [code: embeddings.ts, config.ts:9-11].
- The same table name and dimension allow the Codex process to open SC's LanceDB file directly via the LanceDB-Node binding without translation. SQLite+sqlite-vec, DuckDB-VSS, and pgvector all require a translation layer that re-implements vector format and rebuilds the same BGE-M3 dimension assumption — they each create a second source of truth for the embedding space.

**JUDGMENT for Codex memory**: choose `@lancedb/lancedb` Node binding, same table name `agent_memories`, same 1024-dim vector column, same schema-seed bootstrap pattern as `store.ts:150-158`. Database lives at `C:\Users\7amma\.codex\memory\lancedb\`.

**Rejected alternatives**: pgvector requires a separate Postgres process violating the embedded/single-host constraint; SQLite+sqlite-vec and DuckDB-VSS need new code to read SC's existing rows and add risk of cosine-comparability drift across vector formats.

### 5.2 Runtime (Q2) — JUDGMENT: Node/TypeScript

Same character of call (vendor-fact + operational). Codex's bias-check is the right discipline: don't pick Node just because SC is Node. The operational delta sources:

- SC's MCP server uses the official `@modelcontextprotocol/sdk` Server class, stdio transport, Streamable HTTP transport, and Zod schemas [code: index.ts:3-5, http-server.ts:18-20]. The 10-tool registration pattern repeats `setRequestHandler` per tool [code: index.ts:51, 78, 136, 164, 181, 211, 230, 245, 260, 291] — directly portable to Codex.
- Embedding model loading and caching are solved at the package level [code: embeddings.ts:1-10] with "loaded on first use" semantics [code: http-server.ts:424]. Codex can vendor or NPM-link this package; Python/FastMCP would duplicate the model loader and the BGE-M3 cache.
- Python/FastMCP would still require the same LanceDB binding, but the Node binding is what SC has been validated against. Mixed-language access to a single LanceDB file is not impossible but creates a second axis of "does it still work after version drift".

**JUDGMENT for Codex memory**: Node/TypeScript MCP server, NPM-link or vendor SC's embeddings package (rename internally if needed), keep the same Zod schema discipline.

**Rejected alternatives**: Python/FastMCP would be the right call if Codex memory had Python-only ML dependencies (e.g., a custom reranker). It doesn't. Going Python adds the embedding-model-duplicate-load risk and the LanceDB-binding-cross-language-drift risk without a single Python-specific upside.

### 5.3 Bridge transport (Q3) — JUDGMENT: direct LanceDB cross-read

**SOURCE FACT** [`mit12: book-09-chunk-0050 pp.205-208`]: Table 7.2 in Kochenderfer's *Decision Making Under Uncertainty* gives the complexity classes of multi-agent decision problems crossed by observability and communication. Free Communication × Full Joint Observability = MMDP (P). Free Communication × Partial Observability = MPOMDP (PSPACE). General Communication × Joint Full = Dec-MDP (NEXP). General Communication × Partial = Dec-POMDP (NEXP).

**SOURCE FACT** [`mit12: book-04-chunk-0136 pp.570-573`]: Kochenderfer-Wheeler-Wray define free communication as "happens outside the model (e.g., a high-speed wireless connection in robots)" and general communication as agents communicating "(typically imperfectly) via their actions".

**INFERENCE**: When SC and Codex run on the same machine with mutual filesystem access, the available bridge transports map as follows. Direct LanceDB cross-read is **free communication** — Codex observes SC's state directly through a shared substrate, outside the action-space. Communication-via-shared-rows (Codex saving a row that SC interprets as a message) is **general communication** — Codex's observation of SC happens through SC's actions on the shared store. The complexity class delta is significant: free comm collapses to P/PSPACE, general comm sits at NEXP.

**JUDGMENT for Codex memory bridge — Phase 1**: implement `ScMemoryBridge` as the Codex-side twin of `PmmBridge`. Lazy LanceDB import, connect to `C:\Users\7amma\.claude\memory\lancedb\`, open `agent_memories` read-only, degrade to `available=false` returning `[]` on failure [pattern: pmm-bridge.ts:64, 73-76, 112-113]. Apply the full SC-side predicate on every read: `status='active' AND visibility='shared' AND (valid_to=0 OR valid_to>={now}) AND (scope='global' OR scope={requested})`. Preserve original `agent_id` from SC rows into the result; do **not** repeat the PMM bridge's `mapRow` drop [pattern to fix: pmm-bridge.ts:214, 218, 231]. Return prefixed IDs (`sc:{id}`) so caller-side mutations can be rejected (see §5.4.1).

### 5.3.1 Bridge availability and retry semantics

The bridge exposes three fields surfaced through `memory_health.bridge`:

- `available: boolean` — true iff the most recent probe succeeded
- `last_probe_at: number` — unix ms of the last probe attempt
- `last_error: string | null` — last failure message, or null if last probe succeeded

Probe policy:

- **Startup probe**: attempted once at server start. Result populates the three fields. Failure is non-fatal — server stays up with `available=false`.
- **Per-call lazy retry**: when a tool that would consult the bridge is called and `available=false` and `now - last_probe_at > 60000` (60s cooldown), re-probe before the read. If re-probe succeeds, set `available=true` and continue. If re-probe fails, leave `available=false` and update `last_probe_at` + `last_error`.
- **Disabled mode**: if `CODEX_MEMORY_BRIDGE_ENABLED` (env, see §5.5 step 5) is false, no probe attempts. `available` stays `false` permanently, `last_error` is `"bridge disabled by config"`, `last_probe_at` is the server-start time.

**Visibility enforcement on the read side** — this is the notify-handler gotcha applied symmetrically. Inbound notify carries `agent_id` [code: notify-handler.ts:22, 25] but the save path drops identity and forces `visibility='shared'` [code: notify-handler.ts:118, 124-126]. That proves write-side labels are not enforceable assumptions. Codex's bridge does not trust SC's write-side labels; it filters at read time using the full predicate above.

**Rejected alternatives**: HTTP localhost is the right call **once** SC v0.3 auth is live and caller identity is on the wire — currently `/notify` and `/mcp` are unauthenticated [code: http-server.ts:359, 360, 365, 376] which would let any process on the box impersonate Codex's identity. Named pipes/Unix sockets add transport complexity without a payoff at this scale. Phase 1 stays on direct LanceDB; **Phase 3** migrates to HTTP localhost when SC v0.3 auth ships (see §7 Phase 3 item 21).

**OPEN QUESTION**: under what concurrency conditions does LanceDB-Node tolerate two processes (SC write + Codex read) on the same table? Lance's storage format is append-only with manifest versioning, which is favorable, but the specific behavior under SC writing a new row while Codex is mid-query needs to be tested. Requires a Phase 1 acceptance test, not a paper answer.

### 5.4 MCP tool surface (Q4) — JUDGMENT: mirror SC's 10 tools, with codex-side defaults

**JUDGMENT for Codex memory tool surface (Phase 1)**: register the same 10 tools as SC, with these per-tool differences:

| Tool | Codex-side difference |
|------|----------------------|
| `memory_save` | Default `agent_alias="codex"`, `agent_id={codex_id}`, `visibility="private"`. Writes to Codex local LanceDB only. |
| `memory_search` | Search Codex local + bridge SC reads. **Return two separate ranked lists** with `provenance` field on each row (`"local"` or `"sc-shared"`); local list first by convention. Apply local predicate to local rows; bridge predicate (`visibility='shared'` only) to SC rows. **Do not** mix cosine scores across stores in Phase 1 — see §6.1 for construct-validity rationale; mixed ranking is deferred to Phase 2 after empirical cosine-comparability calibration. |
| `memory_load_session` | **Both stores**. Local rows where `(visibility='shared' OR agent_id=codex_id)`; SC rows where `visibility='shared'`. Apply SC's five-tier loader pattern [code: store.ts:425-480] symmetrically to both stores. Results include `provenance` field per row. |
| `memory_update` | Reject `sc:`-prefixed IDs (see §5.4.1 error contract). Mutate only Codex local rows. |
| `memory_delete` | Reject `sc:`-prefixed IDs (see §5.4.1). Mutate only Codex local rows. |
| `memory_compact` | Operate only on Codex local rows. |
| `memory_health` | Report Codex local store health (row counts, vector dim, orphan refs, `schema_version`, identity status) AND bridge state separately (see §5.3.1 bridge availability fields). Pattern: extend [code: store.ts:93-100, 109, 526] with new `bridge`, `schema_version`, `manifest_path` fields. |
| `memory_stats` | Same separation — local stats vs bridge stats. |
| `memory_task_list` | Include SC shared tasks (read-only via bridge) in results. Mark `provenance`. |
| `memory_task_update` | Reject `sc:`-prefixed task IDs (see §5.4.1). Mutate only Codex local tasks. |

### 5.4.1 Cross-store read-only ID rejection contract

Any mutating tool (`memory_update`, `memory_delete`, `memory_task_update`) called with an ID matching `^sc:` returns an MCP error:

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "{\"code\": \"READ_ONLY_BRIDGE_ID\", \"id\": \"<the rejected id>\", \"message\": \"Cannot mutate cross-store row through bridge. SC rows are read-only from Codex in Phase 1.\"}"
    }
  ]
}
```

If the same tool is exposed via the HTTP wrapper (Streamable HTTP transport), the wrapper maps this to HTTP 400 with the same JSON payload.

**Rationale for `memory_load_session` reading both stores**: session start is exactly where cross-agent continuity matters most. A Codex session that doesn't see SC's `mem_343df0ac`-style state memories at startup will re-litigate decisions that Hammad already validated. The cost of NOT cross-loading at session start is exactly the failure mode the Agentic Memory System project exists to prevent.

**Rejected alternative**: keep `memory_load_session` local-only for safety. Safer, but defeats the project's purpose. The constraint that makes it safe is the bridge predicate — Codex sees only `visibility='shared'` SC rows, never private SC rows.

**DECIDED (was an open question)**: Phase 1 returns two separate ranked lists with a `provenance` field — see §5.4 `memory_search` row and §6.1 for the construct-validity rationale. Mixed-cosine ranking across stores is deferred to Phase 2 after the Phase 2 calibration step in §7 item 19 measures cosine-comparability between independent re-embeddings.

### 5.5 Migration story (Q5) — JUDGMENT: clean-slate bootstrap, no legacy migration

**SOURCE FACT** [`mit12: book-03-chunk-0146 pp.444-446`]: "Feature store migration represents a significant undertaking... Successful migrations typically proceed incrementally: starting with new features in the feature store while gradually migrating high-value legacy features, prioritizing those used across multiple models or causing known training-serving skew issues."

**INFERENCE**: Codex memory does not have legacy memory state to migrate. `~/.codex/memory/` does not exist. The `automations/` directory contains automation configs, not memory rows. Even SC's own migration script (`migration.ts`) operates on `.claude`-rooted paths [code: migration.ts:15-19] and is the wrong tool for a clean-slate `~/.codex/memory/` bootstrap.

**JUDGMENT for Codex bootstrap**. Two-phase ordering (matches §7 backlog phases):

**Phase 0 — pre-row bootstrap (before any memory rows exist)**:

1. **Identity generation**. On first server start, generate ed25519 keypair. Store private key at `~/.codex/memory/identity/codex.ed25519.key` with restrictive permissions (Windows: NTFS ACL restricting to user). Store public key alongside as `codex.ed25519.pub`. Derive `agent_id = lowercase hex sha256(ed25519_pub_key)`. Set `agent_alias = "codex"`. Refuse to start if identity files exist but don't parse.
2. **Manifest creation**. Write `~/.codex/memory/manifest.json` with `{"schema_version": "0.3.0", "agent_id": "...", "agent_alias": "codex", "created_at": <unix_ms>, "embedding_model": "BGE-M3", "embedding_dim": 1024}`. Server reads manifest on every start and refuses to start if `schema_version` is not in the runtime-supported semver range (see §5.7.1).
3. **LanceDB table creation**. Connect to `~/.codex/memory/lancedb/`. Open or create `agent_memories`. Seed with a v0.3-shape row [pattern: store.ts:150-158], then delete the seed. Schema must include all v0.3 columns from [mem_63263e0e].
4. **BGE-M3 warmup**. Embed a fixed string (`"codex memory bootstrap"`) to pre-load the model and cache the result. Validate output is 1024-length and `EMBEDDING_DIM === 1024` [pattern: embeddings.ts:6-10].

**Phase 1 — MCP runtime activation**:

5. **MCP registration**. Add `[mcp_servers.codex-memory]` block to `~/.codex/config.toml`. Concrete block (paths normalized for Windows):

   ```toml
   [mcp_servers.codex-memory]
   command = "node"
   args = ["C:\\Users\\7amma\\.codex\\mcp-servers\\codex-memory\\dist\\index.js"]

   [mcp_servers.codex-memory.env]
   CODEX_MEMORY_DB_PATH = "C:\\Users\\7amma\\.codex\\memory\\lancedb"
   CODEX_MEMORY_AGENT_ALIAS = "codex"
   CODEX_MEMORY_IDENTITY_PATH = "C:\\Users\\7amma\\.codex\\memory\\identity"
   CODEX_MEMORY_MANIFEST_PATH = "C:\\Users\\7amma\\.codex\\memory\\manifest.json"
   SC_MEMORY_DB_PATH = "C:\\Users\\7amma\\.claude\\memory\\lancedb"
   CODEX_MEMORY_BRIDGE_ENABLED = "true"
   ```

   Env var defaults (used when key is absent):

   | Env var | Default | Parse rule |
   |---------|---------|------------|
   | `CODEX_MEMORY_DB_PATH` | `~/.codex/memory/lancedb` | filesystem path string |
   | `CODEX_MEMORY_AGENT_ALIAS` | `"codex"` | string |
   | `CODEX_MEMORY_IDENTITY_PATH` | `~/.codex/memory/identity` | filesystem path string |
   | `CODEX_MEMORY_MANIFEST_PATH` | `~/.codex/memory/manifest.json` | filesystem path string |
   | `SC_MEMORY_DB_PATH` | `~/.claude/memory/lancedb` | filesystem path string |
   | `CODEX_MEMORY_BRIDGE_ENABLED` | `"true"` | true if value in `["true","1","yes","on"]` (case-insensitive); false otherwise |

6. **Bridge probe (non-fatal)**. On first start, attempt to open SC's `agent_memories` table read-only. Populate `available`, `last_probe_at`, `last_error` (see §5.3.1). Log to `~/.codex/memory/telemetry.jsonl`.
7. **Acceptance test battery**. Run the 8-test battery in §8.5 before declaring Phase 1 complete.

**`automations/` and migration candidates**: `mtm-lead-generation-scout` and `sonoa-lead-generation-scout` are persistent automation state. They are not memory rows and should NOT be auto-imported. They may be ingestion candidates in a later Phase if Hammad confirms they contain learnings worth preserving as memory entries; that's a separate workflow decision, not part of Codex memory bootstrap.

**Rejected alternative**: running SC's `migration.ts` against `~/.codex/`. Its file-rename and backup procedures [code: migration.ts:701, 710, 712] target `.claude`-rooted paths and would either no-op or corrupt the Codex directory layout.

### 5.6 Codex's pushback (Q6) — accepted: `memory_review_stale` not frozen out

Codex's pushback was: "mirror SC's 10 tools" is correct as a Phase 1 floor but should not permanently exclude `memory_review_stale`, which v0.3 Phase 3 introduces. **Accepted.** Phase 1 mirrors 10 tools exactly for compatibility (the locked constraint). Phase 2 adds `memory_review_stale` to the Codex tool surface as soon as v0.3 temporal columns (`valid_from`, `valid_to`, `review_after`) are live in SC and the Codex local store has accumulated non-trivial review_after-set rows.

This is not a re-litigation of the hard constraint — it's a phase ordering. The hard constraint says "mirror SC's 10 tools" for MCP registration in Phase 1; it does not say "never expand beyond 10." Codex caught a real ambiguity in how the constraint reads.

### 5.7 Missing item (Q7) — accepted: backup/restore + schema-version protocol

Codex flagged the absence of a backup/restore protocol as the most foundational missing item. **Accepted.** Hardening with MIT-12 grounding:

**SOURCE FACT** [`mit12: book-03-chunk-0381 pp.1157-1160`]: "Assumptions baked into earlier models become implicit constraints for future models, limiting flexibility and increasing the cost of downstream corrections... Correction cascades emerge from hidden feedback loops that violate system modularity principles... The cascade propagation follows power-law distributions, where small initial changes can trigger disproportionately large system-wide modifications."

**SOURCE FACT** [`mit12: book-03-chunk-0386 pp.1171-1173`]: "Robust rollback procedures are essential to handle unexpected issues, reverting systems to the previous stable model version to ensure minimal disruption."

**SOURCE FACT** [`mit12: book-03-chunk-0145 pp.442-444`]: "Storage strategies typically implement tiered retention: hot storage retains recent data (past week) for rapid analysis, warm storage keeps medium-term data (past quarter) for periodic analysis, and cold archive storage retains long-term data (past years)."

**INFERENCE**: Schema decisions made on day 1 of a memory store have power-law downstream cost. The `manifest.json` + `schema_version` discipline is cheap to add Phase 1 and exponentially expensive to retrofit after rows accumulate. Tiered backup retention is the operational template — fresh snapshots are cheap; archive of older snapshots is the safety net.

**JUDGMENT for Codex backup/schema versioning (Phase 1)**:

- **manifest.json**: `~/.codex/memory/manifest.json` records `schema_version` (semver, starts at `0.3.0`), `embedding_model`, `embedding_dim`, `agent_id`, `agent_alias`, `created_at`. Read at every server start; refuse to start if `schema_version` is not in the runtime-supported semver range (see §5.7.1 — Phase 1 server supports `^0.3.0`, i.e., `>=0.3.0 <0.4.0`).
- **schema_version in health output**: `memory_health` returns `schema_version` and `manifest_path` alongside existing fields [extend: store.ts:93-100, 526]. Bridge health includes SC's `schema_version` read from SC's manifest (if SC ships one — see Open Question).
- **Snapshot before schema rewrite**: any code path that adds/removes columns or changes column types **must** first call a `snapshot()` routine that copies the lancedb/ directory to `~/.codex/memory/snapshots/{YYYY-MM-DD-HH-MM-SS}-pre-{from_version}-to-{to_version}/`. Tiered retention: keep daily snapshots for 30 days, weekly for 1 year, archive monthly beyond. Implementation can defer until the first real schema change (Phase 2+).
- **Rollback procedure**: if a schema migration corrupts the table, restore from the most recent snapshot. Document the procedure in `specs/2026-05-26-codex-memory-rollback-runbook.md` (separate artifact, can be deferred to Phase 2).

### 5.7.1 Schema version semver progression rules

Codex memory uses semver for `schema_version` in `manifest.json`:

- `0.3.0` — initial v0.3-compatible schema. Includes all six v0.3 columns (`agent_id`, `agent_alias`, `capabilities`, `valid_from`, `valid_to`, `review_after`) plus the existing SC pre-v0.3 columns. Matches SC's v0.3 Phase 1 row shape exactly.
- `0.3.x` — patch versions. May add manifest fields, bridge-health field shape, telemetry log format. **No row-shape change. No tool-surface semantic expansion.** Existing rows remain readable.
- `0.4.0` — minor version bump. Triggered by any one of: row-shape change (add/remove/rename column), new MCP tool with new semantics (e.g., `memory_review_stale`), breaking change in the visibility-filter clause. Requires a `snapshot()` call before migration.
- `1.0.0` — major version. Cross-store wire-format change or incompatible bridge protocol change. Coordinated with SC + ACS major versions.

Server start-time check: read `manifest.schema_version`. If not in supported range (Phase 1 server supports `^0.3.0`, i.e., `>=0.3.0 <0.4.0`), refuse to start with error `MANIFEST_VERSION_UNSUPPORTED` and log expected vs actual.

**OPEN QUESTION**: does SC v0.3 ship a manifest.json or schema_version? The v0.3 spec doesn't currently require one. If not, the cross-store `schema_version` consistency check must initially probe SC's row shape directly (presence/absence of v0.3 columns) and infer the version. This is a one-off probe, not a permanent design. Recommend filing a v0.3.1 patch on SC to add a manifest. This is a sub-project B follow-up.

---

## 6. Cross-cutting concerns

### 6.1 Construct validity of cross-store cosine search (Lens 5)

**SOURCE FACT** [`mit12: book-10-chunk-0066 pp.199-202`]: "Word embeddings are representations of linguistic units; they do not correspond to any linguistic or decision-making task. As such, lacking any notion of ground truth or harms to people, it is not meaningful to ask fairness questions about word embeddings without reference to specific downstream tasks in which they might be used. More generally, it is meaningless to ascribe fairness as an attribute of models as opposed to actions, outputs, or decision processes."

**INFERENCE**: BGE-M3 cosine similarity between embeddings has no intrinsic meaning. Its meaning lives in the downstream task — for the Agentic Memory System, the downstream task is "rank memories by relevance to a query for session-start loading or in-session search." Cross-store cosine comparability is a *proxy* for the construct (relevance to query). The proxy can drift even when the construct hasn't changed — for example, if SC and Codex re-load BGE-M3 from different cached versions (model file updates, quantization differences, BLAS library swaps).

**JUDGMENT for Codex search ranking**: in Phase 1, do **not** merge local and SC search results into a single mixed-cosine ranked list. Return two separate ranked lists with a `provenance` field on each row (`"local"` or `"sc-shared"`). Caller can interleave or weight as needed. Phase 2 can introduce a mixed ranking once cosine-comparability has been empirically validated by running parallel embed-then-search on a fixed query set and measuring rank correlation between the two stores.

**OPEN QUESTION**: what's the acceptable rank correlation threshold (Spearman ρ? Kendall τ?) before mixed ranking is safe? This needs a Phase 2 calibration experiment, not a paper answer.

### 6.2 Concurrency and consistency (Lens 4)

**SOURCE FACT** [`mit12: book-03-chunk-0503 pp.1503-1506`]: "Concurrency and synchronization errors... in distributed or multi-threaded environments, incorrect coordination among parallel processes can lead to race conditions, deadlocks, or inconsistent states. These issues are often tied to the improper use of asynchronous operations, such as non-blocking I/O or parallel data ingestion. Synchronization bugs can corrupt the consistency of training states or produce unreliable model checkpoints."

**JUDGMENT for Codex bridge concurrency**: Phase 1 is **read-only** from Codex's side. SC continues to write to its own LanceDB; Codex never writes to SC's table. This eliminates the entire write-conflict class. Read-only-cross-read concurrency is bounded by LanceDB's append-only manifest semantics — Codex sees a consistent snapshot at query time; SC writes append without invalidating Codex's read. Acceptance test §8.5 T8 must verify this empirically; treat the contract as "trust but verify".

### 6.3 Cold-start dynamics (Lens 6) — OUT OF CORPUS

MIT-12 covers PAC bounds, Rademacher complexity, and cross-validation [book-01-chunk-0012, book-01-chunk-0021] but these address sample complexity for *model selection*, not "when does building an ANN index pay off versus linear scan." The ANN index cold-start question is a vendor/operational issue (LanceDB's index-build threshold and rebuild cost), not a theory question.

**OPEN QUESTION**: at what row count does LanceDB's IVF/HNSW index outperform linear cosine scan for 1024-dim BGE-M3 vectors? Codex memory should start with no index (linear scan) and add the index when row count crosses an empirically-measured threshold. Defer to Phase 2 measurement.

---

## 7. Priority backlog

### Phase 0 — Pre-row bootstrap (before any memory rows exist)

1. **Backup directory structure** — `~/.codex/memory/{identity/, lancedb/, snapshots/, telemetry.jsonl}`.
2. **Identity generation** — ed25519 keypair, derive `agent_id`, set `agent_alias="codex"`.
3. **Manifest creation** — `manifest.json` with `schema_version=0.3.0`, identity, embedding model+dim.
4. **LanceDB table creation** with v0.3 row shape — seed-and-delete pattern per [code: store.ts:150-158].
5. **BGE-M3 warmup** — pre-load model and validate `EMBEDDING_DIM === 1024`.
6. **Schema-version supported-range gate** — server reads manifest at every start; refuses to start outside `^0.3.0`.

### Phase 1 — MCP runtime activation + cross-read bridge (P0)

7. **Node/TypeScript MCP server** scaffold — mirror SC's stdio + Streamable HTTP transports [pattern: index.ts:3-5, http-server.ts:18-20].
8. **10 tools** registered with Codex-side defaults — `memory_save/search/load_session/update/delete/compact/health/stats/task_list/task_update`.
9. **`memory_search` separate-ranked-lists contract** — local list + sc-shared list with provenance.
10. **`ScMemoryBridge` implementation** — direct LanceDB cross-read, `available=false` degradation pattern [pmm-bridge.ts:64, 73-76, 112-113], visibility re-check on every read, `sc:` ID prefix.
11. **`memory_load_session` cross-store loader** — both stores, provenance, predicate-filtered.
12. **`memory_health` extension** — local store + bridge state + `schema_version` + `manifest_path`.
13. **Bridge availability + retry semantics** — startup probe, per-call lazy retry with 60s cooldown (see §5.3.1).
14. **`sc:` ID mutation rejection contract** — `READ_ONLY_BRIDGE_ID` MCP error (see §5.4.1).
15. **`~/.codex/config.toml` registration** — concrete `[mcp_servers.codex-memory]` block per §5.5 step 5.
16. **Phase 1 acceptance test battery** — 8 tests per §8.5. All must pass.

### Phase 2 — Hygiene + telemetry (P1)

17. **`memory_review_stale`** ported once v0.3 temporal columns are live in SC (codex's accepted pushback).
18. **Bridge telemetry** — log every cross-store read with outcome (hit/miss/bridge-down).
19. **Cosine comparability calibration** — fixed-query rank correlation between local re-embed and SC re-embed. Decide mixed-ranking threshold or keep separate.
20. **Snapshot routine implementation** — implement `snapshot()` function. First real test on the first Phase 2/3 schema change.

### Phase 3 — Identity + security hardening (P2)

21. **HTTP localhost bridge** once SC v0.3 auth ships. Migrate from direct LanceDB read.
22. **Key rotation procedure** — rotate ed25519 identity, re-stamp `agent_id` on local rows, document rollback.
23. **Cross-store write protocol** (if ever needed) — signed writes, conflict semantics. Currently NOT planned.

---

## 8. Migration and rollback playbook (for Phase 1)

### 8.1 Bootstrap dry-run

Before first real use, run on a throwaway directory `~/.codex/memory-dryrun/`:

1. Generate identity → confirm `manifest.json` and key files.
2. Create LanceDB table → confirm schema includes all v0.3 columns.
3. Save 10 test rows with varied `agent_alias`, `visibility`, `scope`.
4. Run `memory_search` for each → confirm cosine ranking sensible.
5. Run `memory_health` → confirm `schema_version`, vector dim, row counts.
6. Probe SC bridge → confirm `available=true` and 1+ shared rows visible (if SC has shared rows).
7. Delete `~/.codex/memory-dryrun/` after acceptance.

### 8.2 First production run

1. Backup `~/.codex/config.toml` to `config.toml.pre-codex-memory.bak`.
2. Add `[mcp_servers.codex-memory]` block. Start Codex. Confirm MCP registration via `~/.codex/` logs.
3. Run `memory_health` from a Codex session. Confirm all fields present.
4. Run `memory_load_session` from a Codex session in `project:agentic-memory-system` scope. Confirm at least the 12 cross-shared SC memories are visible (`mem_343df0ac`, `mem_63263e0e`, etc.).
5. Save a Codex-local memory. Confirm SC does NOT see it (Codex's default `visibility="private"`).

### 8.3 Rollback if something breaks

1. Stop Codex.
2. Remove `[mcp_servers.codex-memory]` block from `~/.codex/config.toml`.
3. Move `~/.codex/memory/` to `~/.codex/memory.broken-{timestamp}/` (preserve for forensics).
4. Restart Codex. Confirm Codex operates without memory (degraded but not crashed).
5. File the failure mode in `research/codex-memory-failure-{timestamp}.md` for next iteration.

### 8.4 Schema-change rollback (Phase 2+)

For any later schema rewrite:

1. Call `snapshot()` → snapshot to `~/.codex/memory/snapshots/{timestamp}-pre-{from}-{to}/`.
2. Apply migration. Run acceptance tests.
3. If acceptance fails: stop Codex, move current `lancedb/` to `lancedb.broken/`, copy snapshot back to `lancedb/`, restart, confirm.

### 8.5 Phase 1 acceptance test battery (8 tests, all must pass)

Each test runs against a clean `~/.codex/memory/` (run `bootstrap` first, then the tests in order). Tests live at `tests/phase1-acceptance.ts` (or equivalent) and exit non-zero on any failure.

| # | Test | Setup | Action | Expected outcome |
|---|------|-------|--------|------------------|
| T1 | Local round-trip | Empty Codex store. | `memory_save({content: "lighthouse keeper memory", type: "context"})`, then `memory_search({query: "lighthouse keeper memory", limit: 1})`. | Returns 1 result. `provenance="local"`. `score >= 0.85`. ID is NOT prefixed with `sc:`. |
| T2 | Vector dimension | Empty Codex store. | `memory_save(...)`, inspect the row's vector via `memory_health`. | Vector length === 1024 exactly. Health reports `embedding_dim: 1024`. |
| T3 | Bridge alive | SC LanceDB at `~/.claude/memory/lancedb/` contains ≥1 row with `visibility="shared"`. | `memory_health()`, then `memory_load_session({scope: "global"})`. | `bridge.available === true`. `last_probe_at` is recent. Session results include the SC shared row with `provenance="sc-shared"` and an `sc:`-prefixed ID. |
| T4 | Bridge dead | Set `SC_MEMORY_DB_PATH` to a non-existent path. | Server start + `memory_health()` + `memory_search({query: "x"})`. | `bridge.available === false`. `last_error` is non-null. Server stays up. Search returns local results only (or empty if local is empty). |
| T5 | Private-row leak prevention | SC LanceDB contains a row with `visibility="private"` and known content. | `memory_load_session()` + `memory_search({query: "<known content>"})`. | Neither result includes the SC private row. The bridge-side query MUST include `visibility='shared'` in its predicate. |
| T6 | `sc:` mutation rejection | Bridge alive, SC has shared row `mem_X`. | `memory_update({id: "sc:mem_X", content: "new"})`. | MCP error returned: `isError=true`, content contains JSON with `code="READ_ONLY_BRIDGE_ID"`, `id="sc:mem_X"`. SC row unchanged. |
| T7 | Schema version manifest | Clean bootstrap. | `memory_health()`. | Response includes `schema_version` matching manifest, `manifest_path` valid filesystem path. |
| T8 | Concurrency snapshot | SC writes 100 new rows in a tight loop. | While SC writes, Codex runs `memory_search({query: "...", limit: 50})` repeatedly. | Codex never throws. Each call returns a consistent snapshot (row count may vary between calls but never returns mid-update corruption). |

**All 8 tests are blocking** for Phase 1 implementation-complete declaration. There is no two-tier gate; the previous draft split (5 blocking + 3 production-ready-only) was incoherent. Concurrency test T8 is a probe of LanceDB-Node's two-process semantics — flagged as OPEN QUESTION in §5.3; T8 is the empirical answer.

---

## 9. Source manifest

### 9.1 SC source citations (codex-counsel-grounded)

| File | Lines | What it shows |
|------|-------|---------------|
| `~/.claude/mcp-servers/superclaude-memory/src/store.ts` | 46-49, 150-158 | LanceDB connect + table seed-and-delete pattern |
| | 119 | Table name `agent_memories` |
| | 425, 431, 452, 464, 480 | `memory_load_session` 5-tier loader |
| | 93-100, 109, 526, 546, 556, 567 | Current health-check fields |
| `~/.claude/mcp-servers/superclaude-memory/src/schema.ts` | 84-108 | Current MemoryRow shape (pre-v0.3) |
| | 112-117 | `seedMemoryRow` builds a 1024-length zero vector (`const dim = 1024; vector: Array.from({length: dim}, () => 0)`) — dim is hard-fixed for BGE-M3 |
| | 142, 148, 158, 164 | Zod tool input schemas |
| `~/.claude/mcp-servers/superclaude-memory/src/index.ts` | 3-5 | MCP SDK imports |
| | 26, 28, 33-36 | JSON response + error wrapper |
| | 40-44 | Lazy LanceDB initialization |
| | 51, 78, 136, 164, 181, 211, 230, 245, 260, 291 | 10 tool registrations |
| `~/.claude/mcp-servers/superclaude-memory/src/http-server.ts` | 18-20 | Streamable HTTP transport |
| | 359-376 | Unauthenticated `/mcp` and `/notify` (auth deferred to v0.3) |
| | 424 | BGE-M3 loaded on first use |
| `~/.claude/mcp-servers/superclaude-memory/src/pmm-bridge.ts` | 64, 73-76 | `available=false` degradation pattern |
| | 82, 88, 89, 98 | LanceDB connect + table open in same process |
| | 112-113 | Returns `[]` when unavailable |
| | 214, 218, 231 | `mapRow` drops agent_id (BUG to fix in Codex bridge) |
| `~/.claude/mcp-servers/superclaude-memory/src/notify-handler.ts` | 22, 25 | Inbound payload carries agent_id |
| | 118, 124-126 | Save drops identity, hardcodes visibility='shared' (notify-handler gotcha) |
| `~/.claude/mcp-servers/superclaude-memory/src/embeddings.ts` | 1-10 | BGE-M3 exports, 1024-dim |
| `~/.claude/mcp-servers/superclaude-memory/src/config.ts` | 9-11 | `dimension: 1024` runtime fix |
| `~/.claude/mcp-servers/superclaude-memory/src/migration.ts` | 15-19 | `.claude`-rooted paths (DO NOT reuse for Codex) |
| | 701, 710, 712 | Backup + rename pattern (not applicable to clean-slate bootstrap) |

### 9.2 Prior-art docs

- `specs/2026-05-26-sc-memory-v0.3-upgrade-spec.md` — v0.3 row shape (schema additions), visibility filter, Phase 0-4 plan
- `research/2026-05-26-superclaude-memory-deep-review-v3-final.md` — v3 review, comparison matrix, ranked backlog
- `research/codex-counsel-C-output.md` — verbatim codex consult for this spec (15,279 chars)

### 9.3 MIT-12 chunk citations

- `mit12: book-09-chunk-0050 pp.205-208` — Table 7.2: free vs general communication complexity classes (Q3 bridge transport)
- `mit12: book-04-chunk-0136 pp.570-573` — free communication definition (Q3)
- `mit12: book-03-chunk-0381 pp.1157-1160` — correction cascades, power-law downstream cost (Q7 schema versioning)
- `mit12: book-03-chunk-0386 pp.1171-1173` — canary, blue-green, rollback procedures (Q7)
- `mit12: book-03-chunk-0145 pp.442-444` — tiered retention storage architecture (Q7 tiered snapshot policy)
- `mit12: book-03-chunk-0146 pp.444-446` — incremental migration pattern (Q5)
- `mit12: book-03-chunk-0503 pp.1503-1506` — concurrency/sync error propagation (§6.2)
- `mit12: book-10-chunk-0066 pp.199-202` — embeddings have no ground truth without downstream task (§6.1 construct validity)

Out-of-corpus flag: Lens 6 (cold-start ANN index growth) — MIT-12 covers PAC/Rademacher but not vector-index operational thresholds. Deferred to Phase 2 empirical measurement.

### 9.4 Memory MCP entries used as inputs

- `mem_343df0ac` — Project state (A+B VERIFIED, C next)
- `mem_63263e0e` — v0.3 schema additions (locked for interop)
- `mem_39845e9e` — Working directory rule (`C:\Dev\Builds\Agentic Memory System\`, NEVER Waki)
- `mem_a4af3f41` — ACS sub-project D design constraints (relevant to Phase 3 HTTP transport when ACS lands)
- `mem_0f8bfb76` — Mandatory verification gate between sub-projects
- `mem_5b8a31b1` — dual-counsel skill procedure
- `mem_13ab8d10` — Codex CLI Windows gotchas (applied during this session)

### 9.5 External tool versions used

- codex-cli: 0.128.0 (consult mode + verification mode; not in known-bad list)
- MIT-12 CLI: `C:\Dev\research\MIT\MIT 12 Research\.venv\Scripts\python.exe` + `tools\mit12_cli.py`
- LanceDB-Node: `@lancedb/lancedb` (version per SC's `package.json`; verify match)
- BGE-M3: 1024-dim, local model (per SC's embeddings.ts)

---

_End of spec. Awaiting Step 6 codex strict-review verification before sub-project D unlocks._
