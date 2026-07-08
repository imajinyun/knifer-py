from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def _read(path: str) -> str:
    return (PROJECT_ROOT / path).read_text(encoding="utf-8")


def _has(path: str, token: str) -> bool:
    return token in _read(path)


def _exists(path: str) -> bool:
    return (PROJECT_ROOT / path).exists()


def collect_checks() -> list[Check]:
    return [
        Check("make.check", _has("Makefile", "check:"), "daily lint/type/API/test gate"),
        Check(
            "make.release-ready",
            _has("Makefile", "release-ready:"),
            "release readiness aggregate gate",
        ),
        Check(
            "api.snapshot",
            _exists("api/kniferpy-public-api.json")
            and _has("Makefile", "scripts/check_api_snapshot.py"),
            "public API snapshot gate",
        ),
        Check(
            "api.index",
            _has("Makefile", "api-index:")
            and _has("scripts/check_api_snapshot.py", "--print-index"),
            "stdout public API index",
        ),
        Check(
            "facade.status",
            _exists("api/facade-status.json")
            and _exists("scripts/check_facade_status.py")
            and _has("Makefile", "facade-status-check:"),
            "facade lifecycle registry",
        ),
        Check(
            "error.taxonomy",
            _exists("scripts/check_error_taxonomy.py")
            and _has("Makefile", "taxonomy-check:"),
            "stable error code taxonomy",
        ),
        Check(
            "core.tests",
            _exists("scripts/run_core_tests.py")
            and _has("Makefile", "test-core:")
            and _has(".github/workflows/ci.yml", "python scripts/run_core_tests.py"),
            "dependency-light core subset in CI",
        ),
        Check(
            "benchmark.smoke",
            _exists("api/benchmark-smoke-baseline.json")
            and _has("Makefile", "bench-smoke:")
            and _has(".github/workflows/ci.yml", "benchmark_smoke.py"),
            "benchmark JSON artifact and baseline",
        ),
        Check(
            "sbom.smoke",
            _exists("scripts/check_sbom_smoke.py")
            and _has("Makefile", "sbom-smoke:")
            and _has(".github/workflows/release.yml", "sbom.cdx.json"),
            "CycloneDX SBOM generation and validation",
        ),
        Check(
            "release.provenance",
            _exists("scripts/check_release_workflow.py")
            and _has("Makefile", "release-workflow-check:")
            and _has(".github/workflows/release.yml", "actions/attest-build-provenance@v2"),
            "release artifact and SBOM provenance",
        ),
        Check(
            "workflow.drift",
            _exists("scripts/check_workflow_drift.py")
            and _has("Makefile", "workflow-drift-check:"),
            "workflow and Makefile gate consistency",
        ),
        Check(
            "security.audit",
            _exists("scripts/check_security_audit.py")
            and _has("Makefile", "security-audit:")
            and _has(".github/workflows/security.yml", "scripts/check_security_audit.py"),
            "local and workflow dependency audit gate",
        ),
        Check(
            "minimum.deps",
            _exists("requirements-min.txt")
            and _exists("scripts/check_min_deps_smoke.py")
            and _has("Makefile", "min-deps-smoke:")
            and _has(".github/workflows/ci.yml", "minimum runtime dependencies"),
            "local and workflow minimum dependency smoke",
        ),
        Check(
            "pypy.smoke",
            _has(".github/workflows/ci.yml", "pypy3.10")
            and _has(".github/workflows/ci.yml", "Core tests"),
            "PyPy core subset job",
        ),
    ]


def render_summary(checks: list[Check]) -> str:
    passed = sum(1 for check in checks if check.ok)
    lines = [
        "# kniferpy Governance Summary",
        "",
        f"Total: {passed}/{len(checks)} checks passed",
        "",
    ]
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        lines.append(f"- {status} {check.name}: {check.detail}")
    return "\n".join(lines) + "\n"


def main() -> int:
    checks = collect_checks()
    print(render_summary(checks), end="")
    if any(not check.ok for check in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
