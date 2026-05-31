# AMS Product Lock Audit

Date: 2026-05-31
Source: `PRODUCT-LOCK.md`
Status: acceptance audit updated after runtime trace intake

## Summary

AMS has a working memory engine and local operator surfaces, but the product is
not accepted yet.

The core gap is no longer "can Codex start through AMS" or "does ordinary Codex
work leave a trace." The default Codex entrypoints route through AMS runtime
control, the live memory topology marks AMS as primary, and guarded Codex runs
now write real `AgentTrace` records into the AMS evidence ledger. The remaining
product gap is aging/maintenance as a first-class operator surface, followed by
fresh operator setup proof and product-path eval reruns.

## Acceptance Matrix

| Criterion | Status | Evidence | Missing Work | Next Step |
|---|---|---|---|---|
| A1. Primary Runtime Lock | pass | `scripts/session-start-gate.ps1` passes; dashboard shows latest startup brief allow; global `ams-memory` MCP is configured in `~/.codex/config.toml`; `startup-brief` now writes governed-run receipts with brief, monitor, evidence, cwd, task, status, and block reasons; live Codex hook smoke proves command hooks are invoked; `ams runtime-control` and `scripts/ams-guarded-command.ps1` enforce allow/block before a downstream command is invoked; the npm `codex.ps1`, `codex.cmd`, and Git Bash `codex` shims are wrapped with `codex.ams-original*` backups; `ams memory-surfaces` reports `ams-memory` as primary, `codex-memory` as secondary, and native Codex memory as an applied secondary import source; guarded runs now write `runtime-trace-latest` and ingest CEM traces. | Keep this as a non-regression gate while adding aging/maintenance. | Add aging and maintenance checks. |
| A2. Real Trace Intake | pass | `ams runtime-trace record` loads a runtime-control receipt, creates a real `AgentTrace`, stores it through `CEM.ingest_trace`, proposes marker-backed memory candidates from the trace, and writes `runtime-trace-runs.jsonl`, `runtime-trace-latest.json`, and dashboard `latest_runtime_trace`. `scripts/ams-guarded-command.ps1` records traces automatically after allowed commands and blocked control decisions. Focused tests prove source spans on trace-derived candidates and quiet-wrapper output preservation. | Keep full product-path smoke evidence current. | Treat as a non-regression gate during aging work. |
| A3. Trust Before Retrieval | pass | Validation, quarantine, reason codes, inactive-card filtering, negative controls, and failure canaries exist in tests and monitor paths; trace-derived candidates still enter as proposed atoms before validation/promotion. | Aging/maintenance still needs an operator surface. | Add aging monitor section and review/repair path. |
| A4. Action Briefs Govern Work | pass | `startup-brief` returns bounded directives/cards/evidence/actions; MCP action brief returns applicable ids, evidence ids, score breakdown, and expected action delta source; governed-run receipts attach the startup brief id, action brief id, influence id, monitor id, and evidence ids; `runtime-control` records the startup brief, monitor, governed-run id, gate decision, prompt decision, and evidence ids; `codex --version` through an unseeded temporary AMS root blocks before raw Codex runs; dashboard exposes memory surface reconciliation and latest runtime trace status. | Keep this as a non-regression gate while adding aging/maintenance. | Add aging and maintenance checks. |
| A5. Outcome Influence Loop | pass | Action influence models, persistence, vertical-loop tests, and `ams governed-run close` exist; close finalizes the governed-run receipt with observed outcome, writes an observational influence event, is idempotent, and fails if a receipt lacks action-brief/influence ids; runtime traces record observed command outcome separately from verified lift. | Verified lift remains separate from observed outcome by design. | Keep observed outcome separate from verified lift during aging work. |
| A6. Correction Capture | pass | Correction capture core, CLI, resume gate, monitor checks, PowerShell hook wrappers, `ams runtime-control`, and `scripts/ams-guarded-command.ps1` exist; live Codex smoke verified `UserPromptSubmit` payload keys and prompt/session projection; guarded-command tests prove a correction prompt blocks before the downstream command is invoked; blocked guarded commands now write failure runtime traces with `downstream_invoked=false`. | Keep the resume gate human-approved only. | Treat as a non-regression gate during aging work. |
| A7. Aging And Maintenance | partial | Expired/inactive cards are excluded from retrieval; staleness penalties and stale/supersession tests exist. | Monitor does not yet expose aging/maintenance as a first-class product surface; no operator repair/review command for AMS aging. | Add aging monitor section and review/repair path. |
| A8. Frontier Eval | partial | Baseline ladder, action-advantage metrics, negative-control suppression, latency budget, and full test suite pass. | Eval has not been rerun against the accepted product path after runtime trace intake and the remaining aging/operator surfaces. | Re-run eval after aging and operator proof land. |
| A9. Operator Product | partial | README documents local commands; CLI can init, brief, audit, monitor; session gate and dashboard work in this repo. | No isolated fresh-operator proof that setup works without hidden state from this machine/repo. | Run fresh-root setup proof and update docs from the transcript. |

## Product State

Accepted now:

- AMS product lock exists and is the acceptance source.
- AMS startup gate can allow/block.
- AMS dashboard reports the current adoption phase.
- AMS monitor deep checks pass.
- Action-brief and validation engine tests pass.
- AMS runtime control can block before a downstream command is invoked.
- The default Windows/Git Bash Codex shims now route through AMS guarded control with backups and bypass escape hatch.
- Legacy `codex-memory` and native Codex memory are reconciled under AMS as secondary inputs.
- Governed runs can close/finalize with observed outcome and an observational influence event.
- Guarded Codex work automatically writes runtime traces into the AMS evidence ledger.

Not accepted yet:

- Memory aging and maintenance as an operator surface.
- Fresh operator setup proof.

## Commands Run For This Audit

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1
python scripts/ams.py dashboard
python scripts/ams.py monitor --deep
python scripts/ams.py runtime-control "continue AMS primary runtime adoption" --domain agentic-memory-system
python scripts/ams.py runtime-trace record --control-id <control_id> --command codex --command-arg=--version --exit-code 0
python scripts/ams.py memory-surfaces
python scripts/ams.py governed-run close --outcome success --action-taken "verified current slice"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ams-guarded-command.ps1 -Workspace "C:\Dev\Builds\Agentic Memory System" -Prompt "SKILL: check startup brief before edits" -Quiet -Command cmd.exe /c echo AMS_TRACE_SMOKE
codex --version # with AMS_ROOT set to a fresh temp root; expected block before raw Codex runs
codex exec "we already said no scaffolding; stop and record this correction" # with AMS_ROOT set to a fresh temp root; expected block before raw Codex runs
cmd /c codex --version
bash -lc '/mnt/c/Users/7amma/AppData/Roaming/npm/codex --version'
rg -n "class ActionBrief|score_breakdown|ActionInfluenceEvent|VerificationProbe|negative_control|retrieve_action_brief|startup-brief|correction hook|review_stale|stale|superseded|ingest_trace|Trace" packages scripts tests docs README.md PRODUCT-LOCK.md
```

## Review Risk

The highest-risk blind spot is not a missing unit test in the engine. It is a
product acceptance mismatch: tests can pass while Codex can still ignore AMS in
ordinary work.

The PR review should focus on whether `PRODUCT-LOCK.md`, this audit, and the
execution plan truly force the build back to the intended AMS product.

## Next Implementation Target

Continue A7 next:

1. Add aging and maintenance checks as a product surface.
2. Add an operator review/repair path for stale, expired, inactive, and contradicted memories.
3. Keep A1/A2/A4/A5/A6 as non-regression gates while adding aging work.
