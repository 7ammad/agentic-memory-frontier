from cem_core import CEM, InMemoryStore
from cem_core.matching import SituationMatcher
from cem_core.models import BehaviorInvariant, DecisionIntent, SkillCandidate


def _decision(
    proposed_action: str,
    *,
    authority: str = "owner_instruction",
    runtime_surface: str = "codex-desktop",
    approval_state: str = "not_required",
) -> DecisionIntent:
    return DecisionIntent(
        agent_id="codex",
        session_id="session_2",
        task_id="task_2",
        proposed_action=proposed_action,
        action_kind="decision",
        expected_outcome="future action is selected correctly",
        applicable_authority=authority,
        authority_refs=["directive_current"],
        approval_state=approval_state,
        experiment_state="not_experiment",
        runtime_surface=runtime_surface,
        evidence_ids=["directive_current"],
    )


def _invariant() -> BehaviorInvariant:
    return BehaviorInvariant(
        source_attribution_id="attribution_1",
        source_record_id="experience_1",
        authority="owner_instruction",
        scope="global_agent_behavior",
        trigger="equivalent situation match",
        forbidden_repeat="scope general behavior failure as project-specific",
        corrected_action="route general Codex/AMS behavior correction to codex-harness",
        enforcement="steer_or_block",
        evidence_ids=["attribution_1", "directive_1"],
    )


def _skill() -> SkillCandidate:
    return SkillCandidate(
        source_attribution_id="attribution_2",
        source_record_id="experience_2",
        transfer_scope="agent",
        preconditions=["authority_basis=system_instruction", "runtime_surface=codex-desktop"],
        procedure=["run AMS startup brief before implementation"],
        expected_result="memory evidence is loaded before edits",
        failure_boundaries=["do not apply when owner supersedes"],
        evidence_ids=["attribution_2", "trace_2"],
        when_not_to_apply=["missing authority evidence", "different runtime surface"],
    )


def test_situation_matcher_fires_on_exact_invariant_repeat():
    decision = _decision("scope general behavior failure as project-specific")

    matches = SituationMatcher().match_decision(decision, invariants=[_invariant()], skills=[])

    assert len(matches) == 1
    match = matches[0]
    assert match.source_type == "invariant"
    assert match.source_id.startswith("invariant_")
    assert match.match_type == "exact_repeat"
    assert match.fires is True
    assert match.confidence == 1.0
    assert "exact" in match.reason.lower()
    assert "reasoning" not in match.audit_summary()


def test_situation_matcher_fires_on_paraphrased_invariant_repeat():
    decision = _decision(
        "treat the not-Waki AMS correction as a Waki-specific implementation task again"
    )

    match = SituationMatcher().match_decision(decision, invariants=[_invariant()], skills=[])[0]

    assert match.match_type == "paraphrase_repeat"
    assert match.fires is True
    assert match.confidence >= 0.72
    assert "paraphrase" in match.reason.lower()


def test_situation_matcher_suppresses_valid_project_neighbor():
    decision = _decision("answer the Waki project-specific dataset review question")

    match = SituationMatcher().match_decision(decision, invariants=[_invariant()], skills=[])[0]

    assert match.match_type == "valid_neighbor"
    assert match.fires is False
    assert match.confidence >= 0.8
    assert "project-specific" in match.reason


def test_situation_matcher_matches_skill_only_when_preconditions_hold():
    skill = _skill()
    matching_decision = _decision(
        "run AMS startup brief before implementation",
        authority="system_instruction",
        runtime_surface="codex-desktop",
    )
    wrong_surface = _decision(
        "run AMS startup brief before implementation",
        authority="system_instruction",
        runtime_surface="untrusted-chat",
    )

    fired = SituationMatcher().match_decision(matching_decision, invariants=[], skills=[skill])[0]
    suppressed = SituationMatcher().match_decision(wrong_surface, invariants=[], skills=[skill])[0]

    assert fired.source_type == "skill"
    assert fired.match_type == "skill_transfer"
    assert fired.fires is True
    assert suppressed.match_type == "valid_neighbor"
    assert suppressed.fires is False
    assert "precondition" in suppressed.reason.lower()


def test_situation_matcher_does_not_block_owner_approved_changed_context():
    decision = _decision(
        "owner-approved changed context: handle this as a project-specific Waki implementation issue",
        approval_state="owner_approved",
    )

    match = SituationMatcher().match_decision(decision, invariants=[_invariant()], skills=[])[0]

    assert match.match_type == "valid_neighbor"
    assert match.fires is False
    assert "owner-approved" in match.reason


def test_cem_match_situation_reads_and_persists_match_receipts():
    store = InMemoryStore()
    cem = CEM(store=store)
    invariant = _invariant()
    decision = _decision("scope general behavior failure as project-specific")
    store.save_behavior_invariant(invariant)

    matches = cem.match_situation(decision)

    assert len(matches) == 1
    assert matches[0].fires is True
    assert store.get_situation_match(matches[0].match_id) == matches[0]
