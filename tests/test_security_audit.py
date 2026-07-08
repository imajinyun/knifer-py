from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts import check_security_audit


def test_audit_command_uses_extra_args() -> None:
    command = check_security_audit.audit_command(["--strict", "--format", "json"])

    assert command[0].endswith("pip-audit")
    assert command[1:] == [
        "--cache-dir",
        str(check_security_audit.DEFAULT_CACHE_DIR),
        "--strict",
        "--format",
        "json",
    ]


def test_run_security_audit_returns_subprocess_code() -> None:
    def fake_run(
        command: Sequence[str],
        cwd: Path,
        check: bool,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        assert command == check_security_audit.audit_command(["--dry-run"])
        assert cwd == check_security_audit.PROJECT_ROOT
        assert check is False
        return subprocess.CompletedProcess(command, 7)

    assert check_security_audit.run_security_audit(["--dry-run"], runner=fake_run) == 7
