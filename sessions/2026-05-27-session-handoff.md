# Session handoff — 2026-05-27

**Operator:** Hammad
**Previous session:** built B Phase 1-4, C Phase 0-2, D Phase 1-2 + ran codex strict-review for each phase
**Stopped at:** 89% context, mid-debugging a real identity-mismatch bug surfaced by the first live e2e test

---

## TL;DR for the new session

The implementation is mostly READY per codex strict-review (38/38 tasks completed). **But the first live `acs_send` end-to-end test exposed a real runtime bug**: SC's HTTP server is running with a **different ed25519 identity** than what's on disk, so envelopes signed by the stdio MCP are rejected by ACS as `SENDER_UNKNOWN`.

**One-command fix below in §"Next session step 1".**

---

## What's verified READY (codex strict-review)

| Phase | Tests passing | Codex passes | Verdict file |
|-------|---------------|-------------|--------------|
| B Phase 1 (v0.3 schema + identity + visibility/temporal filter + auth) | 14/14 | 3 | `specs/sc-memory-v03-impl-verification.md` |
| B Phase 2 (13 named telemetry metrics + alerts) | 16/16 | 4 | (inline in pass-2 codex output transcript) |
| B Phase 3 (per-type review_after + memory_review_stale) | (covered in B1+B2) | 2 | (inline) |
| B Phase 4 (combined-filter ANN + dedup_mode rollout flag) | (covered) | 2 | (inline) |
| C Phase 1 (10 MCP tools + ScMemoryBridge) | 11/11 | 2 | `specs/codex-memory-impl-verification.md` |
| C Phase 2 (review_stale + bridge JSONL log + snapshot) | 6/6 | 3 | (inline) |
| D Phase 1 (envelope + ed25519 + JCS + replay + fail-closed + side-effect bridge) | 15 unit + 5 integration | 3 | `specs/acs-impl-verification.md` |
| D Phase 2 (conv lifecycle + 2-tier rate limit + bridge event telemetry) | (covered) | 4 | `specs/acs-phase2-impl-verification-pass2.md` (reconstructed) |

Total **~67 tests passing**, all builds clean (B/C/D each `npx tsc` exit 0).

---

## REAL bug surfaced by live e2e — identity mismatch

```
$ mcp__superclaude-memory__acs_send → {"ok":false,"error":{"code":"-32000","reason":"SENDER_UNKNOWN"}}

$ tail -1 ~/.acs/data/event-log/events.jsonl
{"sender_agent_id":"60a31edf...","sig_verify_state":"skipped","note":"SENDER_UNKNOWN — fail-closed"}

$ curl http://127.0.0.1:18800/.well-known/agent-card.json | grep agent_id
"agent_id": "b7502fd1..."

$ python -c "import hashlib; print(hashlib.sha256(open('~/.claude/memory/identity/sc.ed25519.pub','rb').read()).hexdigest())"
60a31edf...

$ cat ~/.claude/memory/identity/manifest.json
{"agent_id":"60a31edf...","created_at":1779824940258,...}
```

**Root cause:** my B Phase 1 acceptance tests, in their first run BEFORE I added the `SC_IDENTITY_PATH` env override, generated identity files directly under `~/.claude/memory/identity/` overwriting whatever was there. The disk now has identity `60a31edf...`. But a long-running HTTP SC process (PID 16492, hidden from CommandLine column) is still serving the OLD cached identity `b7502fd1...`. New stdio SC processes load fresh from disk = `60a31edf`. ACS pinned `b7502fd1` from SC's served Agent Card at startup.

**Three identities on the box right now:**

| Source | agent_id | Where it lives |
|--------|----------|----------------|
| Disk (`sc.ed25519.pub` + manifest) | `60a31edf689eafa9b4ebcf91063f0c0f75b1be1aa2dc48c1def8643433d88c66` | `~/.claude/memory/identity/` |
| Running HTTP SC (PID 16492) served card | `b7502fd1fe148218c38f216b795fd39335db532ebb674a367c635d4a770fdfb0` | in-memory cache only |
| ACS's pinned Claude pub_key | `b7502fd1...` (matches running card) | ACS in-memory registry |

Codex identity is consistent: `5a97dd00...` everywhere.

---

## Live runtime state right now

