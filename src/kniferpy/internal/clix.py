from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from io import StringIO
from typing import Protocol, TextIO

from kniferpy.verr import KniferError, ValidationError

# --- Runner injection ---------------------------------------------------------


class Runner(Protocol):
    """Pluggable process runner for testing and mocking."""

    def __call__(
        self,
        name: str,
        args: Sequence[str] | None,
        *,
        dir: str | os.PathLike[str] | None,
        env: Mapping[str, str] | None,
        stdin: str | bytes | None,
        max_output_bytes: int,
        timeout: float | None,
    ) -> ExecResult: ...


RunnerFunc = Callable[
    [
        str,
        Sequence[str] | None,
        str | os.PathLike[str] | None,
        Mapping[str, str] | None,
        str | bytes | None,
        int,
        float | None,
    ],
    "ExecResult",
]

# --- Errors -------------------------------------------------------------------


def _empty_command() -> ValidationError:
    return ValidationError(message="cli: empty command", code="knifer.cli.empty_command")


def _output_limit_exceeded() -> KniferError:
    return KniferError(
        message="cli: output limit exceeded", code="knifer.cli.output_limit_exceeded"
    )


def _usage(detail: str = "") -> ValidationError:
    message = "cli: usage error"
    if detail:
        message = f"{message}: {detail}"
    return ValidationError(message=message, code="knifer.cli.usage")


