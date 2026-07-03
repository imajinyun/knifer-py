from __future__ import annotations

import argparse
import sys
from io import StringIO
from pathlib import Path

import pytest

from kniferpy import vcli
from kniferpy.verr import KniferError, ValidationError

# --- run / output -------------------------------------------------------------


def test_run_captures_stdout() -> None:
    result = vcli.run(sys.executable, ["-c", "print('hello')"])
    assert result.stdout.strip() == "hello"
    assert result.exit_code == 0
    assert result.duration >= 0.0


def test_run_captures_stderr_and_exit_code() -> None:
    result = vcli.run(sys.executable, ["-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"])
    assert result.stderr.strip() == "boom"
    assert result.exit_code == 3


def test_run_empty_command_raises() -> None:
    with pytest.raises(ValidationError):
        vcli.run("")


def test_run_command_not_found_raises() -> None:
    with pytest.raises(ValidationError):
        vcli.run("knifer-nonexistent-binary-xyz")


def test_run_with_stdin() -> None:
    result = vcli.run(
        sys.executable,
        ["-c", "import sys; sys.stdout.write(sys.stdin.read().upper())"],
        stdin="abc",
    )
    assert result.stdout == "ABC"


def test_run_with_env() -> None:
    result = vcli.run(
        sys.executable,
        ["-c", "import os; print(os.environ['KNIFER_TEST'])"],
        env={"KNIFER_TEST": "42"},
    )
    assert result.stdout.strip() == "42"


def test_run_with_dir(tmp_path: Path) -> None:
    result = vcli.run(sys.executable, ["-c", "import os; print(os.getcwd())"], dir=tmp_path)
    assert str(tmp_path) in result.stdout


def test_run_max_output_bytes_exceeded() -> None:
    with pytest.raises(KniferError):
        vcli.run(
            sys.executable,
            ["-c", "print('x' * 1000)"],
            max_output_bytes=10,
        )


def test_run_timeout() -> None:
    with pytest.raises(KniferError):
        vcli.run(
            sys.executable,
            ["-c", "import time; time.sleep(5)"],
            timeout=0.2,
        )


def test_output_returns_stdout() -> None:
    assert vcli.output(sys.executable, ["-c", "print('out')"]).strip() == "out"


# --- colorize -----------------------------------------------------------------


def test_colorize_always() -> None:
    assert vcli.colorize("hi", vcli.Color.RED, mode=vcli.ColorMode.ALWAYS) == "\x1b[31mhi\x1b[0m"


def test_colorize_auto_is_plain() -> None:
    assert vcli.colorize("hi", vcli.Color.RED) == "hi"


def test_colorize_never_is_plain() -> None:
    assert vcli.colorize("hi", vcli.Color.GREEN, mode=vcli.ColorMode.NEVER) == "hi"


def test_colorize_empty_color_is_plain() -> None:
    assert vcli.colorize("hi", "", mode=vcli.ColorMode.ALWAYS) == "hi"


# --- render_help --------------------------------------------------------------


def test_render_help_basic() -> None:
    cmd = vcli.Command(name="tool", summary="Does things")
    help_text = vcli.render_help(cmd)
    assert "Usage: tool" in help_text
    assert "Does things" in help_text


def test_render_help_with_children() -> None:
    root = vcli.Command(name="tool")
    root.add(
        vcli.Command(name="build", summary="Build it"),
        vcli.Command(name="test", summary="Test it"),
    )
    help_text = vcli.render_help(root)
    assert "Usage: tool <command>" in help_text
    assert "Commands:" in help_text
    assert "build" in help_text
    assert "test" in help_text


def test_render_help_none() -> None:
    assert vcli.render_help(None) == ""


def test_render_help_colorized() -> None:
    cmd = vcli.Command(name="tool")
    assert "\x1b[1m" in vcli.render_help(cmd, mode=vcli.ColorMode.ALWAYS)


# --- Command execution --------------------------------------------------------


def _streams() -> tuple[StringIO, StringIO]:
    return StringIO(), StringIO()


def test_execute_runs_handler() -> None:
    seen: dict[str, object] = {}

    def handler(inv: vcli.Invocation) -> int:
        seen["args"] = inv.args
        inv.stdout.write("ran")
        return 0

    cmd = vcli.Command(name="tool", run=handler)
    out, err = _streams()
    code = cmd.execute(["a", "b"], stdout=out, stderr=err)
    assert code == 0
    assert seen["args"] == ["a", "b"]
    assert out.getvalue() == "ran"


def test_execute_routes_to_subcommand() -> None:
    def build(inv: vcli.Invocation) -> int:
        inv.stdout.write("built")
        return 0

    root = vcli.Command(name="tool")
    root.add(vcli.Command(name="build", run=build))
    out, err = _streams()
    code = root.execute(["build"], stdout=out, stderr=err)
    assert code == 0
    assert out.getvalue() == "built"


def test_execute_unknown_subcommand_raises() -> None:
    root = vcli.Command(name="tool")
    root.add(vcli.Command(name="build", run=lambda inv: 0))
    out, err = _streams()
    with pytest.raises(ValidationError):
        root.execute(["deploy"], stdout=out, stderr=err)


def test_execute_no_handler_prints_help() -> None:
    root = vcli.Command(name="tool", summary="Root")
    out, err = _streams()
    code = root.execute([], stdout=out, stderr=err)
    assert code == 0
    assert "Usage: tool" in out.getvalue()


def test_execute_unexpected_args_without_handler_raises() -> None:
    cmd = vcli.Command(name="tool")
    out, err = _streams()
    with pytest.raises(ValidationError):
        cmd.execute(["extra"], stdout=out, stderr=err)


def test_execute_parses_flags() -> None:
    captured: dict[str, object] = {}

    def flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--name", default="world")
        parser.add_argument("--count", type=int, default=1)

    def handler(inv: vcli.Invocation) -> int:
        captured.update(inv.options)
        return 0

    cmd = vcli.Command(name="greet", flags=flags, run=handler)
    out, err = _streams()
    cmd.execute(["--name", "kim", "--count", "3", "extra"], stdout=out, stderr=err)
    assert captured["name"] == "kim"
    assert captured["count"] == 3


def test_execute_invalid_flag_raises() -> None:
    def flags(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--count", type=int)

    cmd = vcli.Command(name="tool", flags=flags, run=lambda inv: 0)
    out, err = _streams()
    with pytest.raises(ValidationError):
        cmd.execute(["--count", "notanumber"], stdout=out, stderr=err)


def test_execute_handler_none_return_is_zero() -> None:
    cmd = vcli.Command(name="tool", run=lambda inv: None)
    out, err = _streams()
    assert cmd.execute([], stdout=out, stderr=err) == 0


def test_execute_handler_returns_exit_code() -> None:
    cmd = vcli.Command(name="tool", run=lambda inv: 7)
    out, err = _streams()
    assert cmd.execute([], stdout=out, stderr=err) == 7
