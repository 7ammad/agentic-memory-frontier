import json

from cem_eval import (
    halumem_sessions_to_agent_traces,
    load_halumem_dataset,
    score_halumem_extraction,
    score_halumem_reference_upper_bound,
    summarize_halumem_dataset,
)


def test_halumem_adapter_loads_official_user_session_shape(tmp_path):
    dataset_path = tmp_path / "halumem_sample.json"
    dataset_path.write_text(json.dumps([_halumem_user_record()]), encoding="utf-8")

    dataset = load_halumem_dataset(dataset_path)
    summary = summarize_halumem_dataset(dataset_path)
    traces = halumem_sessions_to_agent_traces(dataset)

    assert summary.user_count == 1
    assert summary.session_count == 2
    assert summary.dialogue_turn_count == 4
    assert summary.memory_point_count == 4
    assert summary.update_memory_point_count == 1
    assert summary.qa_pair_count == 1
    assert summary.primary_memory_point_count == 3
    assert summary.interference_memory_point_count == 1
    assert [session.session_id for session in dataset.sessions] == [
        "career-shift",
        "career-update",
    ]
    assert dataset.sessions[1].memory_points[0].is_update is True
    assert dataset.sessions[1].memory_points[0].original_memories == [
        "Martin is considering a career change due to mental health."
    ]
    assert dataset.questions[0].evidence_memory_contents == [
        "Martin is considering a career change due to mental health."
    ]
    assert len(traces) == 2
    assert traces[0].trace_id == "halumem-career-shift"
    assert traces[0].agent_id == "halumem-source"
    assert traces[0].environment["domain"] == "halumem"
    assert traces[0].turns[0].role == "user"
    assert traces[0].turns[1].role == "assistant"


def test_halumem_adapter_scores_candidate_memories(tmp_path):
    dataset_path = tmp_path / "halumem_sample.json"
    dataset_path.write_text(json.dumps([_halumem_user_record()]), encoding="utf-8")
    dataset = load_halumem_dataset(dataset_path)

    score = score_halumem_extraction(
        dataset,
        {
            "career-shift": [
                "Martin is considering a career change due to mental health.",
                "Martin secretly moved to Berlin.",
            ],
            "career-update": [
                "Martin now plans to move into healthcare operations.",
            ],
        },
    )

    assert score.reference_memory_count == 4
    assert score.candidate_memory_count == 3
    assert score.matched_memory_count == 2
    assert score.hallucinated_memory_count == 1
    assert score.omitted_memory_count == 2
    assert round(score.extraction_precision, 3) == 0.667
    assert score.extraction_recall == 0.5
    assert round(score.extraction_f1, 3) == 0.571
    assert score.update_recall == 1.0
    assert score.qa_evidence_recall == 1.0


def test_halumem_reference_upper_bound_scores_clean(tmp_path):
    dataset_path = tmp_path / "halumem_sample.jsonl"
    dataset_path.write_text(json.dumps(_halumem_user_record()) + "\n", encoding="utf-8")
    dataset = load_halumem_dataset(dataset_path)

    score = score_halumem_reference_upper_bound(dataset)

    assert score.reference_memory_count == 4
    assert score.candidate_memory_count == 4
    assert score.hallucinated_memory_count == 0
    assert score.omitted_memory_count == 0
    assert score.extraction_precision == 1.0
    assert score.extraction_recall == 1.0
    assert score.extraction_f1 == 1.0
    assert score.update_recall == 1.0
    assert score.qa_evidence_recall == 1.0


def _halumem_user_record():
    return {
        "uuid": "martin-user",
        "persona_info": {"name": "Martin"},
        "sessions": [
            {
                "session_id": "career-shift",
                "start_time": "Dec 15, 2025, 06:11:23",
                "end_time": "Dec 15, 2025, 06:20:23",
                "dialogue_token_length": 120,
                "dialogue": [
                    {
                        "role": "user",
                        "content": "I need a career change because this role is hurting my health.",
                        "timestamp": "Dec 15, 2025, 06:11:23",
                        "dialogue_turn": 0,
                    },
                    {
                        "role": "assistant",
                        "content": "A career change may help if the current role affects your health.",
                        "timestamp": "Dec 15, 2025, 06:12:23",
                        "dialogue_turn": 1,
                    },
                ],
                "memory_points": [
                    {
                        "index": 1,
                        "memory_content": "Martin is considering a career change due to mental health.",
                        "memory_type": "Event Memory",
                        "memory_source": "primary",
                        "is_update": "False",
                        "importance": 0.8,
                        "timestamp": "Dec 15, 2025, 06:12:23",
                    },
                    {
                        "index": 2,
                        "memory_content": "Martin prefers low-impact hiking on weekends.",
                        "memory_type": "Persona Memory",
                        "memory_source": "primary",
                        "is_update": False,
                        "importance": 0.4,
                    },
                ],
                "questions": [
                    {
                        "question": "Why is Martin considering a career change?",
                        "answer": "Because of mental health effects.",
                        "evidence": [
                            {
                                "memory_content": "Martin is considering a career change due to mental health.",
                                "memory_type": "Event Memory",
                            }
                        ],
                        "difficulty": "easy",
                        "question_type": "Basic Fact Recall",
                    }
                ],
            },
            {
                "session_id": "career-update",
                "start_time": "2026-01-10T08:00:00+00:00",
                "dialogue": [
                    {
                        "role": "user",
                        "content": "I now want to move into healthcare operations.",
                        "timestamp": "2026-01-10T08:00:00+00:00",
                        "dialogue_turn": 0,
                    },
                    {
                        "role": "assistant",
                        "content": "Healthcare operations is a clearer target.",
                        "timestamp": "2026-01-10T08:01:00+00:00",
                        "dialogue_turn": 1,
                    },
                ],
                "memory_points": [
                    {
                        "index": 3,
                        "memory_content": "Martin now plans to move into healthcare operations.",
                        "memory_type": "Event Memory",
                        "memory_source": "primary",
                        "is_update": "True",
                        "original_memories": [
                            "Martin is considering a career change due to mental health."
                        ],
                        "importance": 0.9,
                        "timestamp": "2026-01-10T08:01:00+00:00",
                    },
                    {
                        "index": 4,
                        "memory_content": "A distractor says Martin works in astronomy.",
                        "memory_type": "Event Memory",
                        "memory_source": "interference",
                        "is_update": False,
                    },
                ],
                "questions": [],
            },
        ],
    }
