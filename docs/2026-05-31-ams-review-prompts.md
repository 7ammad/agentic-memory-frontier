# AMS Review Prompts

Date: 2026-05-31
Purpose: launch independent review lanes for the AMS product-lock reset.

## Greptile PR Review Prompt

Use this in the PR description or review request.

```markdown
Please review this PR as an independent product-scope and implementation-safety review for AMS.

Context:
- Product line is AMS. Older internal labels are historical implementation detail, not product identity.
- `PRODUCT-LOCK.md` is now the canonical product acceptance lock.
- The goal of this PR is to stop scope drift and make AMS completion measurable against Product Lock criteria A1-A9.
- This PR should not be judged as broad engine feature work. It is a scope/acceptance reset plus primary-runtime adoption work: phase-status correction, planning/audit scaffolding, and governed-run receipts for `startup-brief`.
- Live Codex hook smoke now proves payload projection, but also found Codex CLI 0.128.0 command-hook failures are advisory: non-zero `UserPromptSubmit`/`PreToolUse` hooks did not block the turn/tool.

Primary files:
- `PRODUCT-LOCK.md`
- `docs/2026-05-31-ams-product-lock-execution-plan.md`
- `docs/2026-05-31-ams-product-lock-audit.md`
- `docs/2026-05-31-codex-hook-runtime-smoke.md`
- `IDEA.md`
- `TODO.md`
- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/PROJECT-LEDGER.md`
- `packages/cem-core/src/cem_core/local_memory.py`
- `packages/cem-core/src/cem_core/operations.py`
- `packages/cem-core/src/cem_core/correction_capture.py`
- `tests/test_ams_cli.py`

Review questions:
1. Does `PRODUCT-LOCK.md` define a clear, enforceable acceptance bar for AMS?
2. Are the A1-A9 criteria specific enough to prevent fake completion?
3. Does the audit honestly classify current status as pass/partial/fail?
4. Are any claimed "accepted" items unsupported by code or command evidence?
5. Does the phase/dashboard status now reflect the real next work?
6. Is there any remaining product identity drift in active docs?
7. Are there missing acceptance criteria needed for primary runtime adoption?
8. Do tests cover the status behavior changed in `operations.py`?
9. Do governed-run receipts actually make startup work auditable, or can AMS still look primary while being bypassed?
10. Does the live hook smoke correctly prevent a false A6 pass now that Codex command hooks are shown to be advisory?
11. What must be fixed before this PR can be treated as the new product baseline?

Please prioritize bugs, contradictions, false acceptance claims, and missing gates. Be strict about anything that lets AMS look complete while Codex can still ignore it during normal work.
```

## Optional Codex Review Prompt

Use this only as a secondary preflight, not as a substitute for Greptile.

```markdown
You are reviewing the AMS product-lock reset in `C:\Dev\Builds\Agentic Memory System`.

Take a code-review stance. Findings first, ordered by severity. Do not patch.

Scope:
- `PRODUCT-LOCK.md`
- `docs/2026-05-31-ams-product-lock-execution-plan.md`
- `docs/2026-05-31-ams-product-lock-audit.md`
- active SOT docs and phase-status code/tests touched by the PR.

Review for:
- product acceptance criteria that are too vague or fake-greenable;
- places where AMS is claimed complete despite primary runtime adoption being partial;
- active docs that still split the product identity;
- mismatch between `PRODUCT-LOCK.md`, `TODO.md`, dashboard phase status, and `PROJECT-LEDGER.md`;
- false claims that Codex command hooks enforce blocking after the live smoke showed they are advisory in Codex CLI 0.128.0;
- missing tests for changed behavior;
- evidence claims in the audit that are unsupported by repo files or commands.

Return:
1. Findings with file/line references.
2. Open questions.
3. Residual risk.
4. Whether the PR is safe to use as the baseline for continuing AMS build.
```
