from __future__ import annotations

from pathlib import Path

from scripts.check_capability_test_policy import validate_policy


def _registry() -> dict[str, object]:
    return {
        "schema_version": 1,
        "modules": {
            "vhttp": {"domain": "trust_boundary", "security_sensitive": True, "star": True},
            "vjson": {"domain": "data_format", "security_sensitive": False, "star": True},
            "vdict": {
                "domain": "collection_algorithms",
                "security_sensitive": False,
                "star": False,
            },
        },
    }


def _status() -> dict[str, object]:
    return {
        "schema_version": 1,
        "modules": {
            "vhttp": {"status": "stable"},
            "vjson": {"status": "stable"},
            "vdict": {"status": "deprecated", "replacement": "vmap"},
        },
    }


def test_validate_policy_accepts_star_security_and_deprecated_facades(tmp_path: Path) -> None:
    (tmp_path / "test_vhttp.py").write_text(
        "from kniferpy.verr import SecurityError\n\n"
        "def test_safe_http():\n"
        "    assert SecurityError\n",
        encoding="utf-8",
    )
    (tmp_path / "test_vjson.py").write_text(
        "def test_json_read():\n    assert True\n",
        encoding="utf-8",
    )
    (tmp_path / "test_deprecation_policy.py").write_text(
        "def test_vdict_deprecated():\n    assert True\n",
        encoding="utf-8",
    )

    assert validate_policy(_registry(), _status(), test_root=tmp_path) == []


def test_validate_policy_reports_missing_test_file(tmp_path: Path) -> None:
    registry = {
        "schema_version": 1,
        "modules": {"vjson": _registry()["modules"]["vjson"]},  # type: ignore[index]
    }
    status = {"schema_version": 1, "modules": {"vjson": {"status": "stable"}}}

    assert validate_policy(registry, status, test_root=tmp_path) == ["vjson: missing test file"]


def test_validate_policy_reports_star_without_test_function(tmp_path: Path) -> None:
    (tmp_path / "test_vjson.py").write_text("VALUE = True\n", encoding="utf-8")
    registry = {
        "schema_version": 1,
        "modules": {"vjson": _registry()["modules"]["vjson"]},  # type: ignore[index]
    }
    status = {"schema_version": 1, "modules": {"vjson": {"status": "stable"}}}

    assert validate_policy(registry, status, test_root=tmp_path) == [
        "vjson: star facade test file must define tests"
    ]


def test_validate_policy_reports_security_sensitive_without_safety_token(tmp_path: Path) -> None:
    (tmp_path / "test_vhttp.py").write_text(
        "def test_http():\n    assert True\n",
        encoding="utf-8",
    )
    registry = {
        "schema_version": 1,
        "modules": {"vhttp": _registry()["modules"]["vhttp"]},  # type: ignore[index]
    }
    status = {"schema_version": 1, "modules": {"vhttp": {"status": "stable"}}}

    assert validate_policy(registry, status, test_root=tmp_path) == [
        "vhttp: security-sensitive facade lacks safety test token"
    ]
