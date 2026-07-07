"""Template engine with HTML and text backends.

Thin facade over kniferpy.internal.tplx, porting knifer-go's vtpl surface.

Provides a template engine with HTML/text backends, configurable
delimiters, function maps, and per-call render options.
"""

from __future__ import annotations

from kniferpy.internal.tplx import (
    Engine,
    EngineFunc,
    EngineOption,
    ErrInvalidRenderRequest,
    ErrMissingEngine,
    RenderOption,
    RenderRequest,
    new_html_engine,
    new_text_engine,
    render,
    render_template,
    render_with_engine,
    render_with_options,
    with_delims,
    with_engine_delims,
    with_engine_func_map,
    with_engine_template_name,
    with_func_map,
    with_template_executor,
    with_template_factory,
    with_template_name,
    with_template_parser,
)

__all__ = [
    "Engine",
    "EngineFunc",
    "EngineOption",
    "ErrInvalidRenderRequest",
    "ErrMissingEngine",
    "RenderRequest",
    "RenderOption",
    "new_html_engine",
    "new_text_engine",
    "render",
    "render_template",
    "render_with_engine",
    "render_with_options",
    "with_delims",
    "with_engine_delims",
    "with_engine_func_map",
    "with_engine_template_name",
    "with_func_map",
    "with_template_executor",
    "with_template_factory",
    "with_template_name",
    "with_template_parser",
]
