from __future__ import annotations

import builtins
import importlib
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from types import ModuleType

import pytest

from kniferpy.internal.optionalx import OptionalDependencyError, require_extra


@contextmanager
def _missing_import(package: str, *module_names: str) -> Iterator[None]:
    original_import = builtins.__import__
    removed: dict[str, ModuleType] = {}

    for module_name in module_names:
        module = sys.modules.pop(module_name, None)
        if module is not None:
            removed[module_name] = module

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = None,
        level: int = 0,
    ) -> ModuleType:
        if name == package or name.startswith(f"{package}."):
            raise ModuleNotFoundError(f"No module named {package!r}", name=package)
        return original_import(name, globals, locals, fromlist, level)

    builtins.__import__ = fake_import
    try:
        yield
    finally:
        builtins.__import__ = original_import
        sys.modules.update(removed)


def test_require_extra_builds_friendly_error() -> None:
    cause = ModuleNotFoundError("No module named 'requests'", name="requests")

    err = require_extra("requests", "http", cause)

    assert isinstance(err, OptionalDependencyError)
    assert err.code == "knifer.optional_dependency_missing"
    assert err.context == {"module": "requests", "extra": "http", "package": "requests"}
    assert 'pip install "kniferpy[http]"' in err.message
    assert err.cause is cause


@pytest.mark.parametrize(
    ("package", "module_name", "extra"),
    [
        ("requests", "kniferpy.internal.httpx", "http"),
        ("jwt", "kniferpy.internal.jwtx", "jwt"),
        ("argon2", "kniferpy.internal.cryptox", "crypto"),
        ("PIL", "kniferpy.internal.imgx", "img"),
        ("openpyxl", "kniferpy.internal.poix", "poi"),
    ],
)
def test_optional_imports_raise_friendly_error(
    package: str, module_name: str, extra: str
) -> None:
    with _missing_import(package, module_name), pytest.raises(OptionalDependencyError) as exc_info:
        importlib.import_module(module_name)

    err = exc_info.value
    assert err.code == "knifer.optional_dependency_missing"
    assert err.context["extra"] == extra
    assert f'pip install "kniferpy[{extra}]"' in err.message
