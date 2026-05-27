# Codex Strict-Review Verification - Sub-Project C (Codex Memory MCP Design)

_Source: codex exec 0.128.0 strict-review mode_
_Event counts: {'thread.started': 1, 'turn.started': 1, 'item.completed': 21, 'item.started': 17, 'turn.completed': 1}_
_Agent message counts: [228, 162, 163, 9301]_

---

# Check 1 Coverage — per item

**Hard constraints**

- Storage TBD via dual-counsel: **IN DELIVERABLE**. §5.1 chooses LanceDB-Node and rejects SQLite-vec, DuckDB-VSS, pgvector.
- Schema inherits v0.3 Phase 1 row shape: **IN DELIVERABLE**. §2.3 and §5.5 require `agent_id`, `agent_alias`, `capabilities`, `valid_from`, `valid_to`, `review_after`, plus canonical read filter.
- Embedding BGE-M3 1024-dim: **IN DELIVERABLE**. §5.1, §5.2, §5.5 use BGE-M3 / 1024-dim.
- Identity `agent_id = sha256(ed25519_pub_key)`, alias `codex`: **IN DELIVERABLE**. §5.5 bootstrap step 1.
- Deployment Option B, two stores on same box with bridge protocol: **IN DELIVERABLE**. §1 and §5.3.
- MCP registration in `~/.codex/config.toml`, mirror SC’s 10 tools: **IN DELIVERABLE**. §5.4 and §5.5 step 5.
- Bridge extends `pmm-bridge.ts`, enforces `visibility='shared'`, preserves `agent_id`: **IN DELIVERABLE**. §5.3 explicitly calls out all three.

**Soft questions**

- Storage substrate: **IN DELIVERABLE**. §5.1 answers LanceDB-Node.
- Runtime Node vs Python: **IN DELIVERABLE**. §5.2 answers Node/TypeScript.
- Bridge transport: **IN DELIVERABLE**. §5.3 answers direct LanceDB cross-read.
- Migration story for existing Codex skill-data at `~/.codex/skills/`: **IN DELIVERABLE**. §2.4 says there is no `~/.codex/skills/`; §5.5 treats automations as future ingestion candidates, not migration inputs. This is enough for the spec, assuming that prior current-state claim was verified in the producing session.

# Check 2 Internal consistency — contradictions found

1. **Bridge phase numbering contradiction.**  
   §5.3 says HTTP localhost bridge is Phase 2+ after SC v0.3 auth ships. §7 places HTTP localhost bridge in Phase 3. Same direction, inconsistent phase label. Patch needed.

2. **Phase 0 vs Phase 1 bootstrap contradiction.**  
   §1 says backup/schema-version protocol should be Phase 0 “alongside bootstrap.” §7 Phase 0 includes identity generation and memory directory structure. But §5.5 labels identity generation, manifest creation, LanceDB table creation, BGE-M3 warmup, MCP registration, bridge probe, and acceptance test as “Phase 1, in order.” This leaves identity/manifest split across Phase 0 and Phase 1. Patch needed: define Phase 0 as pre-row bootstrap, and Phase 1 as MCP/tool/runtime activation, or move identity/manifest consistently.

3. **Search result ranking contradiction.**  
   §5.4 says `memory_search` should “merge results local-first.” §6.1 says Phase 1 should not merge local and SC search results into one mixed-cosine ranked list, and should return two separate ranked lists with provenance. Patch needed: choose separate lists for Phase 1, or define “merge” as envelope-level aggregation, not ranking merge.

# Check 3 Grounding — cites spot-checked PASS/FAIL

- `notify-handler.ts:22,25,118,124-126` — **PASS**  
  Actual content:
  ```ts
  22:const NotifyPayloadSchema = z.object({
  25:  agent_id: z.string().min(1),
  118:    const saveResult = await store.save({
  124:      source_type: "bridge",
  125:      visibility: "shared",
  126:      task_data: payload.task_data as any,
  ```
  The claim is accurate: inbound payload has `agent_id`; save call does not pass it and hardcodes shared visibility.

- `pmm-bridge.ts:214,218,231` — **PASS**  
  Actual content:
  ```ts
  214:  private mapRow(row: PmmRow): SearchResult {
  218:    return {
  231:    };
  ```
  The returned object includes `id`, `content`, `type`, `scope`, `priority`, `topics`, `status`, `score`, timestamps, `access_count`, `task_data`; no `agent_id`. The claim is accurate.

- `store.ts:150-158` — **PASS**  
  Actual content:
  ```ts
  150:    this.db = await lancedb.connect(dbPath);
  153:    if (tables.includes(MEMORIES_TABLE)) {
  156:      const seed = seedMemoryRow(this.config.embedding.model);
  157:      this.table = await this.db.createTable(MEMORIES_TABLE, [seed]);
  158:      await (this.table as any).delete('id = "__schema__"');
  ```
  The seed-and-delete table creation claim is accurate.

- `schema.ts:112-117` — **FAIL / overclaim**  
  Actual content:
  ```ts
  112:export function seedMemoryRow(_embeddingModel?: string): MemoryRow {
  113:  const dim = 1024; // BGE-M3 via @openclaw/local-embeddings
  117:    vector: Array.from({ length: dim }, () => 0),
  ```
  This supports “1024-dim seed vector,” but not the exact claim “1024-dim FixedSizeList.” The cited source does not mention `FixedSizeList`.

