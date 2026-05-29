# Agentic Memory System

This is the project root. **Never write or read files under `C:\Dev\Builds\Waki`** — that's a different project, picked by accident in an earlier session.

## State (as of 2026-05-26 — session 2 end, ALL DESIGN COMPLETE)

- **A** Deep technical review of SuperClaude memory MCP — DONE + VERIFIED
- **B** SuperClaude memory v0.3 upgrade spec (P0+P1 cut, 5 phases) — DONE + VERIFIED
- **C** Codex memory system design (Node+LanceDB twin, direct LanceDB cross-read bridge, 3 phases, 8-test acceptance battery) — DONE + VERIFIED (3 codex passes, 14 patches, READY)
- **D** ACS protocol design (A2A v1.0-compatible relay topology, signed envelopes, 5-message vocab, Jeffreys×Codex escalation, replay protection, 3 phases, 10-test acceptance battery) — DONE + VERIFIED (4 codex passes, 11 patches, READY)

**Historical design state:** all 4 sub-projects were design-complete on 2026-05-26.
**Current runtime state:** implementation work started on 2026-05-27; read `sessions/2026-05-27-session-handoff.md` for live status, especially the SC/ACS identity-mismatch blocker.

## To continue right now

1. Run session-start hard gate before any implementation command: `powershell -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1`. If it fails, stop and fix memory wiring first.
2. Load project memories: `memory_search({query: "agentic memory system state", scope: "project:agentic-memory-system", limit: 10, mode: "hybrid"})` — returns the canonical state entry [mem_343df0ac, updated to reflect all 4 done] plus the rest. Don't rely on `memory_load_session` alone — verified in cold-start that it can return cross-scope results.
3. Decide next phase. Options:
   - **Implement** in dependency order: SC v0.3 Phase 1 → Codex memory C Phase 0+1 → ACS D Phase 1. Each phase has its own acceptance battery in the spec.
   - **Iterate on design** — if anything in A/B/C/D needs revision before code is written, do it now while the dual-counsel context is fresh.
   - **Open a new sub-project E** — e.g., spec for the Phase 2 calibration experiments (cross-store cosine + BF construct validity).
4. If invoking `/dual-counsel` for a new sub-project: the skill file is at `C:\Users\7amma\.claude\skills\dual-counsel\SKILL.md`. Pattern verified 4 times in session 2 (B → C → D each via dual-counsel + verification gate).

## Critical rules (locked from prior session)

**HARDGATE — autonomous build loop (CEM-1 Phases 3-5, mirrors `CLAUDE.md`):** Finish the CEM-1 build as ONE self-paced session (not a manual multi-session fan-out): next unchecked `TODO.md` item -> full build (no MVP/distillation/stubs; TDD + a failure canary that bites) -> `python -m pytest` green -> commit -> continue. Each slice ships as a minimal single-surface PR to `staging` and runs the Greptile review-loop to 5/5 (stop rule: ~5 turns / stuck at 4/5 -> human). Self-pace external review waits with the `/loop` dynamic engine (`ScheduleWakeup`). **Stop before merge — merging is the user's call.** Full contract: `docs/WORKFLOW.md`. (Note: the rest of this file is stale 2026-05-26 A/B/C/D context; the live rail is `TODO.md` + `CLAUDE.md`.)

1. **Mandatory verification between sub-projects.** After every deliverable: dispatch codex strict-review (Step 6 of the `dual-counsel` skill). Loop until READY. Never accept PATCH-FIRST as done.
2. **Sub-projects in strict sequence**: B → C → D, one at a time.
3. **Working directory rule**: research → `research/`, specs → `specs/`, session handoffs → `sessions/`, codex counsels → `research/codex-counsel-*.md`. NEVER touch Waki.
4. **High-stakes review = `dual-counsel` skill**. The skill is at `C:\Users\7amma\.claude\skills\dual-counsel\SKILL.md` and includes the verification gate.
5. **Don't re-litigate decisions in the session-handoff §"What was decided"**. They were validated by 3 codex passes.
6. **Operational memory gate is mandatory**: no implementation, no patches, and no status claims before `scripts/session-start-gate.ps1` passes in the active session.
7. **Record plan changes, gaps, and mistakes**: update `CHANGELOG.md` for timeline-level changes and `docs/PROJECT-LEDGER.md` for decisions, gaps, mistakes, verification state, and follow-ups.

