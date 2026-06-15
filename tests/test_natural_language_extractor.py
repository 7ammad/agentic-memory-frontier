from cem_core import AgentTrace, NaturalLanguageExtractor, TraceTurn


def test_natural_language_extractor_keeps_marker_fixtures_exact():
    trace = AgentTrace(
        session_id="fixture-session",
        agent_id="fixture-agent",
        task_id="fixture-task",
        turns=[
            TraceTurn(
                index=0,
                role="user",
                content="PREFERENCE: database=postgres\nHYPOTHESIS: skip regression tests",
            )
        ],
    )

    atoms = NaturalLanguageExtractor().extract(trace)

    assert [atom.content for atom in atoms] == [
        "database=postgres",
        "skip regression tests",
    ]
    assert [atom.extracted_by_model for atom in atoms] == [
        "deterministic-marker-extractor",
        "deterministic-marker-extractor",
    ]


def test_natural_language_extractor_extracts_unmarked_grounded_memories():
    trace = AgentTrace(
        session_id="natural-session",
        agent_id="natural-agent",
        task_id="natural-task",
        turns=[
            TraceTurn(
                index=0,
                role="user",
                content=(
                    "Please remember database=postgres for this project. "
                    "My editor_theme is dark. I prefer pnpm for package installs."
                ),
            ),
            TraceTurn(index=1, role="environment", content="ANSWER: open approvals tab"),
        ],
        environment={"domain": "benchmark-smoke"},
    )

    atoms = NaturalLanguageExtractor().extract(trace)
    contents = [atom.content for atom in atoms]

    assert "database=postgres" in contents
    assert "editor_theme is dark" in contents
    assert "pnpm for package installs" in contents
    assert "open approvals tab" in contents
    for atom in atoms:
        assert atom.extracted_by_model == "natural-language-heuristic-extractor"
        assert atom.extraction_prompt_version == "cem-natural-language-v1"
        assert atom.source_spans
        assert atom.content in atom.source_spans[0].text
