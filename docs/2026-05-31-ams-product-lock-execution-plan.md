# AMS Product Lock Execution Plan

Date: 2026-05-31
Source: `PRODUCT-LOCK.md`

## Rule

AMS is the product. This plan exists only to satisfy the product lock. It does
not redefine scope.

## Planning Target

Move AMS from a working memory engine plus callable tools into the primary
memory operating path for Codex.

## Current Planning Read

Accepted as built:

- write-path validation and quarantine;
- durable typed memory records;
- action-brief retrieval;
- verification probes and baseline evals;
- local CLI, monitor, dashboard, startup gate, and MCP bridge;
- correction capture core and hook wrappers.

Not accepted yet:

- primary Codex runtime lock;
- governed-run receipts on every serious run;
- live hook payload proof in the real Codex runtime;
- continuous trace intake from ordinary Codex work;
- aging and maintenance product surface;
- fresh operator setup proof.

## Execution Order

### Step 1. Product-Lock Audit

Create an acceptance matrix for `PRODUCT-LOCK.md` criteria A1-A9.

For each criterion, record:

- status: pass, partial, fail;
- evidence file/command;
- missing work;
- first implementation command or file to open.

Output:

- `docs/2026-05-31-ams-product-lock-audit.md`

### Step 2. Primary Runtime Lock

Make AMS the default governed startup path.

Work:

- inspect Codex hook/config surfaces available on this machine;
- decide where the AMS startup gate must run;
- ensure startup emits `brief_id`, `monitor_id`, evidence ids, and block status;
- ensure legacy memory surfaces are treated as secondary inputs.

Acceptance:

- a fresh Codex session proves it started through AMS;
- missing required AMS memory blocks serious work;
- dashboard shows the latest allowed startup brief.

### Step 3. Governed-Run Receipts

Every serious run needs an auditable AMS receipt.

Work:

- define the governed-run record shape;
- write the record at run start;
- attach `brief_id`, `monitor_id`, evidence ids, cwd, task summary, and outcome;
- expose latest governed-run state in dashboard/monitor output.

Acceptance:

- a normal run has a durable receipt;
- the receipt links to the startup brief and memory evidence;
- tests prove a missing receipt is visible.

### Step 4. Live Correction Hook Proof

Prove correction hooks against the real Codex payloads.

Work:

- capture a benign prompt payload shape;
- capture a correction prompt payload shape;
- verify `scripts/correction-hook-prompt.ps1` maps prompt/session fields correctly;
- verify `scripts/correction-hook-gate.ps1` blocks while the resume gate is armed.

Acceptance:

- benign prompt returns allow with no side effects;
- correction prompt records event and blocks;
- pre-tool gate blocks until explicit resume.

### Step 5. Real Trace Intake

Stop relying on manual memory writes for normal agent work.

Work:

- define trace event schema for Codex runs;
- emit trace events during real work;
- ingest trace into AMS root;
- propose memory candidates from trace evidence.

Acceptance:

- a normal Codex run creates a trace;
- source spans link memory candidates back to trace evidence;
- false or unsupported trace-derived candidates quarantine.

### Step 6. Influence Closure

Close the loop after work finishes.

Work:

- record whether the action brief was followed;
- record outcome and failure/success signal;
- link outcome to the brief and governed-run receipt;
- keep observed outcome separate from verified lift.

Acceptance:

- a completed run has an influence record;
- audit can show which memory affected the action;
- reports do not overclaim causal lift from observation alone.

### Step 7. Aging And Maintenance

Make memory freshness a product surface.

Work:

- list stale, contradicted, expired, or low-confidence records;
- expose maintenance risk in monitor output;
- add a review/repair command;
- ensure retrieval excludes inactive records.

Acceptance:

- monitor reports memory aging risks;
- review command lists records requiring action;
- tests prove stale records do not leak into action briefs.

### Step 8. Operator Setup Proof

Make AMS usable outside this one working directory.

Work:

- write fresh setup path;
- run setup in an isolated root;
- retrieve a brief;
- audit a memory;
- run monitor.

Acceptance:

- a new local root can initialize and pass health checks;
- setup docs match the actual commands;
- no hidden state from this repo is required.

## Next File To Create

`docs/2026-05-31-ams-product-lock-audit.md`
