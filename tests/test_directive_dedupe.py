from cem_core.local_memory import list_memory, pin_directive


def test_pin_directive_reuses_normalized_duplicate(tmp_path):
    root = tmp_path / "ams"

    first = pin_directive(
        root,
        "Codex must verify before claiming DONE.",
        scope="global-behavior",
        domain_scope="coding",
    )
    second = pin_directive(
        root,
        "codex must verify before claiming done",
        scope="global-behavior",
        domain_scope="coding",
    )

    directives = list_memory(root, kind="directives")["directives"]

    assert first["created"] is True
    assert second["created"] is False
    assert second["duplicate"] is True
    assert second["duplicate_reason"] == "normalized_exact_match"
    assert second["matched_directive_id"] == first["directive"]["directive_id"]
    assert len(directives) == 1


def test_pin_directive_rejects_semantic_duplicate_in_same_scope(tmp_path):
    root = tmp_path / "ams"

    first = pin_directive(
        root,
        (
            "Canonical Codex Execution Contract: for substantive requests, Codex must understand "
            "the request, define the deliverable and DONE criteria, identify dependencies and "
            "assumptions, make a short practical plan before edits, execute the full task, verify "
            "with the strongest available checks, repair failures, and hand off with exact evidence."
        ),
        scope="global-behavior",
        domain_scope="coding",
    )
    second = pin_directive(
        root,
        (
            "Codex execution contract: for substantive requests, understand the request, define "
            "DONE criteria and dependencies, make a practical plan before editing, execute the full "
            "task, verify using the strongest checks, repair any failures, and hand off exact evidence."
        ),
        scope="global-behavior",
        domain_scope="coding",
    )

    directives = list_memory(root, kind="directives")["directives"]

    assert first["created"] is True
    assert second["created"] is False
    assert second["duplicate"] is True
    assert second["duplicate_reason"] == "semantic_token_overlap"
    assert second["matched_directive_id"] == first["directive"]["directive_id"]
    assert len(directives) == 1


def test_pin_directive_allows_same_words_in_different_domain(tmp_path):
    root = tmp_path / "ams"
    content = "Hessa acceptance is binary and partial evidence is not acceptance."

    first = pin_directive(root, content, scope="global-behavior", domain_scope="coding")
    second = pin_directive(root, content, scope="global-behavior", domain_scope="hessa")

    directives = list_memory(root, kind="directives")["directives"]

    assert first["created"] is True
    assert second["created"] is True
    assert len(directives) == 2
