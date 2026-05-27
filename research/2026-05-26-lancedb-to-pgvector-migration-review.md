# LanceDB → Postgres+pgvector Migration Review

**Author:** Claude (dual-counsel skill applied: MIT-12 corpus + Codex-prompt-design dry-run)
**Date:** 2026-05-26
**Subject:** Migrating personal `superclaude-memory` from single-table LanceDB to Supabase Postgres+pgvector for multi-machine access.
**Reviewed:** `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\src\{schema.ts, store.ts, config.ts, embeddings.ts, lifecycle.ts}`; live store at `~/.claude/memory/lancedb\agent_memories.lance` (14 MB, **897 fragmented data files**).

---

## §0 Executive verdict

**Goal sound; plan as written is not safe.** Step 3 (re-embed via Python BGE-M3) is gratuitous and the highest-risk decision — copy vectors verbatim. The plan is a blue-green cutover **with no shadow phase**, and one week of dual-run is too short. Single-writer → multi-writer is a **consistency-model change**, not a storage swap; `store.ts:save()` is not atomic enough for it. Do not start until §5's Stop conditions are answered.

## §1 Source-code invariants the target must preserve

1. **1024-dim BGE-M3 vectors** (`config.ts:11`, `schema.ts:114`). `vector(1024)` + HNSW or IVFFlat.
2. **Supersession DAG** — `supersedes`/`superseded_by` (`store.ts:763`). Postgres should enforce as FKs; LanceDB doesn't, hence `getHealth()` orphan count (`store.ts:551`).
3. **Dedup thresholds** — 0.92 skip / 0.75 supersede over ≤100 same-(type,scope) candidates (`store.ts:177-223`). Pgvector's HNSW recall is ~0.95 default; thresholds may behavior-flip unless `ef_construction ≥ 200`.
4. **Lifecycle backups** before each compact (`lifecycle.ts:49`). Postgres equivalent: `pg_dump` per pass, not a no-op.
5. **JSON-serialized `topics` / `task_data`** → migrate to `jsonb`, not `text`; this turns `topics.includes(t)` into `topics @> '[$t]'`.

## §2 Plan critique

| # | User's step | Verdict |
|---|---|---|
| 3 | Re-embed via Python BGE-M3 | **DO NOT.** Different tokenizer/normalize/pool config → drifted vectors; dedup misbehaves silently. **Copy verbatim** from LanceDB. |
| 4 | Cut over MCP adapter | Premature; must follow shadow-read parity (§5 G3). |
| 5 | 1-week dual-run then delete LanceDB | Too short, too binary. See gates G3–G6. |
| 1 | JSON dump | Use Arrow IPC/Parquet — JSON loses fixed-size vector type fidelity. |
| 2 | Provision Supabase | Add pre-flight: pgvector ≥0.7, `vector(1024)`, backup cron live before any insert. |

## §3 MIT-12 corpus grounding

**SOURCE FACT** [`mit12: book-03-chunk-0142 pp.434-437`]: "*A PostgreSQL database handling structured user attributes ... provides millisecond lookups*" but warehouses "*struggle with truly unstructured data ... schema evolution becomes painful*."
**INFERENCE**: Postgres is right for a 21-column transactional record set; pgvector closes the vector-search gap. Reddi's caveat is about training-scale scans, not your workload.

**SOURCE FACT** [`book-03-chunk-0145 pp.442-444` + `book-03-chunk-0386 pp.1171-1173`]: Shadow → canary → blue-green; "*robust rollback procedures are essential.*"
**JUDGMENT**: Plan skips shadow. Insert it: every `save` writes both; every `search` returns LanceDB and diffs Postgres; flip only after diff empty N days.

**SOURCE FACT** [`book-03-chunk-0437 pp.1311-1313`]: "*periodic checkpointing and rollback ... revert to a known good state.*"
**JUDGMENT**: `cp -r lancedb lancedb.snapshot-pre-pgvector` + `pg_dump` at every gate. Do not delete LanceDB for ≥30 days post-cutover.

