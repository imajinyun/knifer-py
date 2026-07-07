"""Template engine with HTML and text backends.

Ports knifer-go's internal/template with Python-idiomatic mappings:

- Go html/template(text/template) -> regex-based template engine
- Go context.Context -> not needed (Python templates are synchronous)
- Go Engine interface -> Python Protocol
- Go functional options -> callable configurators

Syntax: ``{{.Field}}``, ``{{func .Field}}`` with configurable delimiters.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from kniferpy.verr import KniferError

# --- errors --------------------------------------------------------------------


class ErrMissingEngine(KniferError):
    pass


class ErrInvalidRenderRequest(KniferError):
    pass


# --- types ---------------------------------------------------------------------


@dataclass
class RenderRequest:
    Source: str = ""
    Data: Any = None


class Engine(Protocol):
    def render(self, req: RenderRequest) -> str: ...


class EngineFunc:
    def __init__(self, fn: Callable[[RenderRequest], str]):
        self._fn = fn

    def render(self, req: RenderRequest) -> str:
        return self._fn(req)


# --- engine config -------------------------------------------------------------


@dataclass
class _EngineConfig:
    name: str = "kniferpy-template"
    func_map: dict[str, Any] | None = None
    delims: tuple[str, str] = ("{{", "}}")


EngineOption = Callable[["_EngineConfig"], None]


def with_engine_template_name(name: str) -> EngineOption:
    def apply(c: _EngineConfig) -> None:
        c.name = name

    return apply


def with_engine_func_map(func_map: dict[str, Any]) -> EngineOption:
    def apply(c: _EngineConfig) -> None:
        c.func_map = func_map

    return apply


def with_engine_delims(left: str, right: str) -> EngineOption:
    def apply(c: _EngineConfig) -> None:
        c.delims = (left, right)

    return apply


def _apply_engine_options(opts: list[EngineOption]) -> _EngineConfig:
    cfg = _EngineConfig()
    for opt in opts:
        if opt is not None:
            opt(cfg)
    if not cfg.name:
        cfg.name = "kniferpy-template"
    return cfg


# --- built-in engines ----------------------------------------------------------


def new_html_engine(*opts: EngineOption) -> Engine:
    cfg = _apply_engine_options(list(opts))
    return EngineFunc(lambda req: _render_engine(req, cfg, html_escape=True))


def new_text_engine(*opts: EngineOption) -> Engine:
    cfg = _apply_engine_options(list(opts))
    return EngineFunc(lambda req: _render_engine(req, cfg, html_escape=False))


def _render_engine(req: RenderRequest, cfg: _EngineConfig, html_escape: bool) -> str:
    _validate_render_request(req)
    result = _render_template(req.Source, req.Data, cfg.func_map, cfg.delims)
    if html_escape:
        result = html.escape(result)
    return result


def _validate_render_request(req: RenderRequest) -> None:
    if not req.Source:
        raise ErrInvalidRenderRequest("empty source")


def render_with_engine(engine: Engine | None, source: str, data: Any) -> str:
    if engine is None:
        raise ErrMissingEngine("missing engine")
    return engine.render(RenderRequest(Source=source, Data=data))


# --- render options ------------------------------------------------------------


@dataclass
class _RenderConfig:
    name: str = "kniferpy-template"
    func_map: dict[str, Any] | None = None
    delims: tuple[str, str] = ("{{", "}}")
    factory: Callable[..., Any] | None = None
    parser: Callable[[str], str] | None = None
    executor: Callable[[str, Any], str] | None = None


RenderOption = Callable[["_RenderConfig"], None]


def with_template_name(name: str) -> RenderOption:
    def apply(c: _RenderConfig) -> None:
        c.name = name

    return apply


def with_func_map(func_map: dict[str, Any]) -> RenderOption:
    def apply(c: _RenderConfig) -> None:
        c.func_map = func_map

    return apply


def with_delims(left: str, right: str) -> RenderOption:
    def apply(c: _RenderConfig) -> None:
        c.delims = (left, right)

    return apply


def with_template_factory(factory: Callable[..., Any]) -> RenderOption:
    def apply(c: _RenderConfig) -> None:
        c.factory = factory

    return apply


def with_template_parser(parser: Callable[[str], str]) -> RenderOption:
    def apply(c: _RenderConfig) -> None:
        c.parser = parser

    return apply


def with_template_executor(executor: Callable[[str, Any], str]) -> RenderOption:
    def apply(c: _RenderConfig) -> None:
        c.executor = executor

    return apply


def _apply_render_options(opts: list[RenderOption]) -> _RenderConfig:
    cfg = _RenderConfig()
    for opt in opts:
        if opt is not None:
            opt(cfg)
    if not cfg.name:
        cfg.name = "kniferpy-template"
    return cfg


# --- render --------------------------------------------------------------------


def render(tpl: str, data: Any) -> str:
    return render_with_options(tpl, data)


def render_with_options(tpl: str, data: Any, *opts: RenderOption) -> str:
    cfg = _apply_render_options(list(opts))
    delims = cfg.delims
    func_map = cfg.func_map

    if cfg.factory is not None:
        cfg.factory(cfg.name)
    if cfg.parser is not None:
        tpl = cfg.parser(tpl)
    if cfg.executor is not None:
        return cfg.executor(tpl, data)

    return _render_template(tpl, data, func_map, delims)


def render_template(tpl: str, data: Any) -> str:
    return render(tpl, data)


# --- template engine core ------------------------------------------------------


def _data_as_dict(data: Any) -> dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if hasattr(data, "__dict__"):
        return {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
    return {".": data}


def _render_template(
    source: str,
    data: Any,
    func_map: dict[str, Any] | None,
    delims: tuple[str, str],
) -> str:
    data_dict = _data_as_dict(data)
    left, right = delims
    lq = re.escape(left)
    rq = re.escape(right)

    expr_re = re.compile(lq + r"\s*(.+?)\s*" + rq)

    def _replace(match: re.Match[str]) -> str:
        expr = match.group(1).strip()
        return _eval_expr(expr, data_dict, func_map)

    return expr_re.sub(_replace, source)


def _eval_expr(expr: str, data: dict[str, Any], func_map: dict[str, Any] | None) -> str:
    if expr == ".":
        return str(data.get(".", ""))
    if expr.startswith("."):
        field = expr[1:]
        return str(data.get(field, ""))

    parts = expr.split(None, 1)
    if len(parts) == 2 and func_map is not None:
        func_name = parts[0]
        arg_expr = parts[1]
        if func_name in func_map:
            arg_val = _eval_expr(arg_expr, data, func_map)
            return str(func_map[func_name](arg_val))

    if func_map is not None and expr in func_map:
        return str(func_map[expr](data))

    return f"{_DEFAULT_LEFT}{expr}{_DEFAULT_RIGHT}"


_DEFAULT_LEFT = "{{"
_DEFAULT_RIGHT = "}}"
