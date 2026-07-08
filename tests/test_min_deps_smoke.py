from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts import check_min_deps_smoke


def test_config_from_env_uses_project_relative_path() -> None:
    config = check_min_deps_smoke.config_from_env(
        {
            "MIN_DEPS_VENV": "tmp/custom-min",
            "MIN_DEPS_KEEP_VENV": "1",
            "MIN_DEPS_PYTHON": "python3.13",
        }
    )

    assert config.venv == check_min_deps_smoke.PROJECT_ROOT / "tmp" / "custom-min"
    assert config.keep_venv is True
    assert config.python == "python3.13"


def test_command_plan_matches_ci_minimum_deps_flow(tmp_path: Path) -> None:
    config = check_min_deps_smoke.MinDepsConfig(
        venv=tmp_path / "venv",
        keep_venv=True,
        python="python3.11",
    )
    python = str(check_min_deps_smoke.python_bin(config.venv))

    assert check_min_deps_smoke.command_plan(config) == [
        ["python3.11", "-m", "venv", str(config.venv)],
        [python, "-m", "pip", "install", "--upgrade", "pip", "pytest"],
        [python, "-m", "pip", "install", ".[all]", "-c", "requirements-min.txt"],
        [python, "scripts/run_core_tests.py"],
        [python, "examples/smoke.py"],
    ]


def test_run_min_deps_smoke_returns_first_failure(tmp_path: Path) -> None:
    config = check_min_deps_smoke.MinDepsConfig(
        venv=tmp_path / "venv",
        keep_venv=True,
        python=sys.executable,
    )
    calls: list[Sequence[str]] = []

    def fake_run(
        command: Sequence[str],
        cwd: Path,
        check: bool,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        assert cwd == check_min_deps_smoke.PROJECT_ROOT
        assert check is False
        return subprocess.CompletedProcess(command, 9 if len(calls) == 2 else 0)

    assert check_min_deps_smoke.run_min_deps_smoke(config, runner=fake_run) == 9
    assert len(calls) == 2
