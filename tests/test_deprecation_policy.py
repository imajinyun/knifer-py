from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

STATUS_FILE = Path(__file__).resolve().parents[1] / "api" / "facade-status.json"
DEPRECATED_SMOKE: dict[str, tuple[str, Callable[[ModuleType], None]]] = {
    "vdict": ("vmap", lambda module: cast(Any, module).New()),
    "vseq": ("vslice", lambda module: cast(Any, module).is_empty([])),
}


def _deprecated_modules() -> dict[str, str]:
    payload = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    return {
        name: str(entry["replacement"])
        for name, entry in payload["modules"].items()
        if entry["status"] == "deprecated"
    }


def test_deprecated_facade_registry_matches_smoke_cases() -> None:
    assert _deprecated_modules() == {
        name: replacement for name, (replacement, _smoke) in DEPRECATED_SMOKE.items()
    }


@pytest.mark.parametrize("module_name", sorted(DEPRECATED_SMOKE))
def test_deprecated_facades_warn_with_replacement(module_name: str) -> None:
    replacement, smoke = DEPRECATED_SMOKE[module_name]
    module = importlib.import_module(f"kniferpy.{module_name}")

    with pytest.warns(DeprecationWarning, match=rf"kniferpy\.{replacement}"):
        smoke(module)
