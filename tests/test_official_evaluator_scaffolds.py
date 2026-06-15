from cem_eval import official_evaluator_scaffold


def test_official_evaluator_scaffolds_pin_bounded_smoke_evidence():
    for suite_name in (
        "halumem_cem0",
        "memoryarena_cem0",
        "longmemeval_v2_cem0",
    ):
        scaffold = official_evaluator_scaffold(suite_name)

        assert scaffold.status == "official_bounded_smoke_passed"
        assert scaffold.setup_commands
        assert scaffold.bounded_smoke_command
        assert scaffold.full_run_command
        assert scaffold.smoke_evidence_path.startswith("tmp\\")
        assert scaffold.resource_note
        assert "not an official CEM leaderboard score" in scaffold.remaining_note
