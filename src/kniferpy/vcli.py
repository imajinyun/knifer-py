"""Shell-free process execution, ANSI coloring, and a small command tree.

Run external programs with :func:`run`/:func:`output` — argv is passed
directly to :func:`subprocess.run`, so a shell is never invoked and captured
output can be bounded with ``max_output_bytes``. Build a lightweight
subcommand tree with :class:`Command`, render deterministic usage text with
:func:`render_help`, and wrap strings in ANSI escapes with :func:`colorize`.

knifer-go's functional ``With*`` exec/execute/color options collapse into
keyword arguments; its ``FlagParser`` wrapper around ``flag.FlagSet`` is
replaced by an :mod:`argparse` parser supplied through
:attr:`Command.flags`. ``io.Reader``/``io.Writer`` streams become
``str``/``bytes`` and :class:`~typing.TextIO`. Errors raise
:mod:`kniferpy.verr` types instead of returning sentinels.
"""

from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal import clix
from kniferpy.internal.clix import (
    Color,
    ColorMode,
    Command,
    ExecResult,
    FlagParseResult,
    FlagParser,
    Handler,
    Invocation,
    Runner,
    RunnerFunc,
)
from kniferpy.verr import KniferError, ValidationError

# ── Go-compat type aliases ────────────────────────────────────────────────────

ExecRequest = Any  # Go: cli.ExecRequest
ExecOption = Callable[[Any], None]
ExecuteOption = Callable[[Any], None]
FlagParserOption = Callable[[Any], None]
ColorOption = Callable[[Any], None]

# ── Go-compat sentinel errors ─────────────────────────────────────────────────


def _empty_command() -> ValidationError:
    return ValidationError("empty command", code="knifer.cli.empty_command")


def _output_limit_exceeded() -> KniferError:
    return KniferError("output limit exceeded", code="knifer.cli.output_limit_exceeded")


def _usage(detail: str = "") -> ValidationError:
    return ValidationError(f"usage: {detail}" if detail else "usage", code="knifer.cli.usage")


ErrEmptyCommand: ValidationError = _empty_command()
ErrOutputLimitExceeded: KniferError = _output_limit_exceeded()
ErrUsage: ValidationError = _usage()

# ── Go-compat standalone color constants ──────────────────────────────────────

ColorAuto = ColorMode.AUTO
ColorAlways = ColorMode.ALWAYS
ColorNever = ColorMode.NEVER

Red = Color.RED
Green = Color.GREEN
Yellow = Color.YELLOW
Blue = Color.BLUE
Bold = Color.BOLD

__all__ = [
    # Types
    "Color",
    "ColorMode",
    "Command",
    "ExecResult",
    "FlagParseResult",
    "FlagParser",
    "Handler",
    "Invocation",
    "Runner",
    "RunnerFunc",
    # Go-compat type aliases
    "ExecOption",
    "ExecuteOption",
    "FlagParserOption",
    "ColorOption",
    # Go-compat sentinel errors
    "ErrEmptyCommand",
    "ErrOutputLimitExceeded",
    "ErrUsage",
    # Go-compat standalone color constants
    "ColorAuto",
    "ColorAlways",
    "ColorNever",
    "Red",
    "Green",
    "Yellow",
    "Blue",
    "Bold",
    # Core functions
    "colorize",
    "new_flag_parser",
    "output",
    "render_help",
    "run",
    "ExecRequest",
]

colorize = clix.colorize
output = clix.output
render_help = clix.render_help
run = clix.run
new_flag_parser = clix.new_flag_parser
