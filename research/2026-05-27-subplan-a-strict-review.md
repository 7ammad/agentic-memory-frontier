# Codex Strict-Review - Subplan A

**Date:** 2026-05-27
**Scope:** A only - SC memory deep review v3 research artifact.
**Result:** `PATCH-FIRST`

## Check 1 Coverage

- SC architecture: PASS for design-review coverage. v1/v2 cover storage, schema, embedding, search modes, dedup, lifecycle, session load, transports, tools, concurrency, and bridge. v3 is a synthesis, not the standalone architecture manifest.
- Comparator systems: PASS. v1/v2 include the comparator matrix and source-tier framing.
- MIT-12 grounding: PASS. v2 applies the MIT-12 protocol; v3 adds five more MIT-12 query groups and corrects the "out of corpus" overclaim.
- Codex counsel: PASS. v3 integrates `codex-counsel-output.md` and accepts its pushback on Dec-POMDP overclaiming and migration risk.
- Final backlog: PASS. v3 has an ordered backlog.
- Migration/rollback implications: PASS after prior patch. v3 adds the missing migration playbook and snapshot-only rollback.
- Source manifest: PASS with caveat. v3's manifest is explicitly v3-only and points back to v2 as the full source manifest.

## Check 2 Internal Consistency

- FAIL: v3 still used old subproject labels: "sub-project B (Codex memory)" and "sub-project C (ACS)" even though current labels are B = SC v0.3, C = Codex memory, D = ACS.
- FAIL: project bootstrap docs disagreed on `.Codex` vs `.claude`. `AGENTS.md` pointed to `C:\Users\7amma\.Codex\...`, while `CLAUDE.md` and the session handoffs pointed to `C:\Users\7amma\.claude\...`.
- WARN: root docs said "No implementation has started" as a 2026-05-26 state. That was historical, but stale for resuming after the 2026-05-27 implementation session.
- WARN: v1/v2 contain old labels and historical baseline claims. Acceptable only if patched or caveated.

## Check 3 Grounding

Codex CLI could not complete direct source spot-checking because its read sandbox blocked `C:\Users\7amma\.claude\mcp-servers\superclaude-memory\src\*.ts`. The direct source spot-check was completed separately in `research/2026-05-27-subplan-a-review.md`.

## Check 4 Missing Artifacts

- Missing A erratum/current-state repair note.
- Missing current label map in A.
- Missing path reconciliation.
- Missing root-doc freshness note.
- Missing current source spot-check artifact.

## Patches Needed

1. Patch v3 downstream labels to current B/C/D.
2. Add a subplan A erratum or review artifact noting that A code facts are historical baseline facts as of 2026-05-26.
3. Reconcile `.Codex` vs `.claude` paths.
4. Add current-state note to root docs.
5. Add current source spot-check result.

## Readiness Verdict

`PATCH-FIRST`.

Follow-up repair was applied in this session; see `research/2026-05-27-subplan-a-review.md`.