# --- Process execution --------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecResult:
    """Captured process output and exit metadata."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration: float = 0.0


def _limit_result(result: ExecResult, max_bytes: int) -> tuple[ExecResult, bool]:
    """Return the result truncated to ``max_bytes`` and whether it overflowed."""
    if max_bytes <= 0:
        return result, False
    stdout = result.stdout.encode()
    stderr = result.stderr.encode()
    if len(stdout) > max_bytes:
        truncated = ExecResult(
            stdout=stdout[:max_bytes].decode(errors="ignore"),
            stderr="",
            exit_code=result.exit_code,
            duration=result.duration,
        )
        return truncated, True
    remaining = max_bytes - len(stdout)
    if len(stderr) > remaining:
        truncated = ExecResult(
            stdout=result.stdout,
            stderr=stderr[:remaining].decode(errors="ignore"),
            exit_code=result.exit_code,
            duration=result.duration,
        )
        return truncated, True
    return result, False


def _default_runner(
    name: str,
    args: Sequence[str] | None,
    *,
    dir: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    stdin: str | bytes | None = None,
    max_output_bytes: int = 0,
    timeout: float | None = None,
) -> ExecResult:
    """Default process runner using ``subprocess.run``."""
    argv = [name, *(args or ())]
    child_env: dict[str, str] | None = None
    if env is not None:
        child_env = {**os.environ, **env}
    input_bytes: bytes | None = None
    if stdin is not None:
        input_bytes = stdin.encode() if isinstance(stdin, str) else stdin

    started = time.monotonic()
    try:
        completed = subprocess.run(  # noqa: S603 - explicit argv, never a shell
            argv,
            cwd=os.fspath(dir) if dir is not None else None,
            env=child_env,
            input=input_bytes,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValidationError(
            message=f"cli: run {name!r}: command not found",
            code="knifer.cli.not_found",
            context={"cause": str(exc)},
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise KniferError(
            message=f"cli: run {name!r}: timed out",
            code="knifer.cli.timeout",
            context={"cause": str(exc)},
        ) from exc
    duration = time.monotonic() - started

    return ExecResult(
        stdout=completed.stdout.decode(errors="replace"),
        stderr=completed.stderr.decode(errors="replace"),
        exit_code=completed.returncode,
        duration=duration,
    )


def run(
    name: str,
    args: Sequence[str] | None = None,
    *,
    dir: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    stdin: str | bytes | None = None,
    max_output_bytes: int = 0,
    timeout: float | None = None,
    runner: Runner | None = None,
) -> ExecResult:
    """Execute ``name`` with ``args`` without invoking a shell.

    Environment entries in ``env`` are layered on top of the current process
    environment. stdout/stderr are captured and optionally truncated to
    ``max_output_bytes``; exceeding the limit raises
    :class:`~kniferpy.verr.KniferError`.

    Pass a ``runner`` callable to replace the default ``subprocess.run``
    backend (useful for testing).
    """
    if not name:
        raise _empty_command()
    r = runner if runner is not None else _default_runner
    result = r(
        name,
        args,
        dir=dir,
        env=env,
        stdin=stdin,
        max_output_bytes=max_output_bytes,
        timeout=timeout,
    )
    limited, overflowed = _limit_result(result, max_output_bytes)
    if overflowed:
        raise _output_limit_exceeded()
    return limited


def output(
    name: str,
    args: Sequence[str] | None = None,
    *,
    dir: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
    stdin: str | bytes | None = None,
    max_output_bytes: int = 0,
    timeout: float | None = None,
    runner: Runner | None = None,
) -> str:
    """Execute ``name`` with ``args`` and return captured stdout."""
    return run(
        name,
        args,
        dir=dir,
        env=env,
        stdin=stdin,
        max_output_bytes=max_output_bytes,
        timeout=timeout,
        runner=runner,
    ).stdout


# --- ANSI color ---------------------------------------------------------------


class ColorMode(Enum):
    """Controls ANSI color output."""

    AUTO = 0
    ALWAYS = 1
    NEVER = 2


class Color(StrEnum):
    """Supported ANSI foreground colors and text attributes."""

    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    BOLD = "1"


def colorize(text: str, color: Color | str, *, mode: ColorMode = ColorMode.AUTO) -> str:
    """Wrap ``text`` in ANSI escape codes when ``mode`` is :attr:`ColorMode.ALWAYS`."""
    code = str(color)
    if mode is not ColorMode.ALWAYS or not code:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


# --- Command tree -------------------------------------------------------------


# A handler receives the resolved invocation and may return an exit code.
Handler = Callable[["Invocation"], "int | None"]


@dataclass(slots=True)
class Command:
    """A lightweight command or subcommand.

    ``flags`` receives the command's :class:`argparse.ArgumentParser` so the
    caller can declare options; parsed values are exposed on
    :attr:`Invocation.options`.
    """

    name: str
    summary: str = ""
    usage: str = ""
    flags: Callable[[argparse.ArgumentParser], None] | None = None
    run: Handler | None = None
    children: list[Command] = field(default_factory=list)

    def add(self, *children: Command) -> None:
        """Append subcommands to this command."""
        for child in children:
            if child is not None:
                self.children.append(child)

    def execute(
        self,
        args: Sequence[str],
        *,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> int:
        """Route ``args`` to this command or one of its subcommands."""
        out = stdout if stdout is not None else sys.stdout
        err = stderr if stderr is not None else sys.stderr
        return _execute(self, list(args), out, err)


@dataclass(slots=True)
class Invocation:
    """Parsed arguments and command I/O streams passed to a :class:`Command` handler."""

    command: Command
    args: list[str]
    options: Mapping[str, object]
    stdout: TextIO
    stderr: TextIO


def _build_parser(cmd: Command) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=cmd.name, add_help=False, allow_abbrev=False)
    if cmd.flags is not None:
        cmd.flags(parser)
    return parser


def _execute(cmd: Command, args: list[str], stdout: TextIO, stderr: TextIO) -> int:
    if cmd is None or not cmd.name:
        raise _usage("empty command")
    if args:
        for child in cmd.children:
            if child is not None and child.name == args[0]:
                return _execute(child, args[1:], stdout, stderr)
        if cmd.children and cmd.run is None:
            raise _usage(f"unknown command {args[0]!r}")

    parser = _build_parser(cmd)
    try:
        namespace, positionals = parser.parse_known_args(args)
    except SystemExit as exc:  # argparse aborts on invalid flags
        raise _usage(f"invalid arguments for {cmd.name!r}") from exc

    if cmd.run is None and positionals:
        raise _usage(f"unexpected arguments for {cmd.name!r}")
    if cmd.run is None:
        stdout.write(render_help(cmd))
        return 0

    invocation = Invocation(
        command=cmd,
        args=positionals,
        options=vars(namespace),
        stdout=stdout,
        stderr=stderr,
    )
    code = cmd.run(invocation)
    return code if code is not None else 0


def render_help(cmd: Command | None, *, mode: ColorMode = ColorMode.AUTO) -> str:
    """Return deterministic help text for ``cmd``."""
    if cmd is None:
        return ""
    usage = cmd.usage
    if not usage:
        usage = cmd.name
        if cmd.children:
            usage += " <command>"
    buf = StringIO()
    buf.write(colorize("Usage:", Color.BOLD, mode=mode))
    buf.write(" ")
    buf.write(usage)
    buf.write("\n")
    if cmd.summary:
        buf.write("\n")
        buf.write(cmd.summary)
        buf.write("\n")
    if cmd.children:
        buf.write("\nCommands:\n")
        for child in cmd.children:
            if child is None:
                continue
            buf.write("  ")
            buf.write(child.name)
            if child.summary:
                buf.write("\t")
                buf.write(child.summary)
            buf.write("\n")
    return buf.getvalue()


# ── FlagParser: standalone reusable flag parser ──────────────────────────────


@dataclass(frozen=True, slots=True)
class FlagParseResult:
    """Result of a flag parse: unknown args and any error."""

    args: list[str]
    error: Exception | None = None


class FlagParser:
    """Standalone reusable flag parser wrapping argparse.ArgumentParser.

    Provides deterministic error handling (no sys.exit on parse failure)
    and a Go-compatible ``parse`` method that returns a ``FlagParseResult``.
    """

    __slots__ = ("_parser", "_name", "_output")

    def __init__(
        self,
        name: str,
        *,
        output: TextIO | None = None,
    ) -> None:
        self._name = name
        self._output = output
        self._parser = argparse.ArgumentParser(
            prog=name,
            add_help=True,
            exit_on_error=False,
        )

    def parse(self, args: list[str] | None = None) -> FlagParseResult:
        """Parse ``args`` (or sys.argv[1:] if None) and return a result."""
        if args is None:
            args = sys.argv[1:]
        try:
            known, unknown = self._parser.parse_known_args(args)
            return FlagParseResult(args=unknown)
        except SystemExit as e:
            return FlagParseResult(
                args=[],
                error=ValidationError(
                    str(e) or "flag parsing error",
                    code="cli.flag_parse_error",
                ),
            )
        except Exception as e:
            return FlagParseResult(args=[], error=e)

    def add_argument(self, *args: str, **kwargs: object) -> None:
        """Add a command-line argument (delegates to argparse)."""
        self._parser.add_argument(*args, **kwargs)

    def add_flag(self, *flags: str, **kwargs: object) -> None:
        """Add a boolean flag (delegates to argparse)."""
        self._parser.add_argument(*flags, action="store_true", **kwargs)

    def print_usage(self) -> None:
        """Print usage to output (or stderr)."""
        output = self._output or sys.stderr
        self._parser.print_usage(file=output)

    def print_help(self) -> None:
        """Print help to output (or stderr)."""
        output = self._output or sys.stderr
        self._parser.print_help(file=output)

    # ── Go-compat typed flag registration ────────────────────────────────────

    def string(self, name: str, value: str, usage: str) -> str:
        """Register a string flag and return the default value (Go compat)."""
        self._parser.add_argument(f"--{name}", default=value, type=str, help=usage)
        return value

    def int(self, name: str, value: int, usage: str) -> int:
        """Register an int flag and return the default value (Go compat)."""
        self._parser.add_argument(f"--{name}", default=value, type=int, help=usage)
        return value

    def bool(self, name: str, value: bool, usage: str) -> bool:
        """Register a bool flag and return the default value (Go compat)."""
        if value:
            self._parser.add_argument(f"--{name}", default=value, type=bool, help=usage)
        else:
            self._parser.add_argument(f"--{name}", action="store_true", help=usage)
        return value

    def duration(self, name: str, value: str, usage: str) -> str:
        """Register a duration flag and return the default value (Go compat).

        Duration values are stored as ISO 8601 strings (e.g. ``"1h30m"``).
        """
        self._parser.add_argument(f"--{name}", default=value, type=str, help=usage)
        return value

    def usage(self) -> None:
        """Print defaults to configured output (Go compat)."""
        self.print_help()


def new_flag_parser(name: str, *, output: TextIO | None = None) -> FlagParser:
    """Create a standalone flag parser."""
    return FlagParser(name, output=output)
