from __future__ import annotations

from kniferpy.verr import KniferError


class OptionalDependencyError(KniferError):
    """Raised when a facade requires an optional dependency extra."""


def require_extra(module_name: str, extra: str, cause: ImportError) -> OptionalDependencyError:
    package = cause.name or module_name
    return OptionalDependencyError(
        message=(
            f"optional dependency {package!r} is required for this feature; "
            f'install it with `pip install "kniferpy[{extra}]"`'
        ),
        code="knifer.optional_dependency_missing",
        context={"module": module_name, "extra": extra, "package": package},
        cause=cause,
    )