- **ACS relay**: RUNNING on `:18801` (started this session). Health endpoint shows both agents loaded with `has_pub_key: true`. `bridge_event_telemetry`, `rate_limit_buckets`, `conversations_*` all surface in `/health`. PID will be visible via `Get-NetTCPConnection -LocalPort 18801`.
- **SC HTTP**: RUNNING on `:18800`, PID 16492 (hidden CommandLine — likely started by Windows service or detached parent). Serving STALE identity.
- **SC stdio MCP**: 4 fresh processes killed this session; will respawn lazily when Claude Code / Cursor / Codex CLI next invoke a tool.
- **Codex memory MCP**: registered in `~/.codex/config.toml` (line 283); not currently invoked from anywhere yet.

---

## Next session step 1 — the identity fix

```powershell
# 1. Kill the hidden HTTP SC listener (still on b7502fd1)
Stop-Process -Id 16492 -Force   # or whatever PID Get-NetTCPConnection -LocalPort 18800 returns

# 2. Confirm port is free
curl http://127.0.0.1:18800/health  # should fail

# 3. Decide which identity to keep:
#    Option A: keep the disk identity (60a31edf — what stdios load)
#              just start a fresh HTTP server, it'll read disk and serve 60a31edf
#    Option B: keep b7502fd1 by recovering the .key bytes from a memory dump (NOT recommended — destroys keypair atomicity)
#    GO WITH OPTION A.

# 4. Start fresh SC HTTP server
cd C:\Users\7amma\.claude\mcp-servers\superclaude-memory
Start-Process node -ArgumentList "dist/http-server.js" -WindowStyle Hidden
# (or whatever launches the HTTP transport — check src/http-server.ts entry point)

# 5. Verify identity convergence
curl http://127.0.0.1:18800/.well-known/agent-card.json | grep agent_id
# expected: 60a31edf...

# 6. Kill ACS so its registry resets (it'll re-fetch SC's card on restart)
Get-NetTCPConnection -LocalPort 18801 | Stop-Process -Force

# 7. Restart ACS
cd C:\Users\7amma\.acs\server
Start-Process node -ArgumentList "dist/index.js" -WindowStyle Hidden
sleep 2
curl "http://127.0.0.1:18801/health" | grep agent_id
# expected: Claude=60a31edf, Codex=5a97dd00, both has_pub_key=true

# 8. Re-run the live e2e from this session
# (from a fresh Claude Code session that respawned SC stdio)
mcp__superclaude-memory__acs_send --recipient codex --message_type second_opinion.request ...
# expected: {"ok":true, "delivered_to":0, "ack":{"acked_message_id":...}}

# 9. Poll ACS inbox for codex agent_id to confirm envelope landed
curl "http://127.0.0.1:18801/inbox?agent_id=5a97dd00..."
```

---

## Other session's status table — corrections

The other session ran live probes but read **pre-patch** verification files for several claims. Correct entries:

| Claim from other session | Live evidence |
|--------------------------|---------------|
| "D Phase 1 fail-open verification" | FALSE. `index.ts:145, 150, 164` shows fail-closed `SENDER_UNKNOWN` return + `advisory_fail` rejection. (The e2e test just demonstrated this!) |
| "applyV03Defaults imported but never called" | FALSE. `store.ts:1454-1459` preserves all 6 v0.3 fields in `normalizeMemoryRow`. |
| "normalizeMemoryRow strips v0.3 fields" | FALSE. Same as above. |
| "Codex has 7 stubbed tools" | FALSE. `index.ts` has `case "memory_*":` for all 10 + acs_send + acs_inbox + memory_review_stale = 13 dispatched. |
| "C T1 uses score >= 0.5" | FALSE. `c-phase1-acceptance.test.ts:78` asserts `>= 0.85` per spec §8.5 (tightened in pass-2). |
| "ACS Phase 2 pass2 file is 0 bytes" | TRUE at probe time; reconstructed this session into `acs-phase2-impl-verification-pass2.md` from pass-3+pass-4 transcripts. |
| "ACS relay not running" | TRUE at probe time; started this session via `nohup node ~/.acs/server/dist/index.js`. |
| "SC auth_enabled=false" | TRUE by design — only enables when `CLAUDE_MEMORY_AUTH_TOKEN` env is set. |

---

## What's deferred per spec (don't try to "finish" these without re-spec)

