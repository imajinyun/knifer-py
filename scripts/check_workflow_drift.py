from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Requirement:
    path: str
    token: str
    label: str


REQUIREMENTS = (
    Requirement("Makefile", "api-check:", "Makefile exposes API snapshot gate"),
    Requirement("Makefile", "taxonomy-check:", "Makefile exposes error taxonomy gate"),
    Requirement("Makefile", "facade-check:", "Makefile exposes facade consistency gate"),
    Requirement("Makefile", "facade-status-check:", "Makefile exposes facade status gate"),
    Requirement("Makefile", "capability-check:", "Makefile exposes capability domain gate"),
    Requirement(
        "Makefile",
        "capability-test-policy-check:",
        "Makefile exposes capability test policy gate",
    ),
    Requirement("Makefile", "readme-smoke:", "Makefile exposes README smoke gate"),
    Requirement("Makefile", "bench-smoke:", "Makefile exposes benchmark smoke gate"),
    Requirement("Makefile", "test-core:", "Makefile exposes core test subset"),
    Requirement("Makefile", "release-ready:", "Makefile exposes release readiness gate"),
    Requirement("Makefile", "sbom-smoke:", "Makefile exposes SBOM smoke gate"),
    Requirement("Makefile", "security-audit:", "Makefile exposes security audit gate"),
    Requirement("Makefile", "min-deps-smoke:", "Makefile exposes minimum dependency smoke"),
    Requirement("Makefile", "release-workflow-check:", "Makefile exposes provenance check"),
    Requirement("Makefile", "governance-summary:", "Makefile exposes governance summary"),
    Requirement(".github/workflows/ci.yml", "scripts/check_api_snapshot.py", "CI runs API check"),
    Requirement(
        ".github/workflows/ci.yml",
        "scripts/check_error_taxonomy.py",
        "CI runs error taxonomy check",
    ),
    Requirement(
        ".github/workflows/ci.yml",
        "scripts/check_facade_consistency.py",
        "CI runs facade consistency check",
    ),
    Requirement(
        ".github/workflows/ci.yml",
        "scripts/check_facade_status.py",
        "CI runs facade status check",
    ),
    Requirement(
        ".github/workflows/ci.yml",
        "scripts/check_readme_smoke.py",
        "CI runs README smoke check",
    ),
    Requirement(
        ".github/workflows/ci.yml",
        "scripts/benchmark_smoke.py",
        "CI runs benchmark smoke",
    ),
    Requirement(".github/workflows/ci.yml", "scripts/run_core_tests.py", "CI runs core tests"),
    Requirement(
        ".github/workflows/release.yml",
        "make install",
        "release workflow uses Makefile install target",
    ),
    Requirement(
        ".github/workflows/release.yml",
        "make release-ready",
        "release workflow uses Makefile release readiness target",
    ),
    Requirement(
        ".github/workflows/release.yml",
        "make sbom-smoke",
        "release workflow uses Makefile SBOM target",
    ),
    Requirement(
        ".github/workflows/release.yml",
        "actions/attest-build-provenance@v2",
        "release workflow attests artifacts",
    ),
    Requirement(
        ".github/workflows/security.yml",
        "scripts/check_security_audit.py",
        "security workflow runs shared audit script",
    ),
)


def find_missing(requirements: tuple[Requirement, ...] = REQUIREMENTS) -> list[Requirement]:
    cache: dict[str, str] = {}
    missing: list[Requirement] = []
    for requirement in requirements:
        path = PROJECT_ROOT / requirement.path
        if not path.exists():
            missing.append(requirement)
            continue
        text = cache.setdefault(requirement.path, path.read_text(encoding="utf-8"))
        if requirement.token not in text:
            missing.append(requirement)
    return missing


def render_missing(missing: list[Requirement]) -> str:
    if not missing:
        return "workflow drift check passed\n"
    lines = ["workflow drift check failed:"]
    for requirement in missing:
        lines.append(
            f"- {requirement.path}: missing {requirement.token!r} ({requirement.label})"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    missing = find_missing()
    output = render_missing(missing)
    print(output, end="", file=sys.stderr if missing else sys.stdout)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
