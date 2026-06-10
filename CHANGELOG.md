# Changelog

Canonical repo-level timeline for Agentic Memory System changes.

Use this file for high-signal changes only: shipped behavior, plan changes, verification results, newly discovered gaps, mistakes, and status changes. Put deeper reasoning and follow-up detail in `docs/PROJECT-LEDGER.md`.

## 2026-06-10

### Added

- Opened **AMS V2: Experience Enforcement Architecture** as the named post-v1
  phase in `TODO.md`.
- Added `docs/2026-06-10-ams-v2-experience-enforcement-plan.md` as the canonical
  full-scope V2 execution plan.
- Added `docs/2026-06-10-ams-v2-acceptance-contract.md` with the Phase 0
  acceptance axes, seed corpus, false-block budget shape, red-test rule, and
  receipt rule.
- Added the first AMS V2 Phase 1 schema models: `DecisionIntent` and
  `ExperienceGraphRecord`, including required attribution fields and a compact
  audit summary.
- Wired guarded runtime traces to persist V2 experience graph records and expose
  the latest record through dashboard/operator files.
- Added AMS V2 Phase 2 attribution: `ExperienceAttribution`,
  `ErrorAttributor`, `SuccessAttributor`, the owner-labeled attribution seed
  corpus, attribution storage, runtime attribution receipts, and dashboard
  exposure for the latest attribution.
- Added AMS V2 Phase 3 compilation: `BehaviorInvariant`,
  `SkillCandidate`, `BehaviorInvariantCompiler`, `SkillCompiler`,
  `AuthorityScopeResolver`, invariant/skill storage, runtime compiler calls,
  and dashboard/operator files for latest invariant and skill candidates.
- Added AMS V2 Phase 4 situation matching: `SituationMatch`,
  `SituationMatcher`, exact repeat matching, paraphrase repeat matching,
  valid-neighbor suppression, owner-approved changed-context suppression, skill
  precondition matching, match persistence, and `CEM.match_situation()`.
- Added AMS V2 Phase 5 policy binding: `RuntimeInterceptionBoundary`,
  `ActionDecisionReceipt`, `PolicyBindingLayer`, `ActionDecisionPoint`,
  persisted runtime boundary maps, persisted decision receipts, and
  `CEM.decide_action()` for pre-action verdicts.
- Added AMS V2 Phase 6 reasoning control: `ReasoningControlReceipt`,
  `ReasoningController`, `CEM.control_reasoning()`, constrained downgrade rules,
  visible override/block receipts, silent-steer UX, and persisted reasoning
  control receipts.
- Added AMS V2 Phase 7 supersession: `SupersessionEvent`,
  `SupersessionLedger`, supersession/reversal/owner-override events,
  supersession storage, and active filtering so superseded invariants stop
  firing on equivalent future decisions.
- Added AMS V2 Phase 8 multi-agent governance:
  `SharedExperienceEnvelope`, `MultiAgentGovernanceReceipt`,
  `MultiAgentGovernanceLayer`, `CEM.govern_shared_experience()`, governance
  persistence, writer identity, cross-agent authority ranking, visibility and
  ownership constraints, scope-pollution rejection, and conflict receipts.

### Changed

- Locked the correction that the non-repeat enforcement kernel is part of AMS
  V2, not a V1.5 downgrade or smaller substitute.
- Expanded V2 scope to include experience graph and decision intent capture,
  error/success attribution, authority and scope resolution, behavior
  invariants, procedural skill memory, situation matching, policy binding,
  action decision points, reasoning control, under-the-hood inference receipts,
  supersession, multi-agent governance, and the V2 eval battery.
- Updated monitor/dashboard phase status so AMS V2 Phase 9 is the active rail
  after Phase 8 multi-agent experience governance.

### Next

- Start AMS V2 Phase 9: NonRepeatEval, FalseBlockEval,
  ApprovedExperimentEval, SkillTransferEval, SupersessionEval,
  MultiAgentConflictEval, and ContextPollutionEval.

### Verified

- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> `2 passed`.
- Full AMS CLI test file: `python -m pytest tests/test_ams_cli.py -q` -> passed.
- Phase 1 red->green proof: `python -m pytest tests/test_evidence_models.py -q`
  failed before implementation because `DecisionIntent` was missing, then
  passed after adding the schema models.
- `python -m compileall -q packages/cem-core/src/cem_core` passed.
- Export smoke:
  `$env:PYTHONPATH='packages/cem-core/src'; python -c "from cem_core import DecisionIntent, ExperienceGraphRecord; print(DecisionIntent.__name__, ExperienceGraphRecord.__name__)"`
  -> `DecisionIntent ExperienceGraphRecord`.
- Full suite: `python -m pytest -q` -> passed.
- Runtime capture red->green proof:
  `python -m pytest tests/test_storage_evidence.py::test_experience_graph_record_roundtrip_in_both_backends -q`
  failed before persistence existed, then passed.
- Runtime trace red->green proof:
  `python -m pytest tests/test_ams_cli.py::test_ams_cli_runtime_trace_records_controlled_work_and_candidates -q`
  failed before `decision_id` existed, then passed.
- Affected files:
  `python -m pytest tests/test_storage_evidence.py tests/test_ams_cli.py tests/test_evidence_models.py -q`
  -> passed.
- Full suite after Phase 1 runtime capture: `python -m pytest -q` -> passed.
- `git diff --check` passed with only expected Windows CRLF warnings.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 2 - Error and success attribution`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 0 status wiring after contract lock" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 1 next step.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 1 runtime capture completion and Phase 2 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 2 next step.
- Phase 2 red->green proof:
  `python -m pytest tests/test_attribution.py -q` failed before implementation
  because `cem_core.attribution` did not exist, then passed after adding
  deterministic attribution.
- Scope-trap canary:
  `python -m pytest tests/test_attribution.py::test_error_attributor_marks_general_owner_correction_as_non_repeat_mistake -q`
  failed while the attributor preserved `project` scope, then passed after
  general Codex/AMS correction evidence promoted the scope candidate to
  `global_agent_behavior`.
- Phase 2 focused checks:
  `python -m pytest tests/test_attribution.py -q` -> passed.
- Runtime attribution checks:
  `python -m pytest tests/test_storage_evidence.py tests/test_ams_cli.py::test_ams_cli_runtime_trace_records_controlled_work_and_candidates -q`
  -> passed.
- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> passed.
- `python -m compileall -q packages/cem-core/src/cem_core` -> passed.
- Full suite: `$env:PYTHONIOENCODING='utf-8'; python -m pytest -q --tb=short --disable-warnings`
  -> passed. An earlier default-timeout full-suite attempt was interrupted by
  the command timeout and pytest's Windows stdout flush error during shutdown,
  then the longer quiet rerun passed.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 3 - Invariants, skills, and authority scope`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 2 attribution completion and Phase 3 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 3 next step.
- Phase 3 red->green proof:
  `python -m pytest tests/test_phase3_compilers.py -q` failed before
  implementation because `cem_core.compilers` did not exist, then passed after
  adding invariant, skill, and authority compilers.
- Phase 3 focused checks:
  `python -m pytest tests/test_phase3_compilers.py tests/test_storage_evidence.py -q`
  -> passed.
- Runtime compiler checks:
  `python -m pytest tests/test_ams_cli.py::test_ams_cli_runtime_trace_records_controlled_work_and_candidates tests/test_ams_cli.py::test_ams_cli_runtime_trace_compiles_failure_into_behavior_invariant -q`
  -> passed.
- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> passed.
- `python -m compileall -q packages/cem-core/src/cem_core` -> passed.
- Full suite: `$env:PYTHONIOENCODING='utf-8'; python -m pytest -q --tb=short --disable-warnings`
  -> passed.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 4 - Situation matching`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 3 compiler completion and Phase 4 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 4 next step.
- Phase 4 red->green proof:
  `python -m pytest tests/test_situation_matching.py -q` failed before
  implementation because `cem_core.matching` did not exist, then passed after
  adding match receipts and `SituationMatcher`.
- Phase 4 focused checks:
  `python -m pytest tests/test_situation_matching.py -q` -> passed.
- Situation match storage:
  `python -m pytest tests/test_storage_evidence.py::test_situation_match_roundtrip_in_both_backends -q`
  -> passed.
- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> passed.
- `python -m compileall -q packages/cem-core/src/cem_core` -> passed.
- Full suite: `$env:PYTHONIOENCODING='utf-8'; python -m pytest -q --tb=short --disable-warnings`
  -> passed.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 5 - Action decision point and policy binding`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 4 situation matching completion and Phase 5 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 5 next step.
- Phase 5 red->green proof:
  `python -m pytest tests/test_policy_binding.py -q` failed before
  implementation because `RuntimeInterceptionBoundary` did not exist, then
  passed after adding the policy binding layer.
- Phase 5 focused checks:
  `python -m pytest tests/test_policy_binding.py -q` -> passed.
- Boundary and receipt storage checks:
  `python -m pytest tests/test_storage_evidence.py::test_action_decision_receipt_roundtrip_in_both_backends tests/test_storage_evidence.py::test_runtime_interception_boundary_roundtrip_in_both_backends -q`
  -> passed.
- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> passed.
- `python -m compileall -q packages/cem-core/src/cem_core` -> passed.
- Full suite: `$env:PYTHONIOENCODING='utf-8'; python -m pytest -q --tb=short --disable-warnings`
  -> passed.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 6 - Reasoning controller and under-the-hood UX`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 5 action decision point completion and Phase 6 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 6 next step.
- Phase 6 red->green proof:
  `python -m pytest tests/test_reasoning_controller.py -q` failed before
  implementation because `ReasoningControlReceipt` did not exist, then passed
  after adding reasoning control.
- Phase 6 focused checks:
  `python -m pytest tests/test_reasoning_controller.py -q` -> passed.
- Reasoning receipt storage:
  `python -m pytest tests/test_storage_evidence.py::test_reasoning_control_receipt_roundtrip_in_both_backends -q`
  -> passed.
- Policy-to-reasoning chain:
  `python -m pytest tests/test_policy_binding.py tests/test_reasoning_controller.py -q`
  -> passed.
- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> passed.
- `python -m compileall -q packages/cem-core/src/cem_core` -> passed.
- Full suite: `$env:PYTHONIOENCODING='utf-8'; python -m pytest -q --tb=short --disable-warnings`
  -> passed.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 7 - Supersession and active forgetting`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 6 reasoning controller completion and Phase 7 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 7 next step.
- Phase 7 red->green proof:
  `python -m pytest tests/test_supersession.py -q` failed before
  implementation because `cem_core.supersession` did not exist, then passed
  after adding supersession events and active filtering.
- Phase 7 focused checks:
  `python -m pytest tests/test_supersession.py -q` -> passed.
- Supersession storage:
  `python -m pytest tests/test_storage_evidence.py::test_supersession_event_roundtrip_in_both_backends -q`
  -> passed.
- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> passed.
- `python -m compileall -q packages/cem-core/src/cem_core` -> passed.
- Full suite: `$env:PYTHONIOENCODING='utf-8'; python -m pytest -q --tb=short --disable-warnings`
  -> passed.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 8 - Multi-agent experience governance`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 7 supersession completion and Phase 8 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 8 next step.
- Phase 8 red->green proof:
  `python -m pytest tests/test_multi_agent_governance_v2.py -q` failed before
  implementation because `cem_core.multi_agent_governance` did not exist, then
  passed after adding shared-experience governance.
- Phase 8 focused checks:
  `python -m pytest tests/test_multi_agent_governance_v2.py -q` -> passed.
- Governance storage:
  `python -m pytest tests/test_storage_evidence.py::test_shared_experience_governance_roundtrip_in_both_backends -q`
  -> passed.
- Phase 8 combined focused checks:
  `python -m pytest tests/test_multi_agent_governance_v2.py tests/test_storage_evidence.py::test_shared_experience_governance_roundtrip_in_both_backends -q`
  -> passed.
- Focused phase-status regression:
  `python -m pytest tests/test_ams_cli.py -k "monitor_and_dashboard_records_status or dashboard_separates_ams_and_global_behavior_records" -q`
  -> passed.
- `python -m compileall -q packages/cem-core/src/cem_core` -> passed.
- Full suite: `$env:PYTHONIOENCODING='utf-8'; python -m pytest -q --tb=short --disable-warnings`
  -> passed.
- Live `python scripts/ams.py monitor --json` reports current phase
  `AMS V2 Phase 9 - V2 eval harness`.
- Live `python scripts/ams.py startup-brief "verify AMS V2 Phase 8 multi-agent governance completion and Phase 9 active status" --domain codex-harness --json`
  returns `status=allow` and the V2 Phase 9 next step.
- `git diff --check` passed with only expected Windows CRLF warnings.

## 2026-06-09

### Fixed

- Corrected the startup-control architecture so Monitor-0 failures and missing required memory become `degraded` non-blocking startup/runtime status by default instead of `block`. Explicit blocking is reserved for the separate runtime-control/action-safety lane.
- Added `degraded_reasons` to startup briefs, governed-run receipts, and runtime-control receipts so memory infrastructure warnings remain auditable without becoming command authority.
- Updated `scripts/session-start-gate.ps1` to allow `degraded` startup briefs while printing the degraded reasons.
- Moved active correction resume enforcement out of startup memory readiness and kept it in `runtime-control` through the explicit correction gate decision.
- Converted startup-brief infrastructure exceptions into `runtime-control` degraded reasons so guarded commands continue unless runtime-control returns an explicit action-safety `block`.
- Converted `scripts/session-start-gate.ps1` from a hard startup gate into a warning surface: missing `ams.py`, startup-brief command failure, malformed output, unknown status, or startup `block` now report `SESSION_GATE_DEGRADED` and exit 0.
- Converted `scripts/ams-guarded-command.ps1` missing-`ams.py` handling from fail-closed to degraded/non-blocking so an absent AMS script cannot stop an unrelated owner command.
- Superseded stale live AMS card `card_3b90d70eb3ac475286cc96cb59646011`, which still claimed safety-critical missing directives could block, and recorded replacement card `card_db1b028bfc664fa097f2dd7f01598d92`.
- Corrected memory-surface reconciliation for the AMS-only Codex default: `ams-memory` as primary plus native Codex Memories disabled now reconciles even when the unfinished `codex-memory` bridge is not configured. The bridge is reported as an optional warning, not a readiness dependency.
- Corrected the live Codex memory wiring: native Codex Memories are explicitly disabled in `C:\Users\7amma\.codex\config.toml`, `ams-memory` is registered as the primary MCP, and existing Codex automations now start from AMS startup/action briefs instead of old Markdown/native memory defaults.

### Verified

- Red proof before implementation: focused regression tests failed because monitor failure returned `block`, runtime-control exited `12`, and no `degraded_reasons` field existed.
- Green proof after implementation: `python -m pytest tests/test_ams_cli.py -k "startup_brief_degrades_unreconciled_memory_surfaces or runtime_control_does_not_block_unrelated_owner_task_on_monitor_failure or startup_brief_degrades_when_required_memory_is_missing"` -> `3 passed`.
- Follow-up correction proof: `python -m pytest tests/test_ams_cli.py -k "startup_brief_degrades_when_required_memory_is_missing or correction_capture_records_plan_first_violation_and_blocks_resume"` -> `2 passed`.
- Final review remediation proof: `python -m pytest tests/test_ams_cli.py -k "startup_brief_infrastructure_fails or runtime_control_infrastructure_fails or unknown_startup_status or startup_brief_command_failure"` -> `4 passed`.
- Missing-`ams.py` red->green proof: temporarily restored the old fail-closed launcher behavior, then `python -m pytest tests/test_ams_cli.py -k "guarded_command_runs_downstream_when_ams_script_is_missing"` failed; restored the fix and the same command passed.
- Final focused regression group: `python -m pytest tests/test_ams_cli.py -k "guarded_command_runs_downstream_when_ams_script_is_missing or runtime_control_infrastructure_fails or unknown_startup_status or startup_brief_command_failure or startup_brief_infrastructure_fails"` -> `5 passed`.
- Broader affected suite: `python -m pytest tests/test_ams_cli.py -k "startup_brief or runtime_control or runtime_trace or guarded_command or session_start_gate or monitor"` -> `24 passed`.
- Full suite: `python -m pytest` -> `211 passed`.
- `python scripts/run_synthetic_eval.py` -> pass with false-memory resistance `1.0`, contradiction precision/recall `1.0`, and false quarantine rate `0.0`.
- Fresh operator proof: `python scripts/run_ams_operator_proof.py --root tmp\ams-operator-proof-monitor-degraded-fix` -> `AMS_OPERATOR_PROOF_PASS`.
- Live session gate on the current global root -> `SESSION_GATE_DEGRADED`, allowed with `monitor_failed:*` warning.
- Live MTM incident replay from `C:\Dev\MTM Final AI approach\MTM OS\mtm-os`: `startup-brief "Review third meeting transcript, Claude analysis, and low-quality voice-note transcription options" --domain mtm-os --json` -> `status=degraded`, `block_reasons=[]`, `degraded_reasons=["monitor_failed:*"]`.
- Live AMS retrieval check no longer surfaces the stale missing-directives blocking card; audit shows `card_3b90d70eb3ac475286cc96cb59646011` as `promotion_status=superseded`.
- Independent Codex review found two issues: active correction gates were degraded and degraded trace/close surfaces lacked tests. Both were fixed. Re-review then found session-start could still fail-closed on unknown startup status; that was fixed with a degrade/allow PowerShell regression. Later review found a missing-`ams.py` fail-closed launcher path plus stale docs; both were fixed. Final independent re-review reported no actionable findings, with the caveat that its read-only sandbox could not run tests. Local final affected suite passed (`24 passed`) and full suite passed (`211 passed`).
- AMS-only default red proof: `python -m pytest tests/test_ams_cli.py::test_ams_cli_memory_surfaces_reconcile_ams_only_when_native_memory_disabled -q` failed before the reconciliation fix because `report["reconciled"]` was `False`.
- AMS-only default green proof: the same focused regression passed, and the affected memory/startup/runtime cluster passed (`6 passed`).
- Live global memory proof: `python scripts/ams.py memory-surfaces --json` -> `reconciled=true`, `ams-memory=primary/pass`, `codex-memory=unconfigured/warn`, `native-codex-memory=secondary_import_source/pass` with native Codex Memories disabled/import-only.
- Live Codex config proof: TOML parse showed `features.memories=False`, `memories.generate_memories=False`, `memories.use_memories=False`, and `ams-memory.command=python`; `codex mcp list` showed `ams-memory` enabled; `codex features list` showed `memories experimental false`; direct MCP stdio initialize/tools-list returned the CEM tool list.
- Refreshed live Monitor-0 after the config repair -> `status=pass`, `memory_surfaces_reconciled=pass`, detail `ams-memory primary; codex-memory optional bridge unconfigured; native Codex memory disabled/import-only`.
- Independent local `codex review --base staging` found one P2: AMS-only reconciliation would pass if native Codex Memories were not disabled but no `MEMORY.md` existed yet. Added a regression for that exact case and tightened reconciliation to require native-memory disablement for AMS-only mode, or the old secondary bridge plus imported native registry for bridge mode.
- Final AMS-only verification: `python -m pytest -q` passed; `python scripts/run_ams_operator_proof.py --root tmp\ams-operator-proof-ams-only-memory-p2` -> `AMS_OPERATOR_PROOF_PASS`.
- `git diff --check` -> clean aside from expected Windows CRLF warnings.

## 2026-06-01

### Added

- Added `scripts/run_ams_operator_proof.py`, the terminal AMS v1 operator proof. It creates a fresh local AMS root, seeds only documented inputs, reconciles `ams-memory` as primary, retrieves a startup brief, runs maintenance and Monitor-0 deep checks, audits a real card, closes the governed run with outcome success, and reruns the Phase 4 frontier eval.
- Added `tests/test_ams_operator_proof.py` so the fresh-root operator path cannot silently become documentation-only.

### Changed

- Froze the AMS v1 terminal scope in `TODO.md`: A1-A9 are listed once, all checked, and no new TODO item may be added to redefine AMS v1 as "really done." Future work must be post-v1 or a regression fix.
- Updated dashboard/monitor phase status to `AMS v1 Accepted`, `ready_for_next_phase=True`, and no open follow-ups.
- Updated `PRODUCT-LOCK.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, and the product-lock audit to reflect AMS v1 acceptance.

### Verified

- `python scripts/run_ams_operator_proof.py --root tmp\ams-operator-proof-final` -> `AMS_OPERATOR_PROOF_PASS`; startup `brief_f3a88b2624454ddd886505de39e407f6`; monitor `monitor_17adf0c7bc9f4d84a906210bce318d0f`; maintenance items `0`; audit `card_264bed74b7a346dfbb0d3898aef1c8f8`; governed run `run_946ba867b16947438ac0a50919b66619 outcome=success`; frontier eval `PASS margin=75.0pp`.
- `python -m pytest tests/test_ams_operator_proof.py -q` -> `1 passed`.
- Focused operator proof/status canaries -> `3 passed`.
- `python scripts/ams.py monitor --deep` -> pass (`monitor_f62d9107b19941959a79caceda35c264`) with phase `AMS v1 Accepted`, next `none - AMS v1 terminal acceptance contract is complete`.
- `python -m pytest` -> `203 passed`.

## 2026-05-31

### Added

