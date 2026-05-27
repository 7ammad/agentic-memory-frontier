# Agentic Memory System

This is the project root. **Never write or read files under `C:\Dev\Builds\Waki`** — that's a different project, picked by accident in an earlier session.

## State (as of 2026-05-26 — session 2 end, ALL DESIGN COMPLETE)

- **A** Deep technical review of SuperClaude memory MCP — DONE + VERIFIED
- **B** SuperClaude memory v0.3 upgrade spec (P0+P1 cut, 5 phases) — DONE + VERIFIED
- **C** Codex memory system design (Node+LanceDB twin, direct LanceDB cross-read bridge, 3 phases, 8-test acceptance battery) — DONE + VERIFIED (3 codex passes, 14 patches, READY)
- **D** ACS protocol design (A2A v1.0-compatible relay topology, signed envelopes, 5-message vocab, Jeffreys×Codex escalation, replay protection, 3 phases, 10-test acceptance battery) — DONE + VERIFIED (4 codex passes, 11 patches, READY)

**Historical design state:** all 4 sub-projects were design-complete on 2026-05-26.
**Current runtime state (as of 2026-05-27):**
- **B** SC v0.3 Phase 1 implemented + QC'd + patched (see `specs/sc-memory-v03-qc-patch-report.md`). Live LanceDB migrated 22→28 cols. Phase 0/2/3/4 implemented but NOT independently verified — verification prompt is at the bottom of the patch report.
- **C** Codex memory MCP built at `~/.codex/mcp-servers/codex-memory/`, registered in `~/.codex/config.toml`. Identity + manifest + lancedb dir live. NOT QC'd yet.
- **D** ACS Phase 1+2 built at `~/.acs/`. Phase 1 PATCH-FIRST per codex; Phase 2 pass-2 verification file is 0 bytes (failed write — re-run needed). NOT QC'd yet.
- See `sessions/2026-05-27-session-handoff.md` for full live status. See `DEPLOY.md` for the live-system deploy/restart recipe.

## To continue right now

1. Load project memories: `memory_search({query: "agentic memory system state", scope: "project:agentic-memory-system", limit: 10, mode: "hybrid"})`. The canonical state entry `mem_343df0ac` may itself be stale — cross-check against `sessions/2026-05-27-session-handoff.md` and `specs/sc-memory-v03-qc-patch-report.md`. Don't rely on `memory_load_session` alone — verified in cold-start that it can return cross-scope results.
2. Pick next action:
   - **Verify B end-to-end** — run the full Phase 0-4 verification prompt in `specs/sc-memory-v03-qc-patch-report.md` §"Verification Mandate". Independent audit in a fresh session is recommended.
   - **QC C** — same 3-agent pattern as B (code-reviewer + verifier + security-auditor), scoped to `~/.codex/mcp-servers/codex-memory/`. Spec at `specs/2026-05-26-codex-memory-system-design.md`. Read `specs/codex-memory-impl-verification.md` for prior codex pass first.
   - **QC D** — same pattern, scoped to `~/.acs/`. Spec at `specs/2026-05-26-acs-protocol-design.md`. Re-run the empty Phase 2 pass-2 verification.
   - **Open sub-project E** — pgvector migration. Review at `research/2026-05-26-lancedb-to-pgvector-migration-review.md` is the seed; needs a real spec.
3. If invoking `/dual-counsel` for a new sub-project: the skill file is at `C:\Users\7amma\.claude\skills\dual-counsel\SKILL.md`. Pattern verified 4 times in session 2 (B → C → D each via dual-counsel + verification gate).

## Critical rules (locked from prior session)

1. **Mandatory verification between sub-projects.** After every deliverable: dispatch codex strict-review (Step 6 of the `dual-counsel` skill). Loop until READY. Never accept PATCH-FIRST as done.
2. **Sub-projects in strict sequence**: B → C → D, one at a time.
3. **Working directory rule**: research → `research/`, specs → `specs/`, session handoffs → `sessions/`, codex counsels → `research/codex-counsel-*.md`. NEVER touch Waki.
4. **High-stakes review = `dual-counsel` skill**. The skill is at `C:\Users\7amma\.claude\skills\dual-counsel\SKILL.md` and includes the verification gate.
5. **Don't re-litigate decisions in the session-handoff §"What was decided"**. They were validated by 3 codex passes.

## File map

