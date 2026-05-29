# Development Workflow

How feature work moves through this repo. Adapted from the minimal-PR + AI-review-loop
workflow (Ras Mic, *My Agentic Engineering Workflow*) and layered on top of the existing
local discipline in `CLAUDE.md` (session-start gate, CHANGELOG/LEDGER, TODO, verify-before-done).

## Branch model

```text
feature branch  ->  PR  ->  staging  ->  (periodic PR)  ->  main
```

- **`main`** — production / source of truth. Only reached via a reviewed `staging -> main` PR.
- **`staging`** — soak branch. Features land here first and are exercised before promotion.
- **feature branches** — one focused change each, branched off `staging`.

## The rules that make review work

1. **Minimal, focused PRs.** One review surface per PR. Big PRs (>~800-1000 lines) degrade
   AI review quality — split them into stacked PRs where later pieces depend on earlier ones.
2. **AI review loop to 5/5.** Every PR is reviewed by the repo's AI reviewer (**Greptile**),
   which posts a confidence score out of 5. Address the comments, push, wait for re-review,
   repeat until **5/5 or ~5 turns** — whichever comes first.
3. **Know when to stop.** If the score cycles stuck at 4/5, or the loop hits its turn cap,
   stop the agent, review by hand, and merge deliberately. Don't let it keep editing — that's
   where it starts hallucinating.
4. **Human verification every slice.** A green review is not proof the feature works. Run the
   real checks before merging: `python -m pytest` plus the relevant smoke command
   (`python scripts/run_synthetic_eval.py`, `python scripts/run_cem_vertical_loop.py`, etc.).
5. **No fake-green.** Every gate ships a failure canary (a test that injects a known-bad
   condition and asserts the gate fails). A gate that cannot fail is not a gate.

## Commands

```powershell
git checkout -b <type>/<short-name> staging   # branch a focused change off staging
# ... build + test ...
git push -u origin <type>/<short-name>
gh pr create --base staging --fill            # open the PR; the AI reviewer fires on push
gh pr view --json reviews,comments            # read the review + confidence score
# address comments -> commit -> push -> re-review, until 5/5 or the turn cap
```

The review-loop is mechanized as a reusable skill (see the global `review-loop` skill);
this doc is the human-readable contract it follows.

## HARDGATE — autonomous build loop (CEM-1 completion)

**Binding for the remaining CEM-1 build (`TODO.md` Phases 3-5). Not optional, not reducible to an MVP.**

1. **One self-driving session, self-paced.** Drive `TODO.md` autonomously: take the next unchecked
   item -> build it -> verify it -> commit it -> continue. Never stop at "task complete" while an
   unchecked item is clear. Do **not** fan the build out across many manual sessions. Self-pace
   across unavoidable external waits (e.g. a Greptile re-review) with the `/loop` dynamic-mode
   engine: the `ScheduleWakeup` tool re-fires the loop when there is genuinely nothing to do until
   an external state changes. Pass the build task forward each wake; omit the call to end the loop.
   Do not sleep-poll harness-tracked work.
2. **Full build — no MVP, no distillation, no stubs.** Every component ships complete: a real
   (grep-provable) non-test caller, real persisted state, real tests, and a failure canary proven to
   bite (break -> fail -> revert -> pass). TDD (RED -> GREEN -> REFACTOR) for all code.
   `python -m pytest` green before any "done" claim.
3. **Every slice rides the Greptile PR loop above.** Each slice ships as a minimal single-surface PR
   to `staging` and runs the 5/5 review loop (rules 1-5 above). A 5/5 review never replaces human
   verification.
4. **The agent stops before merge.** Merging to `staging` or `main` is the human's call. Drive to
   5/5 (or the stop rule), then hand off — never merge autonomously.
