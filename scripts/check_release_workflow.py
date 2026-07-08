from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "release.yml"
REQUIRED_TOKENS = (
    "attestations: write",
    "id-token: write",
    "actions/attest-build-provenance@v2",
    "subject-path: dist/*",
    "subject-path: sbom.cdx.json",
)


def check_release_workflow(text: str) -> list[str]:
    return [token for token in REQUIRED_TOKENS if token not in text]


def main() -> int:
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    missing = check_release_workflow(text)
    if missing:
        print("release workflow provenance check failed:", file=sys.stderr)
        for token in missing:
            print(f"- missing token: {token}", file=sys.stderr)
        return 1

    print("release workflow provenance check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
