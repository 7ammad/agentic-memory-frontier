# AMS V2 Product Lock Audit

Date: 2026-06-10
Source: `PRODUCT-LOCK.md`, `docs/2026-06-10-ams-v2-experience-enforcement-plan.md`,
and `docs/2026-06-10-ams-v2-acceptance-contract.md`
Status: accepted after terminal V2 operator proof

## Summary

AMS V2 is accepted when the system proves verified experience changes future
agent behavior under the hood without trimming valid work. The non-repeat
kernel is not a smaller V1.5 product. It is one subsystem inside the full V2
architecture: decision-intent capture, attribution, invariant and skill
compilation, situation matching, policy binding, reasoning receipts,
supersession, multi-agent governance, context-pollution defense, eval harness,
and fresh-root operator proof.

## Acceptance Matrix

| Criterion | Status | Evidence | Missing Work | Next Step |
|---|---|---|---|---|
| V2-1. Experience Graph | pass | `DecisionIntent` and `ExperienceGraphRecord` capture proposed action, expected outcome, authority, approval/experiment state, runtime surface, and evidence ids; runtime traces persist experience graph records. | None for V2. | Preserve as non-regression evidence. |
| V2-2. Attribution | pass | `ErrorAttributor` and `SuccessAttributor` distinguish mistake, approved experiment failure, acceptable tradeoff, success, and unresolved outcomes; owner-labeled seed tests cover the June 9 Codex/AMS correction and approved experiment exclusion. | None for V2. | Preserve as non-regression evidence. |
| V2-3. Invariants And Skills | pass | `BehaviorInvariantCompiler`, `SkillCompiler`, and `AuthorityScopeResolver` compile confirmed mistakes into scoped invariants and successes into skill candidates with authority-ranked scope. | None for V2. | Preserve as non-regression evidence. |
| V2-4. Situation Matching | pass | `SituationMatcher` catches exact and paraphrased repeats, suppresses valid project neighbors and owner-approved changed contexts, and transfers skills only when preconditions match. | None for V2. | Preserve as non-regression evidence. |
| V2-5. Policy Binding | pass | `RuntimeInterceptionBoundary`, `ActionDecisionPoint`, and `PolicyBindingLayer` return allow, steer, block, override, and degraded receipts before downstream action selection. | None for V2. | Preserve as non-regression evidence. |
| V2-6. Reasoning Control | pass | `ReasoningController` keeps silent steering under the hood, makes blocks visible, rejects silent downgrade, and requires explicit authority for overrides without exposing raw hidden reasoning. | None for V2. | Preserve as non-regression evidence. |
| V2-7. Supersession | pass | `SupersessionLedger` supersedes, reverses, and records owner overrides; active filtering prevents superseded invariants from firing. | None for V2. | Preserve as non-regression evidence. |
| V2-8. Multi-Agent Governance | pass | `SharedExperienceEnvelope` and `MultiAgentGovernanceLayer` preserve writer/recipient identity, authority, visibility, ownership, scope, provenance, and conflict receipts; project-specific lessons and low-authority context cannot become global action control. | None for V2. | Preserve as non-regression evidence. |
| V2-9. Eval Harness | pass | `scripts/run_ams_v2_eval.py --root tmp\ams-v2-eval-phase9-smoke` returns `AMS_V2_EVAL_PASS`, 13/13 cases passed, false_blocks=0/0 across NonRepeatEval, FalseBlockEval, ApprovedExperimentEval, SkillTransferEval, SupersessionEval, MultiAgentConflictEval, and ContextPollutionEval. | None for V2. | Preserve as release evidence. |
| V2-10. Operator Proof | pass | `scripts/run_ams_v2_operator_proof.py` composes the fresh-root v1 operator path with the V2 eval harness and asserts `AMS V2 Accepted`, ready=true, no open follow-ups, complete executed seed coverage, and false-block budget adherence. The proof writes `v2-operator-proof-latest.json` and enumerates the V1 operator root, V2 eval receipt, Phase 4 frontier root, and monitor artifact. | None for V2. | Preserve as terminal release evidence. |

## Blocking Acceptance Battery

The V2 eval harness covers all acceptance ids:

- V2-SEED-001 confirmed mistake replay;
- V2-SEED-002 paraphrased repeat replay;
- V2-SEED-003 valid neighbor / false-block budget;
- V2-SEED-004 approved experiment exclusion;
- V2-SEED-005 authority precedence;
- V2-SEED-006 silent steering;
- V2-SEED-007 block receipt;
- V2-SEED-008 downgrade receipt;
- V2-SEED-009 skill transfer;
- V2-SEED-010 skill boundary;
- V2-SEED-011 supersession;
- V2-SEED-012 multi-agent scope;
- V2-SEED-013 context pollution.

## Terminal Proof

Terminal command:

```powershell
python scripts/run_ams_v2_operator_proof.py --root tmp\ams-v2-operator-proof-final
```

Expected terminal signal:

```text
AMS_V2_OPERATOR_PROOF_PASS
v2_eval=PASS 13/13 false_blocks=0/0
phase=AMS V2 Accepted ready=True
```

## Residual Risk

V2 is accepted as a deterministic local product proof. Future work can improve
model-backed semantic matching, broader external benchmark coverage, richer UI,
and hosted/distributed packaging, but those are post-V2 improvements and must
not reopen or shrink the V2 acceptance bar.
