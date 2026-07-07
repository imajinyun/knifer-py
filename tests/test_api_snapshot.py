from __future__ import annotations

from typing import Any

from scripts.check_api_snapshot import diff_snapshot


def _snapshot(signature: str = "(x: int) -> str") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "package": "kniferpy",
        "root_exports": ["vfoo"],
        "modules": {
            "vfoo": {
                "exports": {
                    "convert": {
                        "kind": "function",
                        "signature": signature,
                        "type": "builtins.function",
                    },
                    "Thing": {
                        "kind": "class",
                        "signature": "()",
                        "type": "builtins.type",
                        "methods": {"run": {"signature": "(self) -> None"}},
                    },
                }
            }
        },
    }


def test_diff_snapshot_accepts_identical_snapshot() -> None:
    snapshot = _snapshot()

    assert diff_snapshot(snapshot, snapshot) == []


def test_diff_snapshot_reports_removed_export_and_signature_change() -> None:
    expected = _snapshot()
    actual = _snapshot("(x: str) -> str")
    del actual["modules"]["vfoo"]["exports"]["Thing"]

    diffs = diff_snapshot(expected, actual)

    assert "missing export: vfoo.Thing" in diffs
    assert any(diff.startswith("changed signature: vfoo.convert") for diff in diffs)


def test_diff_snapshot_reports_method_signature_change() -> None:
    expected = _snapshot()
    actual = _snapshot()
    actual["modules"]["vfoo"]["exports"]["Thing"]["methods"]["run"]["signature"] = (
        "(self, force: bool) -> None"
    )

    diffs = diff_snapshot(expected, actual)

    assert any(diff.startswith("changed method signature: vfoo.Thing.run") for diff in diffs)
