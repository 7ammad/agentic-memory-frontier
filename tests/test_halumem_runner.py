import json

from cem_eval import run_halumem_cem0_eval


def test_halumem_cem0_runner_scores_proposed_and_trusted_write_path(tmp_path):
    dataset_path = tmp_path / "halumem_runner_sample.json"
    dataset_path.write_text(json.dumps([_halumem_runner_record()]), encoding="utf-8")

    result = run_halumem_cem0_eval(dataset_path, tmp_path / "cem")

    assert result.suite_name == "halumem_cem0"
    assert result.session_count == 2
    assert result.proposed_count == 4
    assert result.trusted_count == 2
    assert result.quarantined_count == 1
    assert result.proposed_score.reference_memory_count == 3
    assert result.proposed_score.candidate_memory_count == 4
    assert result.proposed_score.matched_memory_count == 3
    assert result.proposed_score.hallucinated_memory_count == 1
    assert result.proposed_score.omitted_memory_count == 0
    assert result.proposed_score.extraction_precision == 0.75
    assert result.proposed_score.extraction_recall == 1.0
    assert result.trusted_score.candidate_memory_count == 2
    assert result.trusted_score.hallucinated_memory_count == 0
    assert result.trusted_score.omitted_memory_count == 1
    assert round(result.trusted_score.extraction_recall, 3) == 0.667
    assert result.trusted_score.update_recall == 1.0
    assert result.trusted_score.qa_evidence_recall == 1.0
    assert "assistant_hypothesis" in result.decision_reason_codes["user wants us to skip tests"]


def _halumem_runner_record():
    return {
        "uuid": "runner-user",
        "sessions": [
            {
                "session_id": "initial",
                "dialogue": [
                    {
                        "role": "user",
                        "content": (
                            "PREFERENCE: database=postgres\n"
                            "PREFERENCE: editor_theme=light\n"
                            "HYPOTHESIS: user wants us to skip tests"
                        ),
                        "dialogue_turn": 0,
                    }
                ],
                "memory_points": [
                    {
                        "index": 1,
                        "memory_content": "database=postgres",
                        "memory_source": "primary",
                        "is_update": False,
                    },
                    {
                        "index": 2,
                        "memory_content": "editor_theme=light",
                        "memory_source": "primary",
                        "is_update": False,
                    },
                ],
                "questions": [
                    {
                        "question": "Which database should be used?",
                        "answer": "postgres",
                        "evidence": [{"memory_content": "database=postgres"}],
                    }
                ],
            },
            {
                "session_id": "update",
                "dialogue": [
                    {
                        "role": "user",
                        "content": "UPDATE: editor_theme=dark",
                        "dialogue_turn": 0,
                    }
                ],
                "memory_points": [
                    {
                        "index": 3,
                        "memory_content": "editor_theme=dark",
                        "memory_source": "primary",
                        "is_update": True,
                        "original_memories": ["editor_theme=light"],
                    }
                ],
                "questions": [],
            },
        ],
    }
