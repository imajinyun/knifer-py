from __future__ import annotations

from scripts.check_release_workflow import check_release_workflow


def test_release_workflow_check_accepts_required_tokens() -> None:
    text = """
permissions:
  attestations: write
  id-token: write
steps:
  - uses: actions/attest-build-provenance@v2
    with:
      subject-path: dist/*
  - uses: actions/attest-build-provenance@v2
    with:
      subject-path: sbom.cdx.json
"""

    assert check_release_workflow(text) == []


def test_release_workflow_check_reports_missing_tokens() -> None:
    missing = check_release_workflow("permissions:\n  contents: read\n")

    assert "attestations: write" in missing
    assert "id-token: write" in missing
    assert "actions/attest-build-provenance@v2" in missing
    assert "subject-path: dist/*" in missing
    assert "subject-path: sbom.cdx.json" in missing
