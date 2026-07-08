from __future__ import annotations

import os
import shlex
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PIP_AUDIT = PROJECT_ROOT / ".venv" / "bin" / "pip-audit"
PIP_AUDIT = str(LOCAL_PIP_AUDIT) if LOCAL_PIP_AUDIT.exists() else "pip-audit"
DEFAULT_CACHE_DIR = PROJECT_ROOT / "tmp" / "pip-audit-cache"


Runner = Callable[..., subprocess.CompletedProcess[str]]


def audit_command(extra_args: Sequence[str] | None = None) -> list[str]:
    return [PIP_AUDIT, "--cache-dir", str(DEFAULT_CACHE_DIR), *(extra_args or [])]


def run_security_audit(
    extra_args: Sequence[str] | None = None,
    *,
    runner: Runner = subprocess.run,
) -> int:
    command = audit_command(extra_args)
    print("==> " + " ".join(command), flush=True)
    return runner(command, cwd=PROJECT_ROOT, check=False).returncode


def main() -> int:
    extra_args = shlex.split(os.environ.get("PIP_AUDIT_ARGS", ""))
    try:
        return run_security_audit(extra_args)
    except OSError as exc:
        print(f"security audit failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