**SOURCE FACT** [`book-03-chunk-0429 pp.1291-1294`]: FedAvg treats multi-client writes to one logical state as explicit aggregation policy, not a free property.
**JUDGMENT**: add `client_id`/`created_by_machine` columns; gate dedup hot path (`store.ts:177-223`) with `SELECT … FOR UPDATE` or `pg_advisory_xact_lock`. Current sequence is a textbook **lost-update window** under multi-writer.

**OPEN QUESTION**: cross-machine clock skew on `updated_at`. Corpus doesn't answer. Either single-writer-funnel or `SERIALIZABLE` for supersede, eventual elsewhere.

## §4 Codex prompt I would send (dry-run, per skill instruction)

"Read `~/.claude/mcp-servers/superclaude-memory/src/store.ts` (focus: `save`, `findCandidates`, `markSuperseded`, `upsertRow`) + `schema.ts`. User proposes migrating this single-writer LanceDB store to multi-writer Supabase Postgres+pgvector, with a Python re-embedding step and 1-week dual-run. Answer independently: (1) Is re-embedding via a *different* BGE-M3 lib safe — where in `store.ts` would cosine drift surface first? (2) Which lines assume single-writer semantics; minimal SQL primitives (advisory lock / `FOR UPDATE` / `ON CONFLICT`) to preserve them? (3) One missing item I haven't covered. End with one pushback."

**Expected**: 800–1200 words, three numbered answers + pushback. High-value expected catches: (a) `markSuperseded` is a lost-update bug latent under multi-writer; (b) HNSW recall ~0.95 means the 0.92 threshold flips behavior unless index tuned; (c) `mergeInsert` (`store.ts:857`) is single-machine-OK but needs `ON CONFLICT (id)` semantics in Postgres.

## §5 Migration playbook I would execute instead

| Gate | Action | Acceptance / Stop |
|---|---|---|
| G0 | `cp -r lancedb lancedb.snapshot-2026-05-26` + `memory_health` baseline | snapshot count == live; no orphans |
| G1 | Provision Supabase + pgvector; create schema 1:1 with `MemoryRow` | `\d agent_memories` matches; 10-row round-trip passes |
| G2 | **Vector-preserving** dump-and-load (Arrow IPC, NO re-embed) | row counts equal; 50-row cosine matches to 1e-6; all `supersedes` FKs resolve |
| G3 | **Shadow read** via `SHADOW_READ=1` flag, diff top-10 to `~/.claude/memory/shadow-diff.jsonl` | 7 days, diff < 0.5% on top-1, < 2% on top-10 |
| G4 | **Dual-write**; LanceDB canonical for reads | 7 days, zero `memory_stats` divergence; concurrent-save dedup test passes |
| G5 | Flip canonical to Postgres; LanceDB read-only mirror; `SUPERCLAUDE_USE_LANCEDB=1` reverts instantly | 30 days clean |
| G6 | Delete LanceDB; retain off-machine `pg_dump` | — |

**Stop conditions before G2**: (a) one machine writing or many concurrently? (b) who owns Supabase backups and where? (c) rollback SLA if Postgres is down mid-session? If any are vague, do not start.

## §6 Source manifest

- Code: `~/.claude/mcp-servers/superclaude-memory/src/{schema.ts:84-138, store.ts:164-233, 730-799, 857; lifecycle.ts:49-100; config.ts:11; embeddings.ts:6-11}`
- Store: `~/.claude/memory/lancedb/agent_memories.lance` (897 data fragments, 14 MB)
- MIT-12: `book-03-chunk-0142 pp.434-437`; `book-03-chunk-0145 pp.442-444`; `book-03-chunk-0386 pp.1171-1173`; `book-03-chunk-0437 pp.1311-1313`; `book-03-chunk-0429 pp.1291-1294`
- Skill: `~/.claude/skills/dual-counsel/SKILL.md`
- Prior reviews (synthesis template): `~/.claude/research/2026-05-26-superclaude-memory-deep-review-v3-final.md`
