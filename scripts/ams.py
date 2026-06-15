from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _same_executable(left: Path, right: Path) -> bool:
    try:
        return left.resolve().samefile(right.resolve())
    except FileNotFoundError:
        return False
    except OSError:
        return left.resolve() == right.resolve()


def _project_python_candidates() -> tuple[Path, ...]:
    if os.name == "nt":
        return (
            ROOT / ".venv" / "Scripts" / "python.exe",
            ROOT / ".venv" / "Scripts" / "python.cmd",
        )
    return (ROOT / ".venv" / "bin" / "python",)


def _bootstrap_project_python() -> None:
    if os.environ.get("AMS_SKIP_PROJECT_PYTHON") == "1":
        return

    current = Path(sys.executable)
    child_env = os.environ.copy()
    child_env["AMS_SKIP_PROJECT_PYTHON"] = "1"
    for candidate in _project_python_candidates():
        if candidate.exists() and not _same_executable(current, candidate):
            raise SystemExit(
                subprocess.call(
                    [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]],
                    env=child_env,
                )
            )

    bootstrap_env = os.environ.copy()
    bootstrap_env["AMS_SKIP_PROJECT_PYTHON"] = "1"
    if os.environ.get("AMS_PROJECT_PYTHON_BOOTSTRAPPED") != "1":
        uv = shutil.which("uv")
        if uv and (ROOT / "pyproject.toml").exists():
            raise SystemExit(
                subprocess.call(
                    [
                        uv,
                        "run",
                        "--project",
                        str(ROOT),
                        "python",
                        str(Path(__file__).resolve()),
                        *sys.argv[1:],
                    ],
                    env=bootstrap_env,
                )
            )


_bootstrap_project_python()

for package_src in (
    ROOT / "packages" / "cem-core" / "src",
    ROOT / "packages" / "cem-eval" / "src",
):
    sys.path.insert(0, str(package_src))

from cem_core.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
