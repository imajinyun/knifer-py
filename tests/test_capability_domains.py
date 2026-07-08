from __future__ import annotations

from scripts.check_capability_domains import validate_registry


def _registry() -> dict[str, object]:
    return {
        "schema_version": 1,
        "domains": {
            "trust_boundary": {"description": "boundary"},
            "runtime_ops": {"description": "runtime"},
        },
        "modules": {
            "vhttp": {
                "domain": "trust_boundary",
                "security_sensitive": True,
                "star": True,
            }
        },
    }


def test_validate_registry_accepts_complete_registry() -> None:
    assert validate_registry(_registry(), {"vhttp"}) == []


def test_validate_registry_reports_missing_unknown_domain_and_bool_errors() -> None:
    registry = _registry()
    modules = registry["modules"]
    assert isinstance(modules, dict)
    modules["vurl"] = {
        "domain": "missing",
        "security_sensitive": "yes",
        "star": "no",
    }

    errors = validate_registry(registry, {"vhttp", "vurl", "vjson"})

    assert "capability-domains missing modules: vjson" in errors
    assert "vurl: unknown domain 'missing'" in errors
    assert "vurl: star must be a boolean" in errors
    assert "vurl: security_sensitive must be a boolean" in errors


def test_validate_registry_rejects_star_facade_in_non_star_domain() -> None:
    registry = _registry()
    modules = registry["modules"]
    assert isinstance(modules, dict)
    modules["vjob"] = {
        "domain": "runtime_ops",
        "security_sensitive": False,
        "star": True,
    }

    errors = validate_registry(registry, {"vhttp", "vjob"})

    assert "vjob: star facade cannot use domain 'runtime_ops'" in errors