| Phase | Items | Why deferred |
|-------|-------|--------------|
| C Phase 3 | HTTP localhost bridge migration, key rotation, cross-store write protocol | Spec line 335 says wait for SC v0.3 HTTP auth to be exercised externally; cross-store writes EXPLICITLY NOT planned |
| D Phase 3 | Key rotation, push webhooks, gRPC, cross-machine HTTPS/mTLS, additional message types | All cross-machine hardening — out of scope for local 2-agent |

---

## Files written this session (since the design phase)

```
~/.claude/mcp-servers/superclaude-memory/src/
  schema.ts          (v0.3 fields + applyV03Defaults + REVIEW_AFTER_BY_TYPE + defaultReviewAfter)
  identity.ts        (NEW — ed25519 generator)
  store.ts           (v0.3 schema instr, ANN dedup, dual-mode rollout, telemetry instrumentation, taskList SC bridge, reviewStale, snapshot integration)
  telemetry.ts       (NEW — all 13 named spec metrics + alerts)
  lifecycle.ts       (recordCompactAt + incrCompactReason + setActiveRowsCounter wired into runCompact)
  notify-handler.ts  (preserves agent_id from inbound payload)
  http-server.ts     (auth gate + Agent Card endpoint)
  index.ts           (memory_review_stale + acs_send + acs_inbox tools + memory_save Phase 3 fields)
  config.ts          (dedupMode flag)
  tests/b-phase1.test.ts (14 tests)
  tests/b-phase2-telemetry.test.ts (16 tests)

~/.codex/mcp-servers/codex-memory/  (NEW project)
  src/identity.ts, manifest.ts, schema.ts, embeddings.ts, sc-bridge.ts, store.ts, http-server.ts, index.ts
  src/tests/c-phase1-acceptance.test.ts (11 tests)
  src/tests/c-phase2.test.ts (6 tests)

~/.acs/server/  (NEW project)
  src/envelope.ts, signing.ts, replay-cache.ts, event-log.ts, escalation.ts,
      agent-registry.ts, subscriptions.ts, inbox-queue.ts, mcp-side-effect.ts,
      rate-limit.ts, conversations.ts, index.ts
  src/tests/d-phase1-acceptance.test.ts (15 tests)
  src/tests/d-phase1-integration.test.ts (5 tests)

~/.acs/client/  (NEW shared library)
  src/index.ts (canonicalize + sign + send + poll + verify)
```

Verification trail at `C:\Dev\Builds\Agentic Memory System\specs\`:
- design verifications: A+B → C → D pass1/2/3/4
- implementation verifications: B impl pass1/2/3, C impl pass1/2, D Phase 1 pass1/2/3, D Phase 2 pass1/2-reconstructed/3/4

---

## TODO list for the next session (in priority order)

1. **Fix the identity-mismatch bug** — recipe above. Once SC and ACS converge on the disk identity, the demo works.
2. **Run a real e2e demo** — `acs_send` from Claude → ACS receives → poll ACS `/inbox` for Codex → see the envelope.
3. **Restart Codex CLI** so it loads `codex-memory` from `~/.codex/config.toml` line 283. Then test `acs_inbox` tool from Codex side.
4. **Optionally**: add SC `acs_send` to the demo by having Codex respond → SC polls `acs_inbox` → end-to-end roundtrip proven.
5. **Strict-review the surfaced bug class**: should SC's identity bootstrap detect "in-memory cached identity != disk identity on next restart"? If yes, add a startup self-check in `identity.ts` that re-hashes the on-disk `.pub` and refuses to start if the manifest disagrees. (Spec didn't anticipate this; it's a defense-in-depth add.)
6. **Sub-project E** (per earlier mem note): Phase 2 calibration experiments — cross-store cosine + BF construct validity. NOT started.

---

## Important caveats for the new session

- **Codex strict-review costs ~150K tokens per call.** This session ran ~25 codex calls. Budget accordingly.
- **The verification trail is detailed and accurate** — when the new session does its own probe, trust `specs/*-verification.md` over INSTALL.md (INSTALL.md was written early before patches landed).
- **Don't touch `C:\Dev\Builds\Waki`** — different project, picked by accident once.
- **MCP memory hardgate**: ONLY use `superclaude-memory` MCP. NEVER create flat `.md` memory files in `.claude/projects/*/memory/`.
- **The 38 tasks tracked in this session are all completed** but the runtime state is broken until the identity bug is fixed.