- Added `PRODUCT-LOCK.md` as the canonical AMS product acceptance lock: product line, scope, acceptance criteria, current status, planning order, and completion rule.
- Added `docs/2026-05-31-ams-product-lock-execution-plan.md` to map the product lock into the first planning moves without redefining scope.
- Added `docs/2026-05-31-ams-product-lock-audit.md` with pass/partial/fail status for Product Lock criteria A1-A9.
- Added `docs/2026-05-31-ams-review-prompts.md` with a Greptile PR review request and optional Codex review preflight prompt.
- Added governed-run receipts to `startup-brief`: each run now records receipt id, startup brief id, monitor id, cwd, task description, evidence ids, status, and block reasons; dashboard exposes the latest governed run.
- Added `docs/2026-05-31-codex-hook-runtime-smoke.md` with live Codex hook evidence.
- Added `ams runtime-control` and `scripts/ams-guarded-command.ps1` as the enforceable AMS-owned runtime path: AMS records launcher control receipts, and the guarded launcher refuses to invoke the downstream command when runtime-control/action-safety blocks.
- Added `scripts/install-ams-codex-entrypoint.ps1` to install, restore, and smoke-test AMS-wrapped Codex shims with `codex.ams-original*` backups.
- Added `ams memory-surfaces` plus dashboard reporting for the active memory topology: `ams-memory` primary, `codex-memory` secondary, and native Codex memory accepted only after an applied AMS migration.
- Added `ams governed-run close` to finalize governed-run receipts with observed outcome and an observational influence event linked to the startup/action brief.
- Added `ams runtime-trace record` and automatic guarded-command trace capture: ordinary AMS-guarded Codex work now writes real `AgentTrace` records, proposes marker-backed memory candidates with source spans, persists `runtime-trace-latest`, and exposes the latest trace in the dashboard.
- Added `ams maintenance review` as the AMS aging/maintenance product surface: expired active cards, stale active cards, active contradiction links, inactive card counts, and stale pending atoms are reported with operator review actions; reports persist to `maintenance-runs.jsonl`, `maintenance-latest.json`, and `maintenance-latest.md`; dashboard exposes `latest_maintenance`.

### Changed

- Locked product language to one line: **AMS**. Active source-of-truth docs now point to `PRODUCT-LOCK.md` for acceptance and avoid treating older internal labels as the product identity.
- New bootstrap, migration, correction, README, TODO, and runtime-facing text now uses AMS product language. Legacy internal labels are recognized only for backwards-compatible parsing/classification.
- Corrected the primary runtime adoption rail after live proof: Codex CLI 0.128.0 invokes command hooks but does not block on non-zero hook exits, so AMS now uses its own runtime-control/guarded-command path instead of another payload-shape check.
- Advanced the active next step from command-hook enforcement replacement through default Codex entrypoint wiring.
- Advanced the active next step again after installing the default Codex shims, reconciling memory surfaces, adding governed-run close/finalize, wiring automatic runtime trace intake, and adding maintenance review; the current next rail is packaging the local operator path.

### Fixed

- Addressed Greptile PR-loop safety findings that still applied in the live branch: governed-run receipts are written before startup briefs can claim them, receipt ids are generated before model construction, run-close/finalization fields are reserved on receipts, bootstrap AMS directive counting is no longer checkout-path-sensitive, live `prompt` hook payloads are accepted by the Python adapter on every platform, multi-atom card audits surface the latest validation decision, influence close is idempotent per brief, `SCORER_VERSION` has one source of truth, single-task MMA cannot pass the confidence gate, and correction resume cannot mint phantom receipts when the gate is already clear.
- Addressed Codex review's WSL shim finding: when the generated Git Bash/WSL `codex` shim converts `basedir` to a Windows path, it now prefers `powershell.exe` before Linux `pwsh`, preventing Linux PowerShell from receiving an unusable `C:\...` script path.
- Addressed Codex review's primary-runtime findings at the time: Monitor-0 gated on memory-surface reconciliation, and AMS directive scoping matched the acronym on token boundaries instead of substring-matching unrelated words like `teams`, `params`, or `diagrams`. The Monitor-0 startup-block behavior was superseded on 2026-06-09 by degraded/non-blocking startup memory readiness.
- Addressed Codex review's maintenance/reconciliation findings: memory-surface reconciliation now reads the latest applied migration even after a later dry-run, and maintenance review skips atoms already referenced by cards so promoted evidence is not mislabeled as stale pending work.
- Addressed Codex review's guarded-launch finding: an allowed guarded command that fails to launch now records a failed runtime trace with exit code 127 before the wrapper exits, so automatic runtime trace intake covers missing executable/path failures.
- Addressed Codex review's installer-backup finding: reinstalling AMS over a fresh non-wrapped Codex shim now refreshes `codex.ams-original*` backups, so wrappers and uninstall restore the current raw shim rather than a stale pre-upgrade backup.
- Addressed Codex review's guarded-persistence findings: quiet guarded invocations now surface AMS trace-recording failures to stderr, and the guarded launcher closes the governed-run receipt after blocked, allowed, and downstream-launch-failure outcomes.
- Addressed Codex review's monitor-surface findings: memory-surface reconciliation now accepts an `ams-memory` MCP `--root` arg or `CEM_ROOT` env value when `AMS_ROOT` is absent, and maintenance review flags active cards that have no validation freshness anchor.

### Verified

