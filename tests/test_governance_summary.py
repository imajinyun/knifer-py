from __future__ import annotations

from scripts.check_governance_summary import Check, render_summary


def test_render_summary_reports_pass_and_fail_counts() -> None:
    summary = render_summary(
        [
            Check("api.snapshot", True, "public API snapshot gate"),
            Check("release.provenance", False, "release artifact and SBOM provenance"),
        ]
    )

    assert summary == """# kniferpy Governance Summary

Total: 1/2 checks passed

- PASS api.snapshot: public API snapshot gate
- FAIL release.provenance: release artifact and SBOM provenance
"""
