# Subplan A Repair Review

**Date:** 2026-05-27
**Scope:** A only - SC memory deep review v3 as a design-only research artifact.
**Trigger:** Hammad reported implementation drift and asked for one subplan at a time.

## Verdict

Subplan A is substantively sound as a 2026-05-26 baseline review, but it had drift hazards that could mislead the next agent:

- old subplan labels in the A documents still mapped Codex memory to B and ACS to C;
- `AGENTS.md` pointed to non-existent `.Codex` paths for `dual-counsel` and SC memory;
- root docs still presented the 2026-05-26 "no implementation started" state without pointing to the 2026-05-27 runtime handoff;
- A's `[code:]` facts are now historical baseline facts, because B/C/D implementation changed SC schema, auth, visibility, dedup, and tools.

Repairs were applied in place. **Post-repair status: READY for its intended role as the historical design review**, not as the current runtime source of truth.

## Repairs Applied

| File | Repair |
|---|---|
| `AGENTS.md` | Corrected `.Codex` paths to `C:\Users\7amma\.claude\...`; added current-state note pointing to `sessions/2026-05-27-session-handoff.md`. |
| `CLAUDE.md` | Added current-state note pointing to `sessions/2026-05-27-session-handoff.md`. |
| `research/2026-05-26-superclaude-memory-deep-review-v3-final.md` | Corrected downstream labels: C = Codex memory, D = ACS. |
| `research/2026-05-26-superclaude-memory-deep-review-v2-mit12.md` | Corrected old B/C label drift for Codex memory and ACS references. |
| `research/2026-05-26-superclaude-memory-deep-review.md` | Corrected old B/C label drift in scoping notes. |

## Strict-Review Gate

Codex CLI strict-review returned `PATCH-FIRST`.

Main findings from that pass:

1. Coverage was acceptable for A's intended design-only review scope.
2. Current labels were wrong in the A docs.
3. `.Codex` vs `.claude` paths conflicted.
4. Current-source spot-checking failed inside the Codex CLI sandbox, so I completed the source spot-check directly from this session.

The strict-review transcript is summarized here rather than treated as final authority, because it could not read the live SC source path under `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\src\`.

## Current Source Spot-Check

| A claim | Current source check | Result |
|---|---|---|
| SC row schema was a 21-column baseline. | `schema.ts:94` still has `visibility`; `schema.ts:111-116` now adds `agent_id`, `agent_alias`, `capabilities`, `valid_from`, `valid_to`, `review_after`. | Historical only. A was correct for the reviewed baseline, not current runtime. |
| Visibility was present but unenforced. | `store.ts:64-92` defines visibility/temporal filters; search paths apply them at `store.ts:590`, `store.ts:642`, and task list at `store.ts:1058`. | Historical only. B implementation addressed this. |
| Dedup used `findCandidates` + JS cosine with a hard 100-candidate bound. | Legacy path still exists at `store.ts:1186-1198`, but `config.ts:30-33` defaults `dedupMode` to `dual`; `store.ts:306-339` runs the rollout branch; `store.ts:459-504` implements ANN dedup with telemetry. | Historical only with legacy fallback. |
| HTTP listener had no auth. | `http-server.ts:343-365` defines token-gated auth; `http-server.ts:447` and `http-server.ts:454` reject unauthorized `/mcp` and `/notify` when enabled. | Historical only; current auth is conditional on env. |
| SC tool surface was 10 MCP tools. | `index.ts:88-337` still lists the original 10 tools; current source adds `memory_review_stale` at `index.ts:367`, `acs_send` at `index.ts:395`, and `acs_inbox` at `index.ts:463`. | Historical baseline; current surface is larger. |
| Identity was future work. | `identity.ts:4-16` documents persisted ed25519 identity, `identity.ts:57` derives sha256, and `identity.ts:129-133` refuses manifest/public-key mismatch. | Historical only; B implementation added identity. |

## Remaining Caution

Do not use A's v1/v2 source-cited sections as a current implementation audit. Use them as the design baseline that produced B/C/D. For current runtime truth, start from `sessions/2026-05-27-session-handoff.md`, then inspect the live source under `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\src\`.

Next subplan to review: B, the SC v0.3 implementation.
