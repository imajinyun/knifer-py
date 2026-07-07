from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
LOCAL_POETRY = PROJECT_ROOT / ".venv" / "bin" / "poetry"
POETRY = str(LOCAL_POETRY) if LOCAL_POETRY.exists() else "poetry"
BENCHMARK_OUTPUT = "tmp/benchmark-smoke.json"
BENCHMARK_BASELINE = "api/benchmark-smoke-baseline.json"


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]


CHECK_STEPS = [
    Step("ruff", (PYTHON, "-m", "ruff", "check", "src", "tests", "examples")),
    Step("mypy", (PYTHON, "-m", "mypy", "src", "tests", "examples")),
    Step("api snapshot", (PYTHON, "scripts/check_api_snapshot.py")),
    Step("error taxonomy", (PYTHON, "scripts/check_error_taxonomy.py")),
    Step("facade consistency", (PYTHON, "scripts/check_facade_consistency.py")),
    Step("facade status", (PYTHON, "scripts/check_facade_status.py")),
    Step("README smoke", (PYTHON, "scripts/check_readme_smoke.py")),
    Step("examples smoke", (PYTHON, "examples/smoke.py")),
    Step(
        "benchmark smoke",
        (
            PYTHON,
            "scripts/benchmark_smoke.py",
            "--output",
            BENCHMARK_OUTPUT,
            "--baseline",
            BENCHMARK_BASELINE,
        ),
    ),
    Step("changelog", (PYTHON, "scripts/generate_changelog.py", "--check")),
    Step("pytest", (PYTHON, "-m", "pytest")),
    Step(
        "coverage",
        (
            PYTHON,
            "-m",
            "pytest",
            "--cov=kniferpy",
            "--cov-branch",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=95",
        ),
    ),
]
DIST_STEPS = [
    Step("build", (POETRY, "build")),
    Step("twine", (PYTHON, "-m", "twine", "check", "dist/*")),
    Step("SBOM smoke", (PYTHON, "scripts/check_sbom_smoke.py")),
]


def _run_step(step: Step) -> int:
    command = _expand_globs(step.command)
    print(f"==> {step.name}: {' '.join(command)}", flush=True)
    try:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


def _expand_globs(command: tuple[str, ...]) -> tuple[str, ...]:
    expanded: list[str] = []
    for arg in command:
        if arg == "dist/*":
            paths = sorted(
                str(path.relative_to(PROJECT_ROOT)) for path in (PROJECT_ROOT / "dist").glob("*")
            )
            expanded.extend(paths or [arg])
        else:
            expanded.append(arg)
    return tuple(expanded)


def _run_steps(steps: Sequence[Step]) -> int:
    for step in steps:
        code = _run_step(step)
        if code != 0:
            print(f"release readiness failed at step: {step.name}", file=sys.stderr)
            return code
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run release readiness gates.")
    parser.add_argument(
        "--skip-dist",
        action="store_true",
        help="skip distribution build and twine validation",
    )
    args = parser.parse_args(argv)

    steps = CHECK_STEPS if args.skip_dist else [*CHECK_STEPS, *DIST_STEPS]
    return _run_steps(steps)


if __name__ == "__main__":
    raise SystemExit(main())
