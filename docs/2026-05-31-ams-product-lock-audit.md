# AMS Product Lock Audit

Date: 2026-05-31
Source: `PRODUCT-LOCK.md`
Status: accepted after terminal operator proof on 2026-06-01

## Summary

AMS v1 is accepted against `PRODUCT-LOCK.md`.

The moving-target part is now closed. The terminal acceptance list is A1-A9:
primary runtime lock, real trace intake, trust before retrieval, governed action
briefs, outcome influence, correction capture, aging/maintenance, frontier eval,
and operator product proof. All nine criteria have repo evidence. Any future
work must be named as post-v1 or treated as a regression fix, not as another
hidden TODO item for AMS v1.

## Acceptance Matrix

| Criterion | Status | Evidence | Missing Work | Next Step |
|---|---|---|---|---|
| A1. Primary Runtime Lock | pass | `scripts/session-start-gate.ps1` passes; dashboard shows latest startup brief allow/degraded status; global `ams-memory` MCP is configured in `~/.codex/config.toml`; `startup-brief` now writes governed-run receipts with brief, monitor, evidence, cwd, task, status, block reasons, and degraded reasons; live Codex hook smoke proves command hooks are invoked; `ams runtime-control` and `scripts/ams-guarded-command.ps1` enforce runtime-control/action-safety blocks before a downstream command is invoked; the npm `codex.ps1`, `codex.cmd`, and Git Bash `codex` shims are wrapped with `codex.ams-original*` backups, and reinstall over a fresh non-wrapped shim refreshes stale backups; `ams memory-surfaces` reports `ams-memory` as primary from `AMS_ROOT`, `CEM_ROOT`, or MCP `--root`, `codex-memory` as secondary, and native Codex memory as an applied secondary import source using the latest applied migration, not a later dry-run; Monitor-0 and memory-surface failures degrade startup memory-readiness status instead of becoming command authority; guarded runs now write `runtime-trace-latest`, surface AMS persistence failures even under quiet mode, and close governed-run receipts; monitor now runs maintenance review. | None for AMS v1. | Preserve as non-regression evidence. |
| A2. Real Trace Intake | pass | `ams runtime-trace record` loads a runtime-control receipt, creates a real `AgentTrace`, stores it through `CEM.ingest_trace`, proposes marker-backed memory candidates from the trace, and writes `runtime-trace-runs.jsonl`, `runtime-trace-latest.json`, and dashboard `latest_runtime_trace`. `scripts/ams-guarded-command.ps1` records traces automatically after allowed commands, blocked control decisions, and allowed launch failures where the downstream executable cannot start. Focused tests prove source spans on trace-derived candidates, quiet-wrapper output preservation, failed-launch trace recording, and stderr visibility when trace recording fails under quiet mode. | Keep full product-path smoke evidence current. | Treat as a non-regression gate during operator packaging. |
| A3. Trust Before Retrieval | pass | Validation, quarantine, reason codes, inactive-card filtering, negative controls, and failure canaries exist in tests and monitor paths; trace-derived candidates still enter as proposed atoms before validation/promotion; `ams maintenance review` names expired, stale, contradicted, inactive, and pending records before operators trust them. | None for AMS v1. | Preserve as non-regression evidence. |
| A4. Action Briefs Govern Work | pass | `startup-brief` returns bounded directives/cards/evidence/actions plus non-blocking degraded reasons; MCP action brief returns applicable ids, evidence ids, score breakdown, and expected action delta source; governed-run receipts attach the startup brief id, action brief id, influence id, monitor id, evidence ids, block reasons, and degraded reasons; `runtime-control` records the startup brief, monitor, governed-run id, gate decision, prompt decision, evidence ids, and degraded reasons; `codex --version` through an unseeded temporary AMS root blocks only through runtime-control/action-safety; dashboard exposes memory surface reconciliation, latest runtime trace status, and latest maintenance status; tests prove startup degrades when memory surfaces are unreconciled. | None for AMS v1. | Preserve as non-regression evidence. |
| A5. Outcome Influence Loop | pass | Action influence models, persistence, vertical-loop tests, and `ams governed-run close` exist; close finalizes the governed-run receipt with observed outcome, writes an observational influence event, is idempotent, and fails if a receipt lacks action-brief/influence ids; the guarded launcher now auto-closes governed-run receipts after blocked, allowed, and downstream-launch-failure outcomes; runtime traces record observed command outcome separately from verified lift. | Verified lift remains separate from observed outcome by design. | Keep observed outcome separate from verified lift during operator packaging. |
| A6. Correction Capture | pass | Correction capture core, CLI, resume gate, monitor checks, PowerShell hook wrappers, `ams runtime-control`, and `scripts/ams-guarded-command.ps1` exist; live Codex smoke verified `UserPromptSubmit` payload keys and prompt/session projection; guarded-command tests prove a correction prompt blocks before the downstream command is invoked; blocked guarded commands write failure runtime traces with `downstream_invoked=false` and close the governed-run receipt as failure, while allowed launch failures write failed runtime traces before exiting. | Keep the resume gate human-approved only. | Treat as a non-regression gate during operator packaging. |
| A7. Aging And Maintenance | pass | `ams maintenance review` writes `maintenance-runs.jsonl`, `maintenance-latest.json`, and `maintenance-latest.md`; it reports expired active cards, stale active cards, active cards with no validation freshness anchor, active contradiction links, inactive/superseded counts, pending atom review counts, and operator review actions. It excludes atoms already referenced by cards so promoted evidence is not misreported as pending. `monitor` adds `maintenance_surface_present` and `maintenance_no_blocking_risks`; dashboard exposes `latest_maintenance`; tests prove expired records do not leak into action briefs, monitor fails visibly on blocking expired active memory, and unknown freshness anchors are not treated as healthy. | Keep thresholds honest during operator proof. | Treat as a non-regression gate during operator packaging. |
| A8. Frontier Eval | pass | Baseline ladder, action-advantage metrics, negative-control suppression, latency budget, and full test suite pass. Terminal operator proof reran the Phase 4 frontier eval after runtime trace intake, aging/maintenance, and operator packaging: `frontier_eval=PASS margin=75.0pp`. | None for AMS v1. | Preserve as non-regression evidence. |
| A9. Operator Product | pass | `scripts/run_ams_operator_proof.py` creates a fresh local AMS root, writes isolated Codex config/memory inputs, runs init/bootstrap/remember/migrate, proves `ams-memory` primary with legacy memory as secondary, retrieves a startup brief, runs maintenance review, runs Monitor-0 deep checks, audits a real card, closes the governed run with outcome success, and reruns the frontier eval. Final proof: startup `brief_f3a88b2624454ddd886505de39e407f6`, monitor `monitor_17adf0c7bc9f4d84a906210bce318d0f`, maintenance items `0`, audit `card_264bed74b7a346dfbb0d3898aef1c8f8`, governed run `run_946ba867b16947438ac0a50919b66619 outcome=success`. | None for AMS v1. | Preserve as terminal operator proof. |

