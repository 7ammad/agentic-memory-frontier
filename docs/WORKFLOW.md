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
2. **AI review loop to 5/5.** Every PR is reviewed by the repo's AI reviewer, which scores
   confidence out of 5. Address the comments, push, wait for re-review, repeat until **5/5 or
   ~5 turns** — whichever comes first.
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
