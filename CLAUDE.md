# Agentic Memory System

Project root. **Never write or read files under `C:\Dev\Builds\Waki`** — different project, picked by accident once.

Canonical product acceptance lock: `PRODUCT-LOCK.md`.
Canonical idea source of truth: `IDEA.md`.

Thesis: *Memory is not storage. Memory is verified experience that improves future action.* The deliverable is **AMS**: ingest agent traces -> extract typed candidate memories -> validate -> quarantine bad ones -> promote verified Experience Cards -> return task-scoped **action briefs**, not raw memory dumps.

## State (as of 2026-05-30)

AMS kernel, synthetic eval, baselines, external adapters (HaluMem / MemoryArena / LongMemEval-V2), AMS v1/v1.1, the Memory Use Controller (`startup-brief` gate), the Correction Capture Controller, and the §12 live-hook wrappers are implemented and tested.

- **Product acceptance source = `PRODUCT-LOCK.md`**. **Idea source of truth = `IDEA.md`**. **Execution source of truth = `TODO.md`** (ordered continuation rail — work the first unchecked item) and **`docs/PROJECT-LEDGER.md`** (decisions/gaps/mistakes/verification).
- **Current open track:** AMS Primary Runtime Adoption: live Codex hook-payload smoke, governed-run brief/monitor/evidence ids, and reconciliation of legacy Codex memories / `codex-memory` / `ams-memory` into an AMS-primary startup path.
- A/B/C/D (SuperClaude-memory review, SC v0.3 spec, Codex-memory design, ACS protocol) are **historical design context** — specs live in `specs/`, not the active rail.

## Commands

```powershell
python -m pytest                                  # full suite (pythonpath wired in pyproject.toml)
python scripts/ams.py init                        # init local memory root (~/.codex/memory/cem; AMS_ROOT or --root to override)
python scripts/ams.py brief "<task>" --domain agentic-memory-system   # action brief before working
python scripts/ams.py remember "<lesson>" --kind skill --outcome success --domain agentic-memory-system --task-family verification
python scripts/ams.py monitor --deep              # Monitor-0
python scripts/ams.py dashboard                   # phase + next step + record layers
python scripts/run_synthetic_eval.py              # AMS V0 corruption eval smoke
powershell -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1   # mandatory before implementation/status claims
```

## Architecture

```text
packages/cem-core/src/cem_core/   kernel: models, extractor, contradiction, validator, kernel,
                                  storage, mcp_stdio, mcp_tools, multi_agent, operations,
                                  local_memory, cli, correction_capture
packages/cem-eval/src/cem_eval/   synthetic_corruption, workflow_gotchas, *_adapter, *_runner, reports
scripts/                          ams.py (CLI), run_*_eval.py, run_cem_mcp_stdio.py, session-start-gate.ps1
tests/                            pytest suite (test_cem_kernel, test_ams_cli, adapters, runners, mcp, multi_agent)
docs/                             PROJECT-LEDGER.md, AMS v1.x plans, cem-0-*.md
research/ specs/ sessions/        plan + spec + handoffs (incl. historical A/B/C/D)
```

## Workflow rules

**HARDGATE - autonomous AMS build loop:** Finish the AMS build as one self-paced session, not a manual multi-session fan-out. Take the next unchecked `TODO.md` item -> build it (full: no MVP/distillation/stubs; TDD + a failure canary that bites) -> verify (`python -m pytest` green) -> commit -> continue. Ship each slice as a minimal single-surface PR to `staging` and run the Greptile review-loop to 5/5 (stop rule: ~5 turns or stuck at 4/5 -> hand to human). Self-pace across external review waits with the `/loop` dynamic engine (`ScheduleWakeup`). **The agent stops before merge - merging is the user's call.** Full contract: `docs/WORKFLOW.md`.

1. Run `scripts/session-start-gate.ps1` before any implementation, patch, or status claim. If it fails, fix memory wiring first.
2. Record changes: `CHANGELOG.md` (timeline) + `docs/PROJECT-LEDGER.md` (decisions/gaps/mistakes/verification) — before or alongside the change.
3. Follow `TODO.md`: after a verified item, run checks → commit → update TODO → continue to the next unchecked item unless blocked/redirected.
4. Verify before claiming done: `python -m pytest`, then the relevant smoke command.
5. Keep `AGENTS.md` (Codex twin) in sync with this file.

## Codex CLI gotchas on this Windows box

- Pass `--skip-git-repo-check` when `-C` is not a git repo.
- Git Bash `python3` hits the Windows Store stub — use `C:/Users/7amma/AppData/Local/Programs/Python/Python314/python.exe`.
- Single-quoted heredoc `<<'PYEOF'` for Python scripts (avoids unicodeescape on backslash paths).
- Convert MSYS `/tmp/` paths via `cygpath -w` before Python access.
- Codex JSONL: parse `item.completed` events of type `agent_message` for the final answer.
