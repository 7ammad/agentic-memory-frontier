# Agentic Memory System — deploy recipe

Status at end of build session: all three pieces (B/C/D) have working code; **none have been built or restarted yet**. This document gets you from "code on disk" to "agents talking in real-time."

## What was built in this session

| Piece | Where | Status |
|-------|-------|--------|
| `@acs/client` shared library | `~/.acs/client/` | Code complete (envelope build + sign + verify + HTTP transport) |
| ACS relay service | `~/.acs/server/` | Code complete (HTTP, /rpc JSON-RPC, /events SSE, /inbox polling, replay cache, event log, escalation) |
| SC v0.3 source changes | `~/.claude/mcp-servers/superclaude-memory/src/` | Compiled clean before adding @acs/client (will compile clean once client is built); identity.ts, schema.ts v0.3 fields, store.ts v0.3 writes, notify-handler fix, HTTP auth, Agent Card endpoint, `acs_send` + `acs_inbox` MCP tools |
| Codex memory MCP | `~/.codex/mcp-servers/codex-memory/` | Project scaffold + identity + bridge + 5 tools (3 memory + 2 ACS) |

## The deploy sequence

Run these in order. Each step assumes the previous succeeded.

### 0. Stop the currently-running SC server (if any)

```powershell
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*superclaude-memory*" } | Stop-Process -Force
```

(Skip if not running. The rebuild in step 5 will create new code that the next SC start picks up.)

### 1. Build `@acs/client` (shared dep)

```bash
cd ~/.acs/client
npm install
npm run build
```

This creates `~/.acs/client/dist/`. SC and codex-memory both depend on this via `file:` paths.

### 2. Build the ACS relay service

```bash
cd ~/.acs/server
npm install
npm run build
```

### 3. Start the ACS relay (long-running)

```bash
cd ~/.acs/server
node dist/index.js
# logs: [acs] listening on http://127.0.0.1:18801
# leave this running in a dedicated terminal
```

### 4. Build codex-memory

```bash
cd ~/.codex/mcp-servers/codex-memory
npm install
npm run build
```

### 5. Rebuild SC (picks up v0.3 changes + ACS tools)

```bash
cd ~/.claude/mcp-servers/superclaude-memory
npm install   # picks up new @acs/client and canonicalize deps
npm run build
```

### 6. Restart SC

SC starts automatically when Claude Code spawns it. So just open a fresh Claude Code session. On first start, SC will:
- Generate `~/.claude/memory/identity/sc.ed25519.{key,pub}` if missing
- Write `~/.claude/memory/identity/manifest.json`
- Serve `GET http://127.0.0.1:18800/.well-known/agent-card.json` returning the new Agent Card with `extensions.acs.{agent_id, ed25519_pub_key}`

Verify with: `curl http://127.0.0.1:18800/.well-known/agent-card.json`

### 7. Register codex-memory in `~/.codex/config.toml`

