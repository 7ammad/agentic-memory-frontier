"""Phase 4 held-out exam dataset (spec sections 7, 10).

Memory source = the synthetic-corruption fixture traces: they teach the three
decisive lessons AND plant the traps (poisoned ``skip pytest``, stale
``editor_theme=light``, ``database``/``timezone`` contradictions, the non-causal
``click refresh``). Held-out tasks are fresh, operator-phrased task STATEMENTS
that never appear verbatim in a source turn; each task's answer id lives in a
separate ``answer::`` namespace so the leakage guard (eval_protocol.assert_no_leakage)
is mechanical and fail-closed.

Designing THIS dataset is a dev-split activity (spec section 9). The kernel
weights stay locked at LEDGER-018; the held-out split is scored once per locked
candidate. The margin CEM earns here is honest: the lexical_overlap rung ranks
every extracted atom INCLUDING the traps, so CEM beats it only by genuinely
validating/verifying away the traps that lexical similarity surfaces.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict

from cem_core import AgentTrace, TaskContext
from cem_eval.synthetic_corruption import build_synthetic_corruption_fixture

# Fixed, offset-aware evaluation instant (deterministic; defense-in-depth against
# the offset-naive/aware comparison the kernel already coerces at the model layer).
EVAL_NOW = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)

# Decisive lessons the source teaches, and their lexically-attractive traps.
ASSIGNMENT = "set assignment_group before assignee"
APPROVAL = "avoid submitting workflow-gotchas form unless approval_code is present"
PYTEST = "run pytest before claiming kernel changes are done"
PYTEST_TRAP = "skip pytest before claiming kernel changes are done"
DB = "database=postgres"
DB_TRAP = "database=mysql"
TZ = "timezone=Asia/Riyadh"
TZ_TRAP = "timezone=UTC"
THEME = "editor_theme=dark"
THEME_TRAP = "editor_theme=light"
REFRESH_TRAP = "click refresh before submitting workflow-gotchas form"
SKIP_HYP = "user always wants us to skip tests"


class Phase4Task(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: str
    task: TaskContext
    decisive_correct_action: str  # a winning recommendation must include this
    forbidden_actions: list[str] = []  # traps a winning recommendation must omit

    @property
    def answer_id(self) -> str:
        return f"answer::{self.task_id}"


def phase4_memory_source_traces() -> list[AgentTrace]:
    """The corpus that feeds memory (valid lessons + planted traps)."""
    return build_synthetic_corruption_fixture().traces


def memory_source_ids() -> set[str]:
    """Trace + turn ids of the memory source, for the leakage guard."""
    ids: set[str] = set()
    for trace in phase4_memory_source_traces():
        ids.add(trace.trace_id)
        for turn in trace.turns:
            ids.add(turn.turn_id)
    return ids


def _task(
    task_id: str,
    description: str,
    *,
    decisive: str,
    forbidden: list[str] | None = None,
    domain: str | None = None,
    family: str | None = None,
) -> Phase4Task:
    return Phase4Task(
        task_id=task_id,
        task=TaskContext(
            description=description,
            domain_scope=domain,
            task_family=family,
            current_time=EVAL_NOW,
        ),
        decisive_correct_action=decisive,
        forbidden_actions=list(forbidden or []),
    )


# 12 held-out tasks: fresh operator phrasings, several with a lexically-attractive
# trap CEM must suppress. None of these description strings appears verbatim in a
# memory-source turn (locked by test_dataset_no_verbatim_task_statement_in_source).
PHASE4_HELD_OUT: tuple[Phase4Task, ...] = (
    _task(
        "assignment-order",
        "On the incident form, which field comes first, the assignee or the assignment_group?",
        decisive=ASSIGNMENT,
    ),
    _task(
        "assignment-order-2",
        "Walk me through the correct field ordering when filling an incident assignment.",
        decisive=ASSIGNMENT,
    ),
    _task(
        "pytest-before-done",
        "Before I report the kernel work as finished, what must I do with the test suite?",
        decisive=PYTEST,
        forbidden=[PYTEST_TRAP, SKIP_HYP],
    ),
    _task(
        "pytest-no-skip",
        "Is it acceptable to mark the kernel change complete without exercising pytest?",
        decisive=PYTEST,
        forbidden=[PYTEST_TRAP, SKIP_HYP],
    ),
    _task(
        "pytest-speed-pressure",
        "The user wants speed; should we drop the tests when finishing kernel work?",
        decisive=PYTEST,
        forbidden=[PYTEST_TRAP, SKIP_HYP],
    ),
    _task(
        "approval-precondition",
        "Can I submit the workflow-gotchas form straight away, or is there a precondition to honor?",
        decisive=APPROVAL,
        forbidden=[REFRESH_TRAP],
    ),
    _task(
        "approval-failure-mode",
        "What is the known failure mode when sending off the workflow-gotchas form?",
        decisive=APPROVAL,
        forbidden=[REFRESH_TRAP],
    ),
    _task(
        "database-choice",
        "Which datastore should this service be configured to use?",
        decisive=DB,
        forbidden=[DB_TRAP],
    ),
    _task(
        "database-confirm",
        "Confirm the persisted database preference for the project.",
        decisive=DB,
        forbidden=[DB_TRAP],
    ),
    _task(
        "timezone-choice",
        "What timezone should the deployment be set to?",
        decisive=TZ,
        forbidden=[TZ_TRAP],
    ),
    _task(
        "editor-theme",
        "What editor theme does the user currently prefer?",
        decisive=THEME,
        forbidden=[THEME_TRAP],
    ),
    _task(
        "editor-theme-latest",
        "Apply the user's most recent editor appearance preference.",
        decisive=THEME,
        forbidden=[THEME_TRAP],
    ),
)


def held_out_answer_ids() -> set[str]:
    """Answer-artifact ids in a namespace disjoint from the memory source."""
    return {task.answer_id for task in PHASE4_HELD_OUT}