## Product State

Accepted now:

- AMS product lock exists and is the acceptance source.
- AMS startup memory-readiness can allow/degrade; execution blocking belongs to runtime-control/action-safety.
- AMS dashboard reports the current adoption phase.
- AMS monitor deep checks pass.
- Action-brief and validation engine tests pass.
- AMS runtime control can block before a downstream command is invoked.
- The default Windows/Git Bash Codex shims now route through AMS guarded control with backups and bypass escape hatch.
- Legacy `codex-memory` and native Codex memory are reconciled under AMS as secondary inputs.
- Governed runs can close/finalize with observed outcome and an observational influence event.
- Guarded Codex work automatically writes runtime traces into the AMS evidence ledger.
- Guarded Codex work automatically closes governed-run receipts and surfaces AMS persistence failures in quiet mode.
- Aging and maintenance review is visible in CLI, monitor, dashboard, and persisted reports.
- Fresh operator setup proof passes from an isolated local root.
- Phase 4 frontier eval rerun passes after operator packaging.

Remaining AMS v1 gaps:

- Nothing for AMS v1.

## Commands Run For This Audit

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1
python scripts/ams.py dashboard
python scripts/ams.py monitor --deep
python scripts/ams.py runtime-control "continue AMS primary runtime adoption" --domain agentic-memory-system
python scripts/ams.py runtime-trace record --control-id <control_id> --command codex --command-arg=--version --exit-code 0
python scripts/ams.py memory-surfaces
python scripts/ams.py governed-run close --outcome success --action-taken "verified current slice"
python scripts/ams.py maintenance review
python scripts/run_ams_operator_proof.py --root tmp\ams-operator-proof-final
python scripts/run_phase4_exam.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ams-guarded-command.ps1 -Workspace "C:\Dev\Builds\Agentic Memory System" -Prompt "SKILL: check startup brief before edits" -Quiet -Command cmd.exe /c echo AMS_TRACE_SMOKE
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ams-guarded-command.ps1 -Workspace "C:\Dev\Builds\Agentic Memory System" -Prompt "continue building Agentic Memory System with verification" -Command definitely-not-a-command-xyz
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ams-guarded-command.ps1 -Workspace "C:\Dev\Builds\Agentic Memory System" -Prompt "continue building Agentic Memory System with verification" -Quiet -Command cmd.exe /c "del /q <runtime-control-log> && echo RAW_OK"
codex --version # with AMS_ROOT set to a fresh temp root; expected block before raw Codex runs
codex exec "we already said no scaffolding; stop and record this correction" # with AMS_ROOT set to a fresh temp root; expected block before raw Codex runs
cmd /c codex --version
bash -lc '/mnt/c/Users/7amma/AppData/Roaming/npm/codex --version'
rg -n "class ActionBrief|score_breakdown|ActionInfluenceEvent|VerificationProbe|negative_control|retrieve_action_brief|startup-brief|correction hook|review_stale|stale|superseded|ingest_trace|Trace" packages scripts tests docs README.md PRODUCT-LOCK.md
```

## Terminal Proof

Terminal command:

```powershell
python scripts/run_ams_operator_proof.py --root tmp\ams-operator-proof-final
```

Terminal result:

```text
AMS_OPERATOR_PROOF_PASS root=C:\Dev\Builds\Agentic Memory System\tmp\ams-operator-proof-final
memory_surfaces_reconciled=True
startup=allow brief_f3a88b2624454ddd886505de39e407f6
monitor=pass monitor_17adf0c7bc9f4d84a906210bce318d0f
maintenance=pass items=0
audit=card_264bed74b7a346dfbb0d3898aef1c8f8
governed_run=run_946ba867b16947438ac0a50919b66619 outcome=success
frontier_eval=PASS margin=75.0pp
```

No AMS v1 implementation target remains. Future work must be a named post-v1
phase or a regression fix from a failing acceptance check.
