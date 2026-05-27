# Codex Strict-Review Verification PASS 2 - Sub-Project C

_Re-verification after applying 8 patches from pass 1_
_Agent messages lengths: [189, 141, 206, 304, 185, 3815]_

---

# Per-patch re-verification

| Patch | Verdict | Evidence |
|---|---|---|
| PATCH 1 | RESOLVED | §5.5 now splits **Phase 0 pre-row bootstrap** identity/manifest/table/BGE-M3 warmup at lines 193-198 and **Phase 1 MCP runtime activation** at lines 200-230; §7 mirrors that split at lines 304-324. |
| PATCH 2 | PARTIALLY RESOLVED | §5.4 `memory_search` now says two separate ranked lists with provenance at line 151 and §6.1 matches at line 284, but line 183 still leaves this as an **OPEN QUESTION** and points to the wrong section (`§5.7`) instead of treating the decision as closed. |
| PATCH 3 | RESOLVED | §8.5 now has an 8-test setup/action/expected table covering local round-trip, dimension, bridge alive/dead, private leak, `sc:` rejection, schema version, and concurrency at lines 385-392. |
| PATCH 4 | RESOLVED | §5.3.1 specifies startup probe, per-call lazy retry with 60s cooldown, disabled mode, and exposes `available`, `last_probe_at`, `last_error` at lines 128-136. |
| PATCH 5 | RESOLVED | §5.5 step 5 includes a concrete `[mcp_servers.codex-memory]` TOML block and env defaults table at lines 202-227. |
| PATCH 6 | RESOLVED | §5.4.1 gives the MCP error payload with `isError: true` and `code: "READ_ONLY_BRIDGE_ID"` at lines 161-176. |
| PATCH 7 | RESOLVED | §5.7.1 defines `0.3.0`, `0.3.x`, `0.4.0`, `1.0.0`, plus supported range and `MANIFEST_VERSION_UNSUPPORTED` behavior at lines 263-270. |
| PATCH 8 | PARTIALLY RESOLVED | §9.1 source manifest wording is corrected to “1024-length zero vector” at line 412, but the same unsupported `FixedSizeList` overclaim still remains in §5.1 at line 95. |

# Any new contradictions introduced

- `memory_search` decision is still internally inconsistent: line 151 and line 284 decide “two separate ranked lists,” while line 183 still asks whether to blend into one ranked list or return separate lists.

- HTTP bridge phase label is still inconsistent: line 140 says “Phase 2+ migrates to HTTP localhost,” while §7 puts HTTP localhost bridge in Phase 3 at lines 333-335.

- Schema version compatibility is inconsistent: line 256 says refuse if `schema_version ≠ runtime-supported version`, but line 270 says Phase 1 supports the semver range `>=0.3.0 <0.4.0`.

- Acceptance-test gating contradicts itself: §8.5 says “8 tests, all must pass” at line 379, but line 394 says T4, T5, and T8 can wait until “production ready.” If Phase 1 must be implementation-ready, this should be one gate, not two.

- Cross-reference error: line 292 says acceptance test in `§5.5.7`, but the acceptance test battery is `§8.5`.

# Cite re-check

- `schema.ts:112-117`: actual source supports `const dim = 1024` and `vector: Array.from({ length: dim }, () => 0)`. The corrected §9.1 source manifest wording is accurate.

- Remaining cite error: §5.1 line 95 still says “1024-dim FixedSizeList” and cites `schema.ts:112-117`. That source does **not** mention `FixedSizeList`; this exact overclaim still needs removal outside §9.1.

- `pmm-bridge.ts` spot-check remains accurate: it exposes `available=false`, degrades to `[]`, and `mapRow()` returns no `agent_id`.

- `notify-handler.ts` spot-check remains accurate: inbound payload includes `agent_id`, but the save call omits it and hardcodes `visibility: "shared"`.

# Remaining gaps

- Remove or resolve the stale `memory_search` OPEN QUESTION at line 183.

- Remove `FixedSizeList` from §5.1 line 95 or replace it with “1024-length seed vector.”

- Normalize HTTP bridge phase label: choose Phase 2+ or Phase 3 and use it consistently.

- Fix schema-version wording so §5.7 and §5.7.1 both use the same supported-range rule.

- Fix bad cross-reference `§5.5.7` to `§8.5`.

- Decide whether all 8 acceptance tests block Phase 1 or whether T4/T5/T8 are a later production-readiness gate.

# Readiness verdict: PATCH-FIRST