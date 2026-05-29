"""Shared no-fake-green AST scanner (Phase 5).

Single source of truth for the ``_check(name, <literal bool>, ...)`` anti-pattern
detector (the ``operations.py:234/:249`` hardcoded-health-value pattern). Imported
by BOTH the guard test and the production-readiness gate, so the same bite that
polices the monitor now also polices the gate module. Lives in cem-eval (never in
a scanned source file, so the linter never walks its own source) and imports
nothing from cem-core -- the one-way cem-eval -> cem-core layering is preserved.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable


def literal_bool_check_names(source: str) -> set[str]:
    """Names passed to ``_check(name, <literal bool>, ...)`` in ``source`` -- a
    hardcoded pass/fail the monitor/readiness layer must never contain. Body is
    behaviour-identical to the original inline guard so its bite is preserved.
    """
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


def literal_bool_check_names_in_files(paths: Iterable[str | Path]) -> set[str]:
    """Union of literal-bool ``_check`` names across the given source files."""
    offenders: set[str] = set()
    for path in paths:
        offenders |= literal_bool_check_names(Path(path).read_text(encoding="utf-8"))
    return offenders