## File map

```
.\
├── AGENTS.md                                                       (this file — auto-loaded by Codex)
├── CHANGELOG.md                                                    (canonical repo timeline)
├── docs/
│   └── PROJECT-LEDGER.md                                           (decisions, gaps, mistakes, verification state)
├── research/                                                       (review docs + codex counsels + verification verdicts)
│   ├── 2026-05-26-superclaude-memory-deep-review.md                (v1)
│   ├── 2026-05-26-superclaude-memory-deep-review-v2-mit12.md       (v2)
│   ├── 2026-05-26-superclaude-memory-deep-review-v3-final.md       (v3 final — READ FOR A)
│   ├── codex-counsel-output.md                                     (A-era codex counsel)
│   ├── codex-counsel-B-output.md                                   (B-era codex counsel)
│   ├── codex-counsel-C-output.md                                   (C-era codex counsel — 15K chars)
│   ├── codex-counsel-D-output.md                                   (D-era codex counsel — 22K chars, with A2A spec refs)
│   ├── codex-verification-A-B*.md                                  (A+B verification trail)
│   └── verification-verdict-A-B-final.md                           (A+B final verdict — READY)
├── specs/
│   ├── 2026-05-26-sc-memory-v0.3-upgrade-spec.md                   (v0.3 spec — READ FOR B)
│   ├── 2026-05-26-codex-memory-system-design.md                    (C spec — READ FOR C)
│   ├── codex-memory-system-design-verification.md                  (C pass-1: PATCH-FIRST, 8 patches)
│   ├── codex-memory-system-design-verification-pass2.md            (C pass-2: PATCH-FIRST, 6 leftover patches)
│   ├── codex-memory-system-design-verification-pass3.md            (C pass-3: READY — final verdict)
│   ├── 2026-05-26-acs-protocol-design.md                           (D spec — READ FOR D)
│   ├── acs-protocol-design-verification.md                         (D pass-1: PATCH-FIRST, 9 patches)
│   ├── acs-protocol-design-verification-pass2.md                   (D pass-2: PATCH-FIRST, 1 topology contradiction)
│   ├── acs-protocol-design-verification-pass3.md                   (D pass-3: PATCH-FIRST, 1 minor table inconsistency)
│   └── acs-protocol-design-verification-pass4.md                   (D pass-4: READY — final verdict)
└── sessions/
    └── 2026-05-26-session-handoff.md                               (session 1 handoff — A/B context, still relevant for §"What was decided")
```

## External tools used by `dual-counsel`