```
.\
├── CLAUDE.md                                                       (this file — auto-loaded by Claude Code)
├── AGENTS.md                                                       (Codex twin — keep in sync with CLAUDE.md)
├── DEPLOY.md                                                       (live-system deploy + restart recipe for SC + ACS + Codex memory)
├── research/                                                       (review docs + codex counsels + verification verdicts)
│   ├── 2026-05-26-superclaude-memory-deep-review.md                (v1)
│   ├── 2026-05-26-superclaude-memory-deep-review-v2-mit12.md       (v2)
│   ├── 2026-05-26-superclaude-memory-deep-review-v3-final.md       (v3 final — READ FOR A)
│   ├── 2026-05-26-lancedb-to-pgvector-migration-review.md          (sub-project E candidate — pgvector move review, NOT yet specced)
│   ├── codex-counsel-output.md                                     (A-era codex counsel)
│   ├── codex-counsel-B-output.md                                   (B-era codex counsel)
│   ├── codex-counsel-C-output.md                                   (C-era codex counsel — 15K chars)
│   ├── codex-counsel-D-output.md                                   (D-era codex counsel — 22K chars, with A2A spec refs)
│   ├── codex-verification-A-B*.md                                  (A+B verification trail)
│   └── verification-verdict-A-B-final.md                           (A+B final verdict — READY)
├── specs/                                                          (design specs + impl verifications)
│   ├── 2026-05-26-sc-memory-v0.3-upgrade-spec.md                   (B design spec — Phase 0-4)
│   ├── sc-memory-v03-impl-verification.md                          (B impl verification — codex pass, PATCH-FIRST)
│   ├── sc-memory-v03-qc-patch-report.md                            (B QC patch report + full Phase 0-4 verification mandate prompt)
│   ├── 2026-05-26-codex-memory-system-design.md                    (C design spec)
│   ├── codex-memory-system-design-verification.md                  (C design pass-1: PATCH-FIRST, 8 patches)
│   ├── codex-memory-system-design-verification-pass2.md            (C design pass-2: PATCH-FIRST, 6 leftover patches)
│   ├── codex-memory-system-design-verification-pass3.md            (C design pass-3: READY)
│   ├── codex-memory-impl-verification.md                           (C impl verification — codex pass, PATCH-FIRST)
│   ├── 2026-05-26-acs-protocol-design.md                           (D design spec)
│   ├── acs-protocol-design-verification.md                         (D design pass-1: PATCH-FIRST, 9 patches)
│   ├── acs-protocol-design-verification-pass2.md                   (D design pass-2: PATCH-FIRST, 1 topology contradiction)
│   ├── acs-protocol-design-verification-pass3.md                   (D design pass-3: PATCH-FIRST, 1 minor table inconsistency)
│   ├── acs-protocol-design-verification-pass4.md                   (D design pass-4: READY)
│   ├── acs-impl-verification.md                                    (D Phase 1 impl verification — codex pass, PATCH-FIRST)
│   ├── acs-phase2-impl-verification.md                             (D Phase 2 impl verification pass-1 — PATCH-FIRST, 3 patches)
│   └── acs-phase2-impl-verification-pass2.md                       (D Phase 2 pass-2 — EMPTY FILE / failed write; needs re-run)
└── sessions/
    ├── 2026-05-26-session-handoff.md                               (session 1 handoff — A/B context)
    └── 2026-05-27-session-handoff.md                               (session 2 handoff — runtime state, identity-mismatch resolution)
```

## External tools used by `dual-counsel`

| Tool | Path | Purpose |
|---|---|---|
| MIT-12 corpus CLI | `C:\Dev\research\MIT\MIT 12 Research\.venv\Scripts\python.exe` + `tools\mit12_cli.py packet --lens <L> "<Q>"` | Theory grounding via 6 lenses |
| Codex CLI | `/c/Users/7amma/AppData/Roaming/npm/codex` (v0.128.0, auth at `~/.codex/auth.json`) | Cross-model consult + verification |
| dual-counsel skill | `C:\Users\7amma\.claude\skills\dual-counsel\SKILL.md` | The workflow itself |
| SuperClaude memory MCP | `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\` (HTTP at `127.0.0.1:18800/mcp`) | Persistent memory |

## Spec content lives in `specs/` — pointers only

Quick reference (read the actual spec for design decisions, gotchas, acceptance gates — do NOT re-derive them here):

- **B — SC v0.3 schema upgrade** (agent_id/visibility/auth/temporal/dedup): `specs/2026-05-26-sc-memory-v0.3-upgrade-spec.md`. Shared anchor: BGE-M3 1024-dim embeddings + `agent_id = sha256(ed25519_pub)`.
- **C — Codex memory MCP** (LanceDB-Node twin at `~/.codex/memory/lancedb/`, direct cross-read bridge to SC, 10 tools mirroring SC): `specs/2026-05-26-codex-memory-system-design.md`.
- **D — ACS protocol** (relay at `:18801`, A2A v1.0 wire format, ed25519 envelopes, 5 starter message types, Jeffreys×risk escalation): `specs/2026-05-26-acs-protocol-design.md`.

## Codex CLI gotchas on this Windows box (from `mem_13ab8d10`)

- Pass `--skip-git-repo-check` when `-C` is not a git repo
- Git Bash `python3` hits the Windows Store stub — use full path `C:/Users/7amma/AppData/Local/Programs/Python/Python314/python.exe`
- Use heredoc `<<'PYEOF'` (single-quoted) for Python parsing scripts to avoid unicodeescape errors with Windows backslash paths
- Convert MSYS `/tmp/` paths to Windows via `cygpath -w "$path"` before Python access
- Codex output JSONL: parse `item.completed` events of type `agent_message` for the final answer