Add this block:

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
ACS_BASE_URL = "http://127.0.0.1:18801"
SC_AGENT_CARD_URL = "http://127.0.0.1:18800/.well-known/agent-card.json"
```

### 8. (Manual) Add Codex Agent Card endpoint

Codex memory's MCP is stdio-only — it can't host the `/.well-known/agent-card.json` HTTP endpoint that ACS expects. **Workaround for Phase 1**: write Codex's Agent Card to a static file, and ACS reads it from disk if HTTP fetch fails.

Simplest hack: run codex-memory once via `node ~/.codex/mcp-servers/codex-memory/dist/index.js` and call `memory_health` from inside Codex; the response includes Codex's `agent_id` + (after a small extension) `ed25519_pub_key`. Copy those into the ACS agent-registry hardcoded list.

**Better solution (TODO)**: add an HTTP layer to codex-memory exposing `/.well-known/agent-card.json` on port 18802. This requires writing `~/.codex/mcp-servers/codex-memory/src/http-server.ts` — same pattern as SC's. Not done this session.

## The demo (once everything's running)

From a Claude Code session (with SC restarted post-rebuild):

```
claude> use mcp__superclaude-memory__acs_send with {
  recipient: "codex",
  message_type: "second_opinion.request",
  protocol_mode: "second_opinion",
  payload: {
    question: "Should we refactor the auth module before shipping?",
    context: ["Current code has 3 callers", "Refactor would unify 2 patterns"],
    requested_depth: "fast"
  }
}
```

ACS logs the envelope, queues it for Codex's agent_id. Claude gets `delivered_to: 0, queued_depth: 1` if Codex hasn't polled yet.

From a Codex CLI session (with codex-memory MCP registered):

```
codex> use mcp__codex-memory__acs_inbox
```

Codex pulls the queued envelope, verifies the signature against SC's pub key (fetched from SC's Agent Card), returns the verified envelope.

```
codex> use mcp__codex-memory__acs_send with {
  recipient: "claude",
  message_type: "second_opinion.response",
  protocol_mode: "second_opinion",
  payload: {
    answer: "No — ship first, refactor when there's a third caller",
    confidence: 0.7,
    agreements: ["3 callers does not justify the rewrite cost"],
    disagreements: [],
    recommended_action: "accept"
  }
}
```

Back in Claude:

```
claude> use mcp__superclaude-memory__acs_inbox
```

Claude receives Codex's response, verifies the signature against Codex's pub key.

**That's the loop.** Real signed messages, real round-trip, real-time (sub-second once both sides are connected).

## Known gaps (next session)

- Codex memory doesn't have HTTP layer for serving its Agent Card → ACS can't auto-fetch Codex's pub key. Manual workaround above; proper fix is `codex-memory/src/http-server.ts`.
- 7 of 10 codex-memory MCP tools are stubbed (memory_load_session, memory_update, memory_delete, memory_compact, memory_stats, memory_task_list, memory_task_update).
- Per-message-type payload validation in ACS is generic (passthrough); D spec §5.2 type-specific Zod schemas can be added in Phase 2.
- Codex strict-review verification on the implemented code hasn't been run.
- 8-test acceptance battery for C and 10-test for D haven't been run.
- B Phase 2-4 (telemetry contract, per-type temporal columns, combined-filter ANN) untouched.
- C Phase 2-3 and D Phase 2-3 untouched.

## Rollback

- ACS service: `Ctrl+C` to stop. Delete `~/.acs/` to nuke entirely.
- Codex memory: remove `[mcp_servers.codex-memory]` block from `~/.codex/config.toml`. Delete `~/.codex/memory/` to nuke.
- SC v0.3 changes: snapshot at `~/.claude/memory/snapshots/20260526-220131-pre-v0.3-phase1/`. To revert: stop SC, restore the snapshot's `superclaude-memory-src/` over the current source, rebuild.

## File map of new code

```
~/.acs/
├── server/                              # the ACS relay
│   ├── package.json
│   ├── tsconfig.json
│   ├── INSTALL.md
│   └── src/
│       ├── envelope.ts                  # Zod schema + reward contracts
│       ├── signing.ts                   # Ed25519 + JCS
│       ├── replay-cache.ts              # in-memory replay protection
│       ├── event-log.ts                 # JSONL append-only at ~/.acs/data/event-log/
│       ├── escalation.ts                # Jeffreys × risk-weighted escalate()
│       ├── agent-registry.ts            # known peer Agent Cards + pub key cache
│       ├── subscriptions.ts             # SSE subscription manager
│       ├── inbox-queue.ts               # per-recipient FIFO for offline delivery
│       └── index.ts                     # HTTP server entry
├── client/                              # shared library
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       └── index.ts                     # buildAndSignEnvelope, sendEnvelopeToAcs, pollInbox, verifyIncoming
└── data/
    ├── event-log/                       # populated at first message
    └── replay-cache/                    # reserved for Phase 2 SQLite

~/.codex/
├── memory/                              # codex memory state
│   ├── identity/                        # ed25519 keypair (auto-generated first run)
│   ├── lancedb/                         # codex's own LanceDB store
│   ├── snapshots/
│   └── telemetry.jsonl
└── mcp-servers/codex-memory/            # codex memory MCP
    ├── package.json
    ├── tsconfig.json
    ├── INSTALL.md
    └── src/
        ├── identity.ts                  # codex agent identity
        ├── manifest.ts                  # schema_version manifest
        ├── schema.ts                    # v0.3 row + Zod inputs
        ├── sc-bridge.ts                 # cross-read SC's LanceDB
        ├── embeddings.ts                # re-exports @openclaw/local-embeddings
        ├── store.ts                     # local LanceDB CRUD
        └── index.ts                     # MCP server with 3 memory tools + 2 ACS tools

~/.claude/mcp-servers/superclaude-memory/src/  # SC v0.3 modifications
├── identity.ts                          # NEW — SC ed25519 keypair
├── schema.ts                            # PATCHED — 6 v0.3 fields + helpers
├── store.ts                             # PATCHED — v0.3 fields on save (createNew + supersede)
├── notify-handler.ts                    # PATCHED — preserves agent_id from inbound payload
├── http-server.ts                       # PATCHED — bearer auth + Agent Card endpoint
└── index.ts                             # PATCHED — adds acs_send + acs_inbox MCP tools
```
