# AMS V2 Review Prompts

Date: 2026-06-10
Purpose: independent review lanes for the AMS V2 release lock.

## Codex Review Prompt

```markdown
You are reviewing AMS V2 in `C:\Dev\Builds\Agentic Memory System`.

Take a code-review stance. Findings first, ordered by severity. Do not patch.

Scope:
- `PRODUCT-LOCK.md`
- `docs/2026-06-10-ams-v2-experience-enforcement-plan.md`
- `docs/2026-06-10-ams-v2-acceptance-contract.md`
- `docs/2026-06-10-ams-v2-product-lock-audit.md`
- `scripts/run_ams_v2_operator_proof.py`
- `scripts/run_ams_v2_eval.py`
- `packages/cem-eval/src/cem_eval/v2_eval_harness.py`
- V2 core surfaces in `packages/cem-core/src/cem_core/`
- `tests/test_ams_v2_operator_proof.py`
- `tests/test_v2_eval_harness.py`
- active phase status in `packages/cem-core/src/cem_core/operations.py`
- active docs: `TODO.md`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, `docs/PROJECT-LEDGER.md`

Review for:
- V2 acceptance claims unsupported by code, commands, or receipts;
- seed battery gaps where a listed V2 acceptance criterion is not actually exercised;
- false-green operator proof paths that can pass without the V2 eval harness, fresh-root v1 path, or final phase status;
- places where a low-authority or project-specific lesson can still become global action control;
- false-block behavior hidden by weak assertions;
- accidental V1.5/downgrade framing or scope trimming;
- mismatch between `PRODUCT-LOCK.md`, `TODO.md`, monitor/dashboard phase status, audit docs, and tests;
- missing tests around final accepted status or the one-command V2 proof.

Return:
1. Findings with file/line references.
2. Open questions.
3. Residual risk.
4. Whether AMS V2 is safe to treat as accepted after the terminal proof.
```

## External PR Review Prompt

```markdown
Please review this PR as the AMS V2 release-lock review.

V2 is not a V1.5 downgrade. The non-repeat kernel is one subsystem inside the
full experience-enforcement architecture. The release claim is valid only if
the fresh-root V2 operator proof, V2 eval harness, product lock, audit docs,
and phase status all agree.

Primary evidence:
- `python scripts/run_ams_v2_operator_proof.py --root tmp\ams-v2-operator-proof-final`
- `python scripts/run_ams_v2_eval.py --root tmp\ams-v2-eval-phase9-smoke`
- `python -m pytest`
- `python scripts/ams.py monitor --json`

Please prioritize anything that lets AMS claim V2 accepted while:
- known mistakes can repeat;
- valid neighbors are blocked;
- approved experiments become mistakes;
- skills transfer without preconditions;
- superseded rules still fire;
- project-specific or low-authority context becomes global action control;
- the proof does not run from a fresh root;
- receipts are missing or too weak to support the claim.
```
