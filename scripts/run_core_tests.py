from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_TESTS = (
    "tests/test_vjson.py",
    "tests/test_vfile.py",
    "tests/test_vurl.py",
    "tests/test_vstr.py",
    "tests/test_vnum.py",
    "tests/test_vobj.py",
    "tests/test_vcodec.py",
    "tests/test_verr.py",
    "tests/test_vid.py",
    "tests/test_vbool.py",
    "tests/test_vdate.py",
    "tests/test_vregex.py",
)


def pytest_args(extra_args: list[str] | None = None) -> list[str]:
    return [*CORE_TESTS, *(extra_args or [])]


def run_core_tests(extra_args: list[str] | None = None) -> int:
    command = [sys.executable, "-m", "pytest", *pytest_args(extra_args)]
    print("==> " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the dependency-light core test subset.")
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="extra arguments forwarded to pytest after the core test list",
    )
    args = parser.parse_args(argv)
    return run_core_tests(args.pytest_args)


if __name__ == "__main__":
    raise SystemExit(main())