- `python -m pytest` -> 193 passed.
- `python scripts/ams.py monitor --deep` -> pass (`monitor_c2f34660e7cf4f618f6a9c7cd4db24f4`).
- `python scripts/ams.py startup-brief "continue AMS primary runtime adoption" --domain agentic-memory-system` -> allow with a governed-run receipt and AMS-only active action text.
- `python scripts/ams.py runtime-control "continue AMS primary runtime adoption" --domain agentic-memory-system` -> allow (`control_21266e4ab3274b73972bfb84aadbd761`) with startup brief, governed-run, monitor, prompt decision, and gate decision attached.
- `codex exec` live hook smoke -> `UserPromptSubmit` payload includes `prompt` + `session_id`; `PreToolUse` is invoked before tools; non-zero command-hook exits are advisory in Codex CLI 0.128.0.
- Focused AMS CLI verification -> `28 passed`, including the portable checkout-path canary and the blocked guarded-command canary that proves the downstream command is not invoked.
- Focused Codex entrypoint installer verification -> `2 passed`; focused entrypoint + phase-status verification -> `3 passed`.
- Real npm Codex shims installed with backups; PowerShell `codex --version`, `cmd /c codex --version`, and WSL `/mnt/c/Users/7amma/AppData/Roaming/npm/codex --version` all return `codex-cli 0.128.0`.
- Fresh-root default-entrypoint smoke: `codex --version` with temp `AMS_ROOT` blocks before raw Codex runs (`control_253ccfd23f9e4db384cc39e8822af226`).
- Correction default-entrypoint smoke: `codex.ps1 exec "we already said no scaffolding; stop and record this correction"` with temp `AMS_ROOT` blocks before raw Codex runs (`control_43d400ec00c3484899571952e5785889`).
- `python scripts/ams.py memory-surfaces` -> reconciled; `ams-memory` primary, `codex-memory` secondary, native Codex memory secondary import source via `migration_8b2e1532c74b4cdd896d78d787d4e4d0`.
- Focused memory-surface and phase-status canaries -> `4 passed`, including the failure case where native memory remains `warn` until migration is applied.
- Focused governed-run close/finalize and phase-status canaries -> `4 passed`, including idempotent close and the failure case for receipts missing action-brief/influence ids.
- Live `python scripts/ams.py governed-run close --receipt-id run_f24ec46f59b14b49aa204d5a75f3ee69 --outcome success ...` -> closed with `influence_ba6f90954fc14042965b163794b4fb95`; dashboard showed `closed=True outcome=success`.
- Focused runtime trace intake suite -> `9 passed`, including source-span candidate extraction, missing-control failure, blocked-command failure trace, and quiet raw output preservation.
- Live guarded-command smoke -> `AMS_TRACE_SMOKE` printed cleanly while dashboard recorded `latest_runtime_trace: success trace_c33a54d6d6c84959bb9e3ec8a28d8ed3 atoms=1`; dashboard now reports next step `add aging and maintenance checks as a product surface`.
- Codex review loop -> found one P2 in the generated WSL shell shim; fixed and verified with focused entrypoint/runtime tests (`5 passed`) and full `python -m pytest` (`193 passed`). Reinstalled the real npm Codex shims; PowerShell `codex --version` and WSL `/mnt/c/Users/7amma/AppData/Roaming/npm/codex --version` both return `codex-cli 0.128.0`.
- Focused maintenance review suite -> `4 passed`, including expired/stale/contradicted/inactive report canaries, dashboard `latest_maintenance`, monitor blocking-risk visibility, and expired-record action-brief exclusion.
- Surrounding AMS CLI/runtime suite -> `48 passed`.
- Codex review loop -> found two primary-runtime findings: memory-surface reconciliation was dashboard-only, and AMS acronym scoping was substring-based. Both fixed with canaries.
- Focused Codex-review remediation canaries -> `6 passed`.
- Second Codex review loop -> found two P2 edge cases: dry-run migration invalidated reconciliation and promoted evidence atoms appeared pending in maintenance. Both fixed with canaries.
- Focused second-pass remediation canaries -> `4 passed`.
- Surrounding AMS CLI/runtime/entrypoint suite -> `57 passed`.
- Full `python -m pytest` -> `202 passed`.
- Live `powershell -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1` -> pass (`brief_b9422ecd489343bbab353850312db302`, monitor `monitor_da9f21a012de4c3eb1b056270e4b6ef5`).
- Live `python scripts/ams.py maintenance review` -> pass (`maintenance_cbdf5de418994987b92783f872dc84d4`) with 8 active cards, 0 inactive cards, 0 expired active, 0 stale active, 0 contradicted active, and no review items.
- Live `python scripts/ams.py monitor --deep` -> pass (`monitor_3d8026c8efd2428b8d36102d3caad845`); `memory_surfaces_reconciled` passed, maintenance checks passed with `expired_active=0`, `stale_active=0`, `contradicted_active=0`, `inactive=0`, `stale_pending_atoms=0`, and deep synthetic eval passed.
- Live `python scripts/ams.py dashboard` -> next step `package the local operator path`, latest monitor `monitor_3d8026c8efd2428b8d36102d3caad845`, and latest maintenance `maintenance_d23ab68f98d3446995673ae38ff2e76a items=0`.
- Third Codex review loop -> found one P2 guarded-launch trace gap; fixed with a launch-failure canary. Focused guarded-command canaries -> `4 passed`.
- Fourth Codex review loop -> found one P2 stale-backup installer gap; fixed with a reinstall/upgrade canary. Focused installer canaries -> `3 passed`.
- Fifth Codex review loop -> found two P2 guarded-persistence gaps: quiet mode could hide trace-recording failures, and guarded runs could leave governed-run receipts open. Both fixed with canaries. Focused guarded-command persistence canaries -> `5 passed`.
- Sixth Codex review loop -> found two P2 monitor-surface gaps: `ams-memory` configured only through MCP `--root` was falsely marked unreconciled, and active cards without freshness anchors could pass maintenance. Both fixed with canaries. Focused monitor-surface canaries -> `4 passed`.
- Final Codex review loop -> no discrete actionable regressions; diff inspected against the merge base and full `python -m pytest -q` passed inside the review.

## 2026-05-30

### Fixed

- Corrected the live phase status: dashboard/monitor no longer reports the already-resolved §12 hook-wiring work as the next active step. The active track is now **AMS Primary Runtime Adoption**.

### Changed

- Added the remaining primary-adoption rail to `TODO.md`: live Codex hook-payload smoke, governed-run brief/monitor/evidence ids, and reconciliation of legacy Codex memories / `codex-memory` / `ams-memory` so AMS becomes the primary startup source.

## 2026-05-29

### Added

