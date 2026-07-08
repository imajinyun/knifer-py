from __future__ import annotations

from scripts.check_governance_summary import Check, render_summary


def test_render_summary_reports_pass_and_fail_counts() -> None:
    summary = render_summary(
        [
            Check("api.snapshot", True, "public API snapshot gate"),
            Check("workflow.drift", True, "workflow and Makefile gate consistency"),
            Check("release.provenance", False, "release artifact and SBOM provenance"),
        ]
    )

    assert summary == """# kniferpy Governance Summary

Total: 2/3 checks passed

- PASS api.snapshot: public API snapshot gate
- PASS workflow.drift: workflow and Makefile gate consistency
- FAIL release.provenance: release artifact and SBOM provenance
"""
