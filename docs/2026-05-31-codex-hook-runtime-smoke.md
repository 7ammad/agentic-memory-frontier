# Codex Hook Runtime Smoke

Date: 2026-05-31
Runtime: Codex CLI 0.128.0 on Windows
Workspace: `C:\Dev\Builds\Agentic Memory System`

## Purpose

Confirm the real Codex hook payload and whether the AMS correction hook wrappers
can enforce correction blocking in the live Codex runtime.

## Official Contract Checked

OpenAI's Codex config reference says lifecycle hooks are configured through
`hooks.json` or inline `[hooks]`, and names events including
`UserPromptSubmit` and `PreToolUse`. It also says command hooks are currently
supported and `commandWindows` is the Windows override.

Local runtime note: `codex features list` reports `codex_hooks` as the active
stable feature. This local 0.128.0 build warns that `features.hooks` is unknown,
even though the current docs name `features.hooks` and describe
`features.codex_hooks` as the older alias.

## Smoke Results

### 1. UserPromptSubmit Payload Shape

The live Codex `UserPromptSubmit` payload contains these keys:

```json
{
  "session_id": "019e7d48-f0b9-7a60-8d1a-03ec4b4a62de",
  "turn_id": "019e7d48-f3a0-7ee3-b72a-8aafe7e8f603",
  "transcript_path": null,
  "cwd": "C:\\Dev\\Builds\\Agentic Memory System",
  "hook_event_name": "UserPromptSubmit",
  "model": "gpt-5.5",
  "permission_mode": "bypassPermissions",
  "prompt": "Reply with exactly AMS_HOOK_SMOKE_READY."
}
```

Conclusion: `scripts/correction-hook-prompt.ps1` maps the live Codex `prompt`
and `session_id` fields correctly.

### 2. Benign Prompt Through AMS Wrapper

Command shape:

```powershell
codex exec -C "C:\Dev\Builds\Agentic Memory System" --ephemeral --enable codex_hooks `
  -c "hooks.UserPromptSubmit=<temp command hook invoking scripts/correction-hook-prompt.ps1>" `
  "Reply with exactly AMS_BENIGN_HOOK_READY."
```

Observed:

- Codex invoked `UserPromptSubmit`.
- AMS wrapper returned allow.
- Codex completed with exit code 0.
- Temp AMS root had no `correction-events.jsonl`.
- Temp AMS root gate was `clear`.

### 3. Correction Prompt Through AMS Wrapper

Command shape:

```powershell
codex exec -C "C:\Dev\Builds\Agentic Memory System" --ephemeral --enable codex_hooks `
  -c "hooks.UserPromptSubmit=<temp command hook invoking scripts/correction-hook-prompt.ps1>" `
  "we already said no scaffolding; stop and record this correction"
```

Observed:

- Codex invoked `UserPromptSubmit`.
- AMS wrapper captured a correction event in the temp AMS root.
- The captured event preserved the Codex `session_id`.
- Temp AMS root gate became `blocked`.
- Codex printed `hook: UserPromptSubmit Failed`.
- Codex still continued the turn and exited 0.

Conclusion: the payload projection is verified, but Codex CLI 0.128.0 does not
treat a non-zero `UserPromptSubmit` command-hook exit as a blocking decision.

### 4. PreToolUse Gate Through AMS Wrapper

Setup: a temp AMS root was pre-armed with a correction gate, then Codex was run
with `PreToolUse` pointing at `scripts/correction-hook-gate.ps1`.

Command shape:

```powershell
codex exec -C "C:\Dev\Builds\Agentic Memory System" --ephemeral --enable codex_hooks `
  -c "hooks.PreToolUse=<temp command hook invoking scripts/correction-hook-gate.ps1>" `
  "Run the shell command pwd, then reply with the result."
```

Observed:

- Codex invoked `PreToolUse`.
- AMS wrapper returned gate-blocked.
- Codex printed `hook: PreToolUse Failed`.
- Codex still ran `pwd` successfully and exited 0.

Conclusion: Codex CLI 0.128.0 command hooks are advisory for this use case. They
can record correction state, but they do not enforce the "no continuation until
explicit approval" product requirement.

## Product Impact

Verified:

- live Codex `UserPromptSubmit` payload shape;
- prompt/session projection in `scripts/correction-hook-prompt.ps1`;
- wrapper capture side effects in an isolated AMS root;
- Codex invokes `PreToolUse` before tool execution.

Not verified as acceptable:

- Codex blocking on `UserPromptSubmit` correction capture;
- Codex blocking on `PreToolUse` while the resume gate is armed.

AMS A6 remains partial until the runtime path is enforceable. The next product
step is to replace the Codex command-hook exit-code assumption with an
enforceable AMS runtime control path.
