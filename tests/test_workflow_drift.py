from __future__ import annotations

from scripts.check_workflow_drift import Requirement, render_missing


def test_render_missing_reports_pass_when_empty() -> None:
    assert render_missing([]) == "workflow drift check passed\n"


def test_render_missing_reports_path_token_and_label() -> None:
    rendered = render_missing(
        [
            Requirement(
                path=".github/workflows/ci.yml",
                token="scripts/check_api_snapshot.py",
                label="CI runs API check",
            )
        ]
    )

    assert rendered == (
        "workflow drift check failed:\n"
        "- .github/workflows/ci.yml: missing 'scripts/check_api_snapshot.py' "
        "(CI runs API check)\n"
    )
