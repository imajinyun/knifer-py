from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VENV = PROJECT_ROOT / "tmp" / "min-deps-venv"
Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class MinDepsConfig:
    venv: Path
    keep_venv: bool
    python: str


def config_from_env(env: dict[str, str] | None = None) -> MinDepsConfig:
    values = env if env is not None else os.environ
    venv = Path(values.get("MIN_DEPS_VENV", str(DEFAULT_VENV)))
    if not venv.is_absolute():
        venv = PROJECT_ROOT / venv
    keep_venv = values.get("MIN_DEPS_KEEP_VENV") == "1"
    python = values.get("MIN_DEPS_PYTHON", sys.executable)
    return MinDepsConfig(venv=venv, keep_venv=keep_venv, python=python)


def python_bin(venv: Path) -> Path:
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    exe = "python.exe" if sys.platform == "win32" else "python"
    return venv / bin_dir / exe


def command_plan(config: MinDepsConfig) -> list[list[str]]:
    python = str(python_bin(config.venv))
    return [
        [config.python, "-m", "venv", str(config.venv)],
        [python, "-m", "pip", "install", "--upgrade", "pip", "pytest"],
        [
            python,
            "-m",
            "pip",
            "install",
            ".[all]",
            "-c",
            "requirements-min.txt",
        ],
        [python, "scripts/run_core_tests.py"],
        [python, "examples/smoke.py"],
    ]


def _run(command: Sequence[str], *, runner: Runner) -> int:
    print("==> " + " ".join(command), flush=True)
    return runner(command, cwd=PROJECT_ROOT, check=False).returncode


def run_min_deps_smoke(
    config: MinDepsConfig | None = None,
    *,
    runner: Runner = subprocess.run,
) -> int:
    selected = config if config is not None else config_from_env()
    if selected.venv.exists() and not selected.keep_venv:
        shutil.rmtree(selected.venv)

    try:
        for command in command_plan(selected):
            code = _run(command, runner=runner)
            if code != 0:
                return code
        return 0
    finally:
        if selected.venv.exists() and not selected.keep_venv:
            shutil.rmtree(selected.venv)


def main() -> int:
    try:
        return run_min_deps_smoke()
    except OSError as exc:
        print(f"minimum dependency smoke failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
