from cem_eval.fake_green_guard import (
    literal_bool_check_names,
    literal_bool_check_names_in_files,
)
from cem_eval.production_readiness import MONITORED_SOURCE_PATHS

# Allowlist of known fake-green checks. The Correction Capture track's two
# entries (correction_controller_wired, recent_corrections_recorded) were made
# honest, so the set is now empty. Any literal-bool _check fails the test.
ALLOWLISTED_FAKE_GREEN: set[str] = set()


def test_no_new_fake_green_checks():
    # Scans operations.py AND the production-readiness gate module (Phase 5 closed
    # the self-referential hole: the gate that asserts no-fake-green is itself policed).
    found = literal_bool_check_names_in_files(MONITORED_SOURCE_PATHS)
    new_offenders = found - ALLOWLISTED_FAKE_GREEN
    assert not new_offenders, f"New fake-green _check(...) with literal bool: {sorted(new_offenders)}"


def test_guard_detects_a_literal_bool_check():
    # Failure canary: prove the (now shared) guard actually bites on a fake-green pattern.
    sample = "def f():\n    _check('always_ok', True, 'x')\n"
    assert literal_bool_check_names(sample) == {"always_ok"}
