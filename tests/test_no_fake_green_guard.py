import ast
from pathlib import Path

OPERATIONS = Path("packages/cem-core/src/cem_core/operations.py")

# Allowlist of known fake-green checks. The Correction Capture track's two
# entries (correction_controller_wired, recent_corrections_recorded) were made
# honest, so the set is now empty. Any literal-bool _check fails the test.
ALLOWLISTED_FAKE_GREEN: set[str] = set()


def _literal_bool_check_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_check"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, bool)
            and isinstance(node.args[0], ast.Constant)
        ):
            names.add(node.args[0].value)
    return names


def test_no_new_fake_green_checks():
    found = _literal_bool_check_names(OPERATIONS.read_text(encoding="utf-8"))
    new_offenders = found - ALLOWLISTED_FAKE_GREEN
    assert not new_offenders, f"New fake-green _check(...) with literal bool: {sorted(new_offenders)}"


def test_guard_detects_a_literal_bool_check():
    # Failure canary: prove the guard actually bites on a fake-green pattern.
    sample = "def f():\n    _check('always_ok', True, 'x')\n"
    assert _literal_bool_check_names(sample) == {"always_ok"}
