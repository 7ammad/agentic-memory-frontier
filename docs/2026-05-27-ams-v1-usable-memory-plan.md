# AMS v1 Usable Memory Plan

Date: 2026-05-27

Status: implementation-approved

## Goal

Build the first usable local Agentic Memory System for Codex.

CEM-0 remains the write-path validation engine, but the user-facing artifact must be a runnable memory workflow:

```text
capture operational experience -> validate before trust -> store locally -> retrieve action brief before action -> audit provenance
```

## Grounding

MIT-12 architecture packet emphasized that trustworthy ML systems need explainability as a system-wide concern, data lifecycle management, provenance, and local/privacy-aware retention. Applied here:

- memory must be auditable, not just retrievable;
- explicit directives must not be laundered as learned experience;
- local persistence and session continuity matter before broad platform integrations;
- the first usable artifact should connect the end-to-end workflow, not only expose a kernel.

Claude Opus 4.7 reviewed the first plan and returned `PATCH-FIRST`. Accepted patches:

- keep explicit directives separate from CEM Experience Cards;
- require `--outcome` for learned memories;
- add current-session discipline instead of making users pass session ids every time;
- default the root to `~/.codex/memory/cem`;
- defer raw trace import until the public schema is documented;
- make bootstrap idempotent and directive-only.

## Build Scope

Add a local CLI entry point:

```powershell
python scripts/ams.py <command>
```

Default root:

```text
~/.codex/memory/cem
```

Environment override:

```text
AMS_ROOT
```

## Commands

### `init`

Initialize storage, config, current session, and directive file.

### `session current`

Print the current session id.

### `session new`

Rotate to a new session id.

### `remember`

Write learned operational experience through CEM validation.

Required:

- `CONTENT`
- `--kind`
- `--outcome`

Supported kinds:

- `fact`
- `preference`
- `instruction`
- `skill`
- `failure`
- `hypothesis`

`remember` creates a CEM `AgentTrace`, proposes atoms, validates them, promotes allowed atoms, and reports quarantined atoms with reason codes.

### `pin`

Store an explicit directive separately from learned experience.

Use this for rules like:

- never read/write Waki;
- do not claim state-of-the-art;
- run verification before completion claims.

Pinned directives appear in action briefs but are audited as directives, not CEM experience.

### `bootstrap-codex`

Idempotently pin the first Codex directives for this workspace, attributed to explicit project docs.

It does not create CEM Experience Cards.

### `brief`

Return a task-scoped action brief with:

- pinned directives;
- verified CEM recommendations;
- preconditions;
- evidence ids;
- confidence.

### `list`

List cards, atoms, or directives.

### `audit`

Audit one card, atom, or directive.

### `eval`

Run the existing synthetic corruption eval.

## Acceptance Tests

- `init` creates a persistent root and current session.
- `remember --outcome success` promotes a supported skill into a card.
- `remember --kind hypothesis --outcome unknown` quarantines hypothesis-only memory.
- `brief` retrieves a trusted action across separate subprocess invocations.
- `pin` stores a directive and `brief` returns it without creating a CEM card.
- `bootstrap-codex` is idempotent and returns Waki/test/TODO guardrails in briefs.
- `audit` explains both CEM cards/atoms and directives.
- root isolation works across two roots.
- JSON output works for scripting.

## Non-Scope

- no ACS relay;
- no dashboard;
- no LanceDB twin;
- no broad database/platform work;
- no state-of-the-art claims;
- no raw trace import until the trace schema is documented for users.