- `index.ts:51,78,136,164,181,211,230,245,260,291` — **PASS with line-label caveat**  
  Actual lines are tool section headers:
  ```ts
  51:  // --- Tool 1: memory_save ---
  78:  // --- Tool 2: memory_search ---
  136:  // --- Tool 3: memory_update ---
  164:  // --- Tool 4: memory_delete ---
  181:  // --- Tool 5: memory_load_session ---
  211:  // --- Tool 6: memory_stats ---
  230:  // --- Tool 7: memory_health ---
  245:  // --- Tool 8: memory_compact ---
  260:  // --- Tool 9: memory_task_list ---
  291:  // --- Tool 10: memory_task_update ---
  ```
  These lines do identify the 10 registered tools, but the actual `server.tool(` calls are usually the next line. Good enough for tool-surface grounding, but patching to cite the `server.tool(` lines would be cleaner.

- `migration.ts:15-19` — **PASS**  
  Actual content:
  ```ts
  15:const HOME = homedir();
  16:const CLAUDE_MEMORY = join(HOME, ".claude", "memory");
  17:const CLAUDE_PROJECTS = join(HOME, ".claude", "projects");
  18:const OPENCLAW_WORKSPACE = join(HOME, ".openclaw", "workspace", "memory");
  19:const OPENCLAW_DOCS = join(HOME, ".openclaw", "docs");
  ```
  The `.claude`-rooted path claim is accurate.

# Check 4 Missing artifacts — gaps

- Acceptance tests are under-specified. “Round-trip cosine > 0.7” is not enough. Need exact test command, fixture rows, expected response shapes, dimension assertion, bridge-down behavior, private-row leak test, `sc:` mutation rejection test, manifest/schema health test, and concurrency probe.
- Schema version semver progression is missing. Spec starts at `0.3.0` but does not define when `0.3.1`, `0.4.0`, etc. are required.
- Bridge availability probe semantics are incomplete. §5.5 says probe on first start; §3 says caller needs telemetry. It does not decide read-once-at-start vs retry per call vs retry with cooldown/backoff.
- Concrete `~/.codex/config.toml` registration is incomplete. Env names are listed, but defaults and the actual TOML block are not specified.
- Rejected `sc:` ID mutation semantics are missing. Spec says reject `sc:` IDs, but not HTTP/MCP error shape, status code, error code, or whether `updated:false`/`deleted:false` is acceptable.
- Feature flag for bridge is partly present but not specified enough. `CODEX_MEMORY_BRIDGE_ENABLED` is named, but default, parse rules, health output, and runtime behavior when disabled are not fully defined.
- Manifest compatibility behavior is incomplete. Spec says refuse if unsupported, but not exact supported range, error message, migration prompt, or read-only degraded mode.
- Bridge result contract needs tightening. Provenance, prefixed IDs, preserved `agent_id`, visibility-filter evidence, and separate-vs-merged result shape should be written as response schemas, not prose.

# Patches needed (ordered by importance)

1. **Resolve Phase 0/Phase 1 ownership of identity, manifest, bootstrap, and table creation** — judgment-call.  
   Current spec splits the same bootstrap work across phases.

2. **Fix Phase 1 search result contract: separate ranked lists vs merged local-first list** — judgment-call.  
   This affects API shape and downstream caller expectations.

3. **Define acceptance tests concretely** — mechanical plus judgment-call.  
   Add commands, fixtures, expected outputs, and pass/fail criteria for local save/search, bridge visibility, bridge unavailable, `sc:` mutation rejection, schema health, and concurrency.

4. **Define bridge availability semantics** — judgment-call.  
   Pick startup-only, per-call retry, or cooldown retry. I would use startup probe plus per-call lazy retry with short cooldown and expose `last_probe_at`, `last_error`, `available`.

5. **Specify `~/.codex/config.toml` block and env defaults** — mechanical.  
   Include exact TOML, env names, defaults, and bool parsing.

6. **Specify rejected `sc:` mutation error contract** — mechanical.  
   Example: MCP tool returns `isError: true` with `{code:"READ_ONLY_BRIDGE_ID", id, message}`; HTTP wrapper maps to 400 if exposed over HTTP.

7. **Define semver progression rules** — judgment-call.  
   Example: `0.3.0` initial v0.3-compatible schema; `0.3.1` manifest/bridge-health patch with no row-shape change; `0.4.0` any row-shape/tool-surface semantic expansion.

8. **Patch inaccurate/loose cites** — mechanical.  
   Replace “FixedSizeList” with “1024-length seed vector inferred by LanceDB,” or cite a source that actually proves FixedSizeList. Optionally move index cites to the exact `server.tool(` lines.

# Readiness verdict: PATCH-FIRST

The design is directionally coherent and covers the requested hard constraints and soft questions. It is not ready to hand to implementation yet because the phase ownership, search response contract, acceptance tests, bridge retry behavior, config defaults, and `sc:` rejection semantics are still underspecified.