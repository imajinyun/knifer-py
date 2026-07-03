"""Shell-free process execution, ANSI coloring, and a small command tree.

Run external programs with :func:`run`/:func:`output` — argv is passed
directly to :func:`subprocess.run`, so a shell is never invoked and captured
output can be bounded with ``max_output_bytes``. Build a lightweight
subcommand tree with :class:`Command`, render deterministic usage text with
:func:`render_help`, and wrap strings in ANSI escapes with :func:`colorize`.

knifer-go's functional ``With*`` exec/execute/color options collapse into
keyword arguments; its injectable ``Runner``/``RunnerFunc`` and the imperative
``FlagParser`` wrapper around ``flag.FlagSet`` are intentionally omitted in
favor of the stdlib :mod:`subprocess` runner and an :mod:`argparse` parser
supplied through :attr:`Command.flags`. ``io.Reader``/``io.Writer`` streams
become ``str``/``bytes`` and :class:`~typing.TextIO`. Errors raise
:mod:`kniferpy.verr` types instead of returning sentinels.
"""

from __future__ import annotations

from kniferpy.internal import clix
from kniferpy.internal.clix import (
    Color,
    ColorMode,
    Command,
    ExecResult,
    Handler,
    Invocation,
)

__all__ = [
    "Color",
    "ColorMode",
    "Command",
    "ExecResult",
    "Handler",
    "Invocation",
    "colorize",
    "output",
    "render_help",
    "run",
]

colorize = clix.colorize
output = clix.output
render_help = clix.render_help
run = clix.run