- Locked the **CEM-1 Full Kernel Build** contract (Phase 0). New evidence primitives `VerificationProbe`, `VerificationResult`, `ActionBriefRecord`, `ActionInfluenceEvent`, plus `ConfidenceInterval` and the `ExpectedActionDeltaSource` enum.
- Extended `ExperienceCard` with lifecycle fields (`promotion_status`, `measured_lift`, `measured_lift_ci`, `verification_result_ids`, deactivation/supersession) and `ActionBrief` with influence/scoring fields.
- Added SQLite + in-memory persistence for verification probes, verification results, action-brief records, and action-influence events in both store backends.
- Added `apply_verification_result()` to the kernel — the only path that can set a card `promotion_status="verified"`.
- Added `packages/cem-eval/src/cem_eval/eval_protocol.py`: the locked Marginal Memory Advantage metric (paired delta + 95% CI), the 10-baseline ladder (`human_runbook` flagged ceiling), the >=5pp lexical-overlap margin, and a leakage guard.
- Added `tests/test_no_fake_green_guard.py`: a static AST guard that fails new literal-bool health checks (the two `operations.py` offenders pinned as tracked debt).
- Added `docs/2026-05-28-cem-1-phase-0-contract-lock-plan.md` (Phase 0 implementation plan).
- Completed **Phase 1 (full vertical skeleton)**: a real end-to-end `trace -> atom -> validate -> candidate card -> action brief -> influence event` loop on persisted SQLite objects, no stubs. `retrieve_action_brief` now persists an `ActionBriefRecord` and emits a sourced `expected_action_delta` (`observational_unverified` when cards are selected, otherwise `none`); `close_influence` writes an observational `ActionInfluenceEvent` that never promotes a card or sets `measured_lift`.
- Added `packages/cem-eval/src/cem_eval/vertical_loop.py` (`run_vertical_loop` + `VerticalLoopReport`) and `scripts/run_cem_vertical_loop.py` as a real CLI consumer. Report counts come from real store queries; the runner enforces the leakage guard. First loop: MMA 1.0, n=2, CI [1.0, 1.0] (toy skeleton smoke, not the Phase 4 exam). Scorer stays `lexical_overlap_v0` (the action-value scorer is Phase 3).
- Added `docs/2026-05-29-cem-1-phase-1-vertical-skeleton-plan.md` (Phase 1 implementation plan).
- Completed **Phase 2 (grounded consolidation + verification)**. Consolidation now runs the full §4.4 pipeline: card-level **temporal supersession** (a newer contradicting atom marks the stale card `superseded` with `deactivated_at`/`deactivated_reason`/`superseded_by_card_ids` and `_card_in_scope` drops it from retrieval) and cross-scope **contradiction links** (two cards with the same claim key but different values in different operational scopes are bidirectionally cross-linked via `contradicts_card_ids` and both stay active — feeding the Phase 3 contradiction penalty). The **verified lifecycle** (§4.2) is evidence-gated end-to-end: `schedule_probe`/`run_probe` measure held-out replay lift (memory arm minus a 0.0 no-memory control) and only `apply_verification_result` promotes to `verified` when lift ≥ threshold; `inject_negative_control` plants a retrievable bad card that `run_probe` deprecates and removes from retrieval, gated by `negative_control_suppression_rate()` (a leak canary forces a control to `verified` and asserts the rate drops below 1.0).
- Wired the Phase 2b machinery into a real caller: `run_vertical_loop` now probes each seeded candidate to `verified` and suppresses an injected negative control, reporting `verified_card_count` and `negative_control_suppression_rate`. `card_count` now tallies active cards so the deactivated control does not inflate it. Scorer stays `lexical_overlap_v0` (action-value scorer is Phase 3).
- Completed **Phase 4 (MMA + 10-baseline exam)**. Added the missing kill-criterion gate to the locked eval protocol (`beats_lexical_by_margin` / `lexical_margin_pp`; `LEXICAL_MARGIN_PP` had no consumer), the held-out dataset (`phase4_dataset.py`: 12 fresh operator-phrased tasks + the corruption-fixture memory source, with a namespace-disjoint leakage guard and a no-verbatim-task-statement lint), the exam runner (`phase4_exam.py`: all 10 `BASELINE_LADDER` rungs run honestly per held-out task, paired MMA + 95% CI per rung, the two gates `mma_passes(cem)` + `beats_lexical_by_margin(cem, lexical)`, weight snapshot, and a PASS/FAIL_REPORTED_HONESTLY verdict), and `scripts/run_phase4_exam.py`. **Single-shot held-out result at the LEDGER-018 locked weights: CEM MMA 0.833 (95% CI [0.613, 1.054], n=12) vs lexical 0.083 → margin 75.0pp; verdict PASS.** Negative-control suppression 1.0; CEM beats every honest baseline (best non-CEM = summary 0.333) and sits below the human_runbook ceiling (1.0). The margin is earned: the lexical/vector/full-context rungs surface the planted poisoned/stale/contradictory traps that CEM validates and consolidates away.
- Completed **§12 Correction Capture live runtime hooks** (the last open item from the project's original state — wiring the controller into a LIVE agent runtime beyond the manual CLI). New `cem_core/correction_hooks.py` pure decision core: `hook_on_user_prompt_submit(root, prompt_text, ...)` classifies a live prompt FIRST and short-circuits a benign prompt to ALLOW with zero side effects, else captures the correction and returns BLOCK; `hook_on_pre_tool_use_gate(root)` DENIES continuation while the resume gate is armed and FAILS CLOSED on a corrupt gate. A `HookDecision` (StrictModel) carries the decision + named exit codes (`HOOK_EXIT_ALLOW=0`/`BLOCK=10`/`GATE_BLOCKED=11`/`PARSE_ERROR=2`). Two CLI subcommands (`correction hook-prompt` reads an untyped stdin payload tolerating unknown runtime keys + a UTF-8 BOM; `correction hook-gate`) map the decision to the process exit code via a single `main()` branch, with a `_emit` hook branch keyed on a unique discriminator. Two PowerShell wrappers (`scripts/correction-hook-prompt.ps1`, `correction-hook-gate.ps1`) mirror `session-start-gate.ps1` (pipe stdin, stdout-only, branch on `$LASTEXITCODE`); the live runtime's payload→`prompt_text` field projection lives only in the wrapper and is tagged **[UNVERIFIED]** until a live runtime smoke. There is deliberately NO agent-callable resume surface — the gate clears only via the existing human-approved `correction resume`. A Monitor-0 bridge test proves the live hook and the manual CLI/session-start gate share ONE gate (single source of truth). **15 new tests; both gate canaries proven to bite; the PS wrappers smoke-verified end-to-end (benign→0, correction→10, gate→11) in an isolated root — which caught a real PowerShell UTF-8-BOM stdin bug that pure pytest missed.**
- Completed **Phase 5 (hardening)**. (1) **Shared `card_is_inactive(card)` predicate** promoted to module level in `kernel.py` (CEM staticmethod delegates to it; adopted by `_supersede_stale_cards` and the eval `vertical_loop` active-card count; exported from `cem_core`), so every consumer classifies card inactivity on one axis (status OR deactivation). (2) **Latency-budget readiness gate**: pre-registered `RETRIEVAL_LATENCY_BUDGET_MS=50.0` + `within_latency_budget(measured_ms, *, budget_ms)` (smaller-is-better `<=`, 6dp rounding) in `eval_protocol.py`; the Phase 4 exam now measures p95 CEM-rung retrieval latency (dedicated `_measure_cem_retrieval_latency` pass, reusing `_measure_ms`/`_p95`), reports `p95_retrieval_latency_ms`/`retrieval_latency_budget_ms`/`within_latency_budget`, and fails closed if the sample count ≠ task count. The MMA PASS/FAIL verdict is **unchanged** — latency is a readiness flag only. (3) **Failure-mode coverage** (`tests/test_fail_closed.py`): empty-store retrieval degrades to a graceful empty brief; missing card/atom ids raise `KeyError` (store + kernel); a probe with no target raises `ValueError`; `StrictModel` rejects malformed input. (4) **Composite production-readiness gate** (`cem_eval/production_readiness.py`): `production_readiness_report(report) -> ReadinessReport` with `ready` **derived** as `all(checks pass)` over the five locked criteria — `mma_passes`, `beats_lexical_by_margin`, `negative_control_suppression==1.0`, `within_latency_budget`, `no_fake_green_ast_clean`. The no-fake-green AST scanner was extracted to a shared `cem_eval/fake_green_guard.py` (single source of truth) and now also policies the gate module itself (self-referential hole closed). **Exam unchanged after wiring: CEM MMA 0.833 (95% CI [0.613, 1.054], n=12), margin 75.0pp, verdict PASS; measured p95 retrieval ≈ 11–13 ms (worst-of-12), within the 50 ms budget.**
- Completed **Phase 3 (action-value retrieval)**. Replaced the bare lexical-overlap scorer (`lexical_overlap_v0`) with the **transparent feature ranker `action_value_v1`** (design §4.1): an auditable additive weighted sum over five features — `precondition_match`, `verified_lift_prior`, `recency_temporal`, `contradiction_penalty`, `staleness_penalty` — plus the preserved normalized lexical floor. `verified_lift_prior` is **hard-gated to 0.0** until a passed probe sets both `card.measured_lift` and `promotion_status="verified"` (never invents a prior from confidence/atom count). `score_card` now returns `(total, breakdown)` and `retrieve_action_brief` persists a per-feature `score_breakdown_by_card` whose `weighted_*` terms sum exactly to each card's `total` (an assertable auditability invariant). `expected_action_delta` is now sourced from the strongest verified selected card's realized lift (`probe_verified`), the confidence proxy (`observational_unverified`), or `none` — never hardcoded; `heldout_eval` stays reserved for the Phase 4 MMA harness. Selection is now **relevance-keyed** (precondition OR lexical OR earned lift), so a penalty never silently drops a relevant card. `retrieve_action_brief(task, *, max_cards)` signature is unchanged.

### Changed

- Fixed the asserted-promotion bug: `promote()` now creates/updates a **candidate** card only and no longer flips the atom or card to `verified`. Verification is a separate, evidence-gated step via `apply_verification_result()`. `audit()` now reports a card's real `promotion_status` instead of a hardcoded `"verified"`.
- **Phase 3 read-path behavior change.** Retrieval now ranks by estimated action value, not word overlap. Two consequent selection-semantics changes (no existing behavioral test asserts numeric scores, so the suite is unaffected): a card with positive net total but **zero relevance** (e.g. pure recency) is now excluded, and a **relevant card driven net-negative by a contradiction penalty is now kept** (relevance-keyed gate, not net-total gate). Pre-registered weight set (the single locked candidate per the spec §10 single-shot rule): `W_PRE=1.0, W_LEX=1.0, W_LIFT=4.0, W_REC=1.0, W_CON=2.0, W_STALE=1.5`; `HALF_LIFE_DAYS=30.0, STALE_WINDOW_DAYS=14.0, CONTRA_SATURATION=2.0`.

### Fixed

- Fixed a `TypeError` in action-brief retrieval on timezone-naive datetimes: `TaskContext.current_time` and `ExperienceCard.valid_from`/`valid_until` now coerce naive values to UTC, so `_card_in_scope` comparisons no longer crash whether the naive value comes from a client-supplied `current_time` or naive card validity bounds (legacy storage / external writes). Closes the standing `current_time` offset-naive/offset-aware follow-up.
- **Adversarial-audit remediation.** Made the two fake-green Correction Capture monitor gates honest: `correction_controller_wired` now evaluates a real falsifiable predicate (controller bound to the active memory root) with a failure canary proving it goes RED when unwired, and the tautological `recent_corrections_recorded` literal-True check was removed (its count folded into the wired check's informational detail). The fake-green allowlist is now empty. Strengthened weak/existence-only tests: vertical-loop counts pinned to exact values, synthetic-eval p95 latency now requires `math.isfinite`, and the tampered-envelope rejection uses `pytest.raises(..., match=...)`. Removed two ghost exports (`trace_body_hash`, `verify_shared_trace_envelope`) from the `cem_core` public surface (kept internal).
- **Phase 4 exam determinism (Phase 5).** `phase4_dataset.EVAL_NOW` was a fixed past instant (`2026-05-29 12:00 UTC`); because the kernel stamps each card's `valid_from` with wall-clock `utc_now()` at promote time, once the wall clock passed that instant every exam-built card was future-dated out of scope (`valid_from > current_time`) → empty briefs → probes could not verify → **MMA silently collapsed to 0.000**. Anchored `EVAL_NOW = utc_now() + timedelta(hours=1)` so exam-built cards are always in scope and the relative recency/staleness deltas stay stable (the exam is deterministic in OUTCOME; the absolute instant enters no score). Reproduces CEM MMA 0.833 / 75pp / PASS. Added a wall-clock-robust regression test (no exam-built card may be `valid_from > EVAL_NOW`).
- **Phase 2 PR review remediation (PR#4).** Three Greptile-flagged fixes: (1) `_matching_card` now skips inactive (superseded/deprecated/quarantined/deactivated) cards, so a re-observed lesson whose title matches a dead card forms a fresh live card instead of being merged into the dead card and rendered permanently unretrievable by `_card_in_scope`. (2) `negative_control_suppression_rate()` now counts a control as suppressed only when its card is actually inactive (was: any status `!= "verified"`), so a freshly planted control whose probe has not run no longer reports a false 1.0 that hides a live hazard; inactive-card check extracted to a shared `_card_is_inactive` predicate. (3) `_supersede_stale_cards` early-exits for non-`invalidation_event` atoms (the only atoms that can populate `superseded_by`), skipping the full `list_atoms()` scan on the common promote path. Each shipped with a failure canary; the negative-control leak canary was rewritten to baseline 1.0 from a genuinely suppressed control rather than the previously-buggy unrun baseline.

### Verification

- **Phase 0:** `python -m pytest` -> 82 passed (21 new Phase 0 tests, including failure canaries for the promotion bug, the audit status, the MMA success bar, the leakage guard, and the no-fake-green guard).
- **Phase 1:** `python -m pytest` -> 91 passed (9 new Phase 1 tests, including failure canaries for untagged action-delta, `close_influence` never verifying a card, and the vertical-loop leakage guard). An independent verifier subagent confirmed real-green, all three canaries bite (break -> fail -> revert -> pass), no ghost code (every new symbol has a real caller), and no Phase 2/3 scope leak (MMA computed not hardcoded; `scorer_version` uniformly `lexical_overlap_v0`).
- `python -m compileall -q packages scripts tests`, `python scripts/run_cem_vertical_loop.py`, `python scripts/run_synthetic_eval.py`, `scripts/session-start-gate.ps1`, and `git diff --check` all clean.
- **Audit remediation:** `python -m pytest` -> 95 passed (2 new correction-controller-gate canaries). The new fake-green failure canary bites (gate goes RED when the controller is unwired); CLI monitor test still green proves the honest gate passes on a healthy seeded root.
- **Phase 2:** `python -m pytest` -> 107 passed (12 new tests across `test_consolidation.py`, `test_verification.py`, and `test_vertical_loop.py`, each consolidation/verification gate paired with a failure canary). `python scripts/run_synthetic_eval.py` clean (false-memory resistance 1.0, contradiction precision/recall 1.0, false-quarantine rate 0.0); `python scripts/run_cem_vertical_loop.py` reports `verified_card_count` 2 and `negative_control_suppression_rate` 1.0. An independent verifier subagent refuted all four Phase 2 claims as SUPPORTED: proved two canaries bite (break -> fail -> revert -> pass) on the grounding guard and suppression-rate gate, grep-confirmed `apply_verification_result` is the only assignment of card `verified` and `scorer_version` stays `lexical_overlap_v0`, and confirmed the real caller chain (`run_vertical_loop` -> `run_probe`/`schedule_probe`; script -> loop). Tree left clean (`git status --short` empty).
- **Phase 2 PR review remediation (PR#4):** `python -m pytest` -> 109 passed (1 new unrun-control failure canary; the leak canary rewritten, not added). Each of the three fixes was driven RED-first: the `_matching_card` canary asserted the re-observed atom merged into the dead card (same `card_id`), the suppression-rate canary asserted a false `1.0 == 0.0`, and the supersession early-exit kept both invalidation and non-invalidation branches green (verified via the existing supersession + re-observation tests). Commits `4ed433b`, `ba9efff`, `d8a5bec`. Greptile re-reviewed at **5/5** (stale re-anchors only); stopped before merge.
- **Phase 3 (action-value retrieval):** `python -m pytest` -> 115 passed (6 ranker tests in `test_action_value_ranker.py`, plus 4 version-string anchors bumped to `action_value_v1`). Canaries proven to bite (break -> fail -> revert -> pass): setting `W_LIFT=0.0` flips the primary canary (the verified high-lift card no longer outranks the lexically-closer unverified card), disabling the `_as_utc` coercion reproduces the offset-naive/-aware `TypeError` on a legacy naive `last_validated_at`, and (after the pre-push review hardening) `W_LIFT=8.0` fails the breakdown test's numeric weight check. `python scripts/run_synthetic_eval.py` clean; `python scripts/run_cem_vertical_loop.py` reports `mma 1.0`, `scorer_version action_value_v1`, `verified_card_count 2`, `negative_control_suppression_rate 1.0`.
- **Phase 4 (MMA + 10-baseline exam):** `python -m pytest` -> 127 passed (11 new: 1 margin-gate boundary in `test_eval_protocol.py` + 10 exam canaries in `test_phase4_exam.py`, incl. a `cem_verified_card_count >= 1` regression guard so the verified-lift prior cannot silently go dark). Canaries cover the leakage gate aborting before any rung, the 10 rungs present with the ceiling excluded from gates, a real (non-hardcoded) no_memory denominator, total negative-control suppression, weights pinned to LEDGER-018, the no-verbatim-task-statement leakage lint, the lexical rung surfacing a trap CEM suppresses, and the margin gate rejecting a no-op (cem==lexical) scorer. `python scripts/run_phase4_exam.py` -> exit 0 (PASS), headline `MMA = 0.833 (95% CI [0.613, 1.054], n=12); lexical MMA = 0.083; margin = 75.0pp`.
- **Phase 3 Greptile review round (PR#5).** First pass 4/5 with two P2 quality findings (retrieval path confirmed correct), both fixed as a behavior-preserving refactor: `_raw_lexical_overlap` is now computed once per card in `retrieve_action_brief` and passed into `score_card` (new optional `raw_lexical` param) instead of being recomputed; and `score_card`'s context-suppressing defaults are documented and locked by a `test_score_card_standalone_defaults_are_context_free` test. Suite -> 116 passed.
- **Phase 3 pre-push review hardening.** An adversarial multi-agent review (5 dimensions -> verify) confirmed 3 minor findings, all fixed before push: (1) the auditability-invariant test was a tautology (re-summed the stored `weighted_*` values) -> rewritten to assert each `weighted_* == weight x raw-feature`, enforce penalty/bonus signs, recompute `total` independently from raw features, and lock `W_LIFT` numerically (now bites a wrong weight). (2) `weighted_lexical` was not reconstructable from the persisted breakdown (the normalization divisor was not stored) -> added `lexical_overlap_norm` to `score_breakdown_by_card`. (3) the staleness `<= 0` branch comment wrongly called itself unreachable -> corrected (it fires at `valid_until == current_time` since `_card_in_scope` uses strict `<`), with a boundary characterization test.
- **Phase 5 (hardening):** `python -m pytest` -> 154 passed (27 new across `test_card_inactive_predicate.py`, `test_fail_closed.py`, `test_production_readiness.py`, `test_eval_protocol.py`, `test_phase4_exam.py`). Canaries proven to bite (break -> fail -> revert): the predicate fix (a deprecated card was clobbered to `superseded` without the shared predicate), the latency operator inversion (`>=` flips the over-budget + boundary tests), the empty-latency-samples fail-closed guard (`DID NOT RAISE` without it), the silent-default store regression (`get_card` returning `None`), and the self-referential-hole closure (a planted `_check('…', True, …)` in `production_readiness.py` now fails the guard). `python scripts/run_phase4_exam.py` -> exit 0 (PASS), headline unchanged + `retrieval p95 = 13.1ms (budget 50ms, within: True)`; `python scripts/run_synthetic_eval.py` clean. An adversarial multi-agent review (4 dimensions -> verify) confirmed 1 finding (a new wall-clock-coupled test assertion inconsistent with the file's anti-flake convention), fixed by deleting it (the deterministic `future_dated` check already bites the regression).

## 2026-05-28

### Added

- Added `CHANGELOG.md` as the canonical human-readable change timeline.
- Added `docs/PROJECT-LEDGER.md` as the deeper engineering ledger for decisions, gaps, mistakes, and verification state.
- Added scoped dashboard/monitor status so AMS records are separated from global Codex behavior records.
- Added explicit current-phase and next-step output to `python scripts/ams.py dashboard` and monitor records.
- Added `python scripts/ams.py startup-brief` as the first Memory Use Controller command with startup status, monitor linkage, evidence ids, scoped retrieval, and bounded output. Its original allow/block status was superseded on 2026-06-09 by allow/degraded memory readiness.
- Wired `scripts/session-start-gate.ps1` through `startup-brief` as a startup memory-readiness warning surface. Its original missing-memory blocking behavior was superseded on 2026-06-09; missing or failed memory now degrades instead of blocking owner-directed work.
- Added `python scripts/ams.py correction ...` as the first Correction Capture Controller surface with live correction classification, affected file/action recording, directive/CEM/ledger routing, resume gate, and event ledgers.
- Added `docs/2026-05-28-ams-v1.3-correction-capture-controller-plan.md` to make live correction capture part of AMS architecture instead of Vol.

### Changed

- Promoted the AMS operating target from "memory exists and can be queried" to "agents must use bounded, auditable retrieval before acting."
- Clarified that startup memory behavior must be action-brief-first and bounded. AMS must not load the full memory corpus into every session.
- Monitor-0 now checks minimum AMS-scoped directives and learned AMS cards instead of trusting total record counts.
- Monitor-0 now checks correction-controller wiring, active resume gates, correction event visibility, and correction directive surfacing.
- Correction resume now updates the stored event status, so `correction list` does not report a cleared event as still blocked.
- The next active phase is now explicit in repo output: `AMS v1.3 Correction Capture Controller`.

### Gap Identified

- Agent behavior was not fully governed by AMS. The system had memory primitives (`brief`, directives, Monitor-0, provenance), but no universal runtime controller forcing agents to retrieve and attach a bounded memory brief before work.
- The first session-start gate was a useful stopgap, but it checked directive presence rather than enforcing the full bounded startup-brief contract.
- AMS still lacked the live correction loop: it validated memories after traces, but did not intercept mistakes while the agent was actively drifting.

### Mistake Logged

- AMS was initially treated too much like a project-local artifact instead of global agent infrastructure.
- Memory loading happened reactively in-session instead of being enforced as a pre-execution control.
- Codex started Vol implementation before the full plan was approved. AMS now treats that class of correction as a first-class capture event.

### Verified

- `python -m pytest` passed.
- `python -m compileall -q packages scripts tests` passed.
- `python scripts/run_synthetic_eval.py` passed with CEM-0 false-memory resistance, contradiction precision/recall, and action-brief pollution still clean.
- `python scripts/ams.py monitor --deep` passed with correction-controller checks.
- `scripts/session-start-gate.ps1` passed after the controller update.

### Next

- Continue the live control layer:
  - wire Correction Capture Controller into live agent runtime hooks beyond the CLI surface;
  - add latency budget enforcement;
  - attach `brief_id`, `monitor_id`, and evidence ids to broader governed agent work;
  - extend controller coverage beyond session-start gating.

## 2026-05-27

### Added

- Implemented AMS v1 usable local memory workflow around CEM-0:
  - `init`;
  - `session`;
  - `remember`;
  - `pin`;
  - `bootstrap-codex`;
  - `brief`;
  - `list`;
  - `audit`;
  - `eval`.
- Implemented AMS v1.1 migration and Monitor-0 operator workflow:
  - curated migration records;
  - monitor records;
  - dashboard summary.
- Added global AMS environment roots:
  - `AMS_ROOT=C:\Users\7amma\.codex\memory\cem`;
  - `CEM_ROOT=C:\Users\7amma\.codex\memory\cem`.
- Added global Codex MCP registration for `ams-memory` in `C:\Users\7amma\.codex\config.toml`.
- Added `scripts/session-start-gate.ps1` as a first enforcement gate for AMS directive availability.

### Verified

- `python scripts/ams.py monitor --deep` passed.
- `python scripts/ams.py dashboard` returned a live global AMS root.
- Cross-project CLI smoke from `C:\Dev\Builds\Playground-and-testing` reached the same AMS root and returned AMS directives.
- `scripts/session-start-gate.ps1` passed with 13 loaded directives.

### Gap Identified

- Codex runtime restart is required before new global MCP registration is active in every session.
- CLI cross-project proof exists, but full in-agent MCP proof after restart remains the true readiness check.

## 2026-05-26

### Completed

- A: Deep technical review of SuperClaude memory MCP - DONE and VERIFIED.
- B: SuperClaude memory v0.3 upgrade spec - DONE and VERIFIED.
- C: Codex memory system design - DONE and VERIFIED.
- D: ACS protocol design - DONE and VERIFIED.

### Verified

- C design reached READY after 3 Codex verification passes.
- D design reached READY after 4 Codex verification passes.

### Locked Rules

- Do not continue from PATCH-FIRST as if it is ready.
- Run strict verification between major sub-projects.
- Do not read or write `C:\Dev\Builds\Waki` from this workspace.