| Tool | Path | Purpose |
|---|---|---|
| MIT-12 corpus CLI | `C:\Dev\research\MIT\MIT 12 Research\.venv\Scripts\python.exe` + `tools\mit12_cli.py packet --lens <L> "<Q>"` | Theory grounding via 6 lenses |
| Codex CLI | `/c/Users/7amma/AppData/Roaming/npm/codex` (v0.128.0, auth at `~/.codex/auth.json`) | Cross-model consult + verification |
| dual-counsel skill | `C:\Users\7amma\.claude\skills\dual-counsel\SKILL.md` | The workflow itself |
| SuperClaude memory MCP | `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\` (HTTP at `127.0.0.1:18800/mcp`) | Persistent memory |

## What the v0.3 spec adds (interop with Codex memory)

Codex memory inherits these v0.3 columns so the two stores interoperate from day 1:

- `agent_id` (sha256 of ed25519 pub key; `agent_alias = "codex"` for Codex's store)
- `agent_alias`, `capabilities` (JSON array)
- `valid_from`, `valid_to`, `review_after` (temporal validity model)
- Enforced `visibility` filter at every read path

Embedding model: BGE-M3 1024-dim (same as SC, for cross-store cosine compatibility).

## What the C spec delivers (Codex memory MCP — the memory twin)

- **Storage**: LanceDB-Node at `~/.codex/memory/lancedb/`, same `agent_memories` table name, 1024-dim BGE-M3 (no impedance mismatch with SC)
- **Runtime**: Node/TypeScript, vendor SC's `embeddings` package
- **Bridge**: direct LanceDB cross-read for Phase 1 (free communication, MMDP/MPOMDP complexity — book-09-chunk-0050 Table 7.2); HTTP localhost deferred to Phase 3 after SC v0.3 auth lands
- **Search contract**: `memory_search` returns TWO separate ranked lists with `provenance`; mixed cosine ranking deferred to Phase 2 calibration (construct-validity per book-10-chunk-0066)
- **session-loader**: `memory_load_session` reads BOTH stores (Codex local + SC shared via bridge)
- **Tool surface**: mirror SC's 10 tools in Phase 1; `memory_review_stale` added in Phase 2 (codex's accepted pushback)
- **Backup/schema-versioning**: `manifest.json` with semver `schema_version`, supported range `^0.3.0` for Phase 1 (codex's accepted missing-item)
- **Identity**: ed25519 keypair, `agent_id = sha256(pub_key)`, `agent_alias = "codex"`
- **Migration**: clean-slate (no `~/.codex/memory/` exists; automations are NOT memory state)
- **Phasing**: Phase 0 = pre-row bootstrap | Phase 1 = MCP runtime + bridge + 8-test acceptance battery | Phase 2 = hygiene + telemetry + cosine calibration | Phase 3 = HTTP transport + key rotation

## What the D spec delivers (ACS — the communication channel)

- **Service**: dedicated ACS process at `:18801/rpc` + `/events` + `/.well-known/agent-card.json`. NOT messages-as-memory-rows (that's the general-communication anti-pattern).
- **Wire format**: A2A v1.0-compatible (NOT ADK-bound — codex's accepted pushback), JSON-RPC 2.0 + SSE.
- **Topology**: RELAY — both SC and Codex Agent Cards advertise the same `:18801` ACS endpoint; routing by `recipient_agent_id`. Each agent's MCP HTTP layer serves only its own `/.well-known/agent-card.json` (static discovery).
- **Identity**: ed25519 signature on EVERY message (no TOFU as sole trust). `agent_id = sha256(pub_key)` shared with v0.3 / C.
- **Canonicalization**: RFC 8785 JCS over `envelope_without_sig`; `body_hash = sha256_hex(JCS(payload))`.
- **5 starter message types**: second_opinion (req/resp), review.findings (one-way+ack), handoff.state (one-way+ack+continuation_token), clarification (req/resp), decision.recorded (one-way+ack).
- **Reward structure**: EXPLICIT `protocol_mode` + `reward_contract` in EVERY message (not conversation-init, not behavioral inference).
- **Escalation**: only auto-resolve case is `risk<0.3 AND BF>=10` (Jeffreys: strong). Hard escalate on irreversible OR security-sensitive OR money/legal/secrets OR `risk>=0.7` OR `BF<3`. Middle zone defaults to escalate. Risk wins over BF.
- **Replay protection MANDATORY in Phase 1**: nonce, message_id, timestamp, ttl_ms, body_hash. Replay cache keyed by `(sender_agent_id, message_id)`. Exact dup = original ack; body_hash mismatch = rejected (codex's accepted missing-item).
- **MCP inner boundary**: ACS uses MCP only for durable memory side effects (`decision.recorded`, `handoff.state` → `memory_save` on recipient). ACS does NOT broker arbitrary MCP tool calls in Phase 1.
- **Phasing**: Phase 1 = service + signed envelopes + 5 message types + replay protection + 10-test acceptance battery | Phase 2 = conversation lifecycle + BF calibration + rate limiting | Phase 3 = key rotation + push webhooks + cross-machine

## Codex CLI gotchas on this Windows box (from `mem_13ab8d10`)

- Pass `--skip-git-repo-check` when `-C` is not a git repo
- Git Bash `python3` hits the Windows Store stub — use full path `C:/Users/7amma/AppData/Local/Programs/Python/Python314/python.exe`
- Use heredoc `<<'PYEOF'` (single-quoted) for Python parsing scripts to avoid unicodeescape errors with Windows backslash paths
- Convert MSYS `/tmp/` paths to Windows via `cygpath -w "$path"` before Python access
- Codex output JSONL: parse `item.completed` events of type `agent_message` for the final answer
