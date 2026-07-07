from __future__ import annotations

import builtins
import getpass
import io
import os
import socket
import sys
import tempfile
from types import TracebackType
from typing import Any

import pytest

from kniferpy import vsys
from kniferpy.internal import sysx


def test_get_os_info() -> None:
    info = vsys.get_os_info()
    assert info.name != ""
    assert info.arch != ""
    assert info.file_separator == os.sep
    assert info.path_separator == os.pathsep
    assert info.line_separator in ("\n", "\r\n")


def test_os_info_str() -> None:
    info = vsys.get_os_info()
    rendered = str(info)
    assert "OS Name:" in rendered
    assert "Path Separator:" in rendered


def test_get_host_info() -> None:
    info = vsys.get_host_info()
    # Address may be empty in sandboxed environments; it must never be loopback.
    assert not info.address.startswith("127.")


def test_host_info_str() -> None:
    assert "Host Name:" in str(vsys.get_host_info())


def test_get_user_info() -> None:
    info = vsys.get_user_info()
    # Directories end with a trailing separator when non-empty (matches Go).
    if info.home_dir:
        assert info.home_dir.endswith(os.sep)
    if info.current_dir:
        assert info.current_dir.endswith(os.sep)
    assert info.temp_dir.endswith(os.sep)


def test_user_info_locale(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANG", "zh_CN.UTF-8")
    monkeypatch.delenv("LC_ALL", raising=False)
    info = vsys.get_user_info()
    assert info.language == "zh"
    assert info.country == "CN"


def test_user_info_locale_fallback_to_lc_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.setenv("LC_ALL", "en_US.UTF-8")
    info = vsys.get_user_info()
    assert info.language == "en"
    assert info.country == "US"


def test_user_info_locale_language_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANG", "C")
    monkeypatch.delenv("LC_ALL", raising=False)
    info = vsys.get_user_info()
    assert info.language == "C"
    assert info.country == ""


def test_user_info_str() -> None:
    assert "User Name:" in str(vsys.get_user_info())


def test_get_current_pid() -> None:
    assert vsys.get_current_pid() == os.getpid()


def test_get_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNIFER_TEST_VAR", "hello")
    assert vsys.get("KNIFER_TEST_VAR") == "hello"


def test_get_missing_quiet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KNIFER_MISSING", raising=False)
    assert vsys.get("KNIFER_MISSING") == ""


def test_get_missing_warns(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("KNIFER_MISSING", raising=False)
    assert vsys.get("KNIFER_MISSING", quiet=False) == ""
    assert "not found" in capsys.readouterr().err


def test_get_or_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KNIFER_MISSING", raising=False)
    monkeypatch.setenv("KNIFER_EMPTY", "")
    monkeypatch.setenv("KNIFER_SET", "value")
    assert vsys.get_or_default("KNIFER_MISSING", "fallback") == "fallback"
    assert vsys.get_or_default("KNIFER_EMPTY", "fallback") == "fallback"
    assert vsys.get_or_default("KNIFER_SET", "fallback") == "value"


def test_get_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNIFER_INT", "42")
    monkeypatch.setenv("KNIFER_BAD_INT", "notanumber")
    monkeypatch.delenv("KNIFER_MISSING", raising=False)
    assert vsys.get_int("KNIFER_INT", 0) == 42
    assert vsys.get_int("KNIFER_BAD_INT", 7) == 7
    assert vsys.get_int("KNIFER_MISSING", 9) == 9


def test_get_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNIFER_TRUE", "true")
    monkeypatch.setenv("KNIFER_BAD_BOOL", "notabool")
    monkeypatch.delenv("KNIFER_MISSING", raising=False)
    assert vsys.get_bool("KNIFER_TRUE", False) is True
    assert vsys.get_bool("KNIFER_BAD_BOOL", True) is True
    assert vsys.get_bool("KNIFER_MISSING", True) is True


def test_os_version_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OSVERSION", "test-version-1.2.3")
    assert vsys.get_os_info().version == "test-version-1.2.3"


def test_os_info_predicates() -> None:
    assert vsys.OsInfo("Linux", "x86", "1", "/", "\n", ":").is_linux()
    mac = vsys.OsInfo("Darwin", "arm64", "1", "/", "\n", ":")
    assert mac.is_mac()
    assert mac.is_mac_os_x()
    assert vsys.OsInfo("Windows", "x86", "1", "\\", "\r\n", ";").is_windows()
    assert vsys.OsInfo("AIX", "x", "1", "/", "\n", ":").is_aix()
    assert vsys.OsInfo("SunOS", "x", "1", "/", "\n", ":").is_solaris()
    assert vsys.OsInfo("FreeBSD", "x", "1", "/", "\n", ":").is_freebsd()


def test_internal_path_locale_and_os_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    assert sysx._fix_path("") == ""
    assert sysx._fix_path(os.sep).endswith(os.sep)
    assert sysx._parse_locale("") == ("", "")
    assert sysx._parse_locale("zh_CN.UTF-8") == ("zh", "CN")
    assert sysx._parse_locale("C") == ("C", "")
    monkeypatch.delenv("OSVERSION", raising=False)
    monkeypatch.setenv("OSTYPE", "darwin-test")
    assert sysx._os_version() == "darwin-test"


def test_host_info_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSocket:
        def __enter__(self) -> FakeSocket:
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            return None

        def connect(self, addr: object) -> None:
            return None

        def getsockname(self) -> tuple[str, int]:
            return ("10.0.0.2", 12345)

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: FakeSocket())
    monkeypatch.setattr(socket, "gethostname", lambda: "host")
    assert sysx._first_non_loopback_ipv4() == "10.0.0.2"
    assert vsys.get_host_info() == vsys.HostInfo(name="host", address="10.0.0.2")

    class LoopbackSocket(FakeSocket):
        def getsockname(self) -> tuple[str, int]:
            return ("127.0.0.1", 12345)

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: LoopbackSocket())
    assert sysx._first_non_loopback_ipv4() == ""

    def fail_hostname() -> str:
        raise OSError("hostname failed")

    monkeypatch.setattr(socket, "gethostname", fail_hostname)
    assert vsys.get_host_info().name == ""


def test_user_info_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(getpass, "getuser", lambda: (_ for _ in ()).throw(KeyError()))
    monkeypatch.setenv("USER", "fallback-user")
    monkeypatch.setattr(os.path, "expanduser", lambda path: "~")
    monkeypatch.setenv("HOME", "/tmp/home")
    monkeypatch.setattr(os, "getcwd", lambda: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr(tempfile, "gettempdir", lambda: "/tmp")
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)

    info = vsys.get_user_info()

    assert info.name == "fallback-user"
    assert info.home_dir == f"/tmp/home{os.sep}"
    assert info.current_dir == ""
    assert info.temp_dir == f"/tmp{os.sep}"
    assert info.language == ""


def test_memory_runtime_and_python_info(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sysx, "_get_total_memory", lambda: 100)
    monkeypatch.setattr(sysx, "_get_free_memory", lambda: 40)
    monkeypatch.setattr(sysx, "get_total_thread_count", lambda: 7)
    runtime = vsys.RuntimeInfo(
        python_version="3.x",
        python_implementation="CPython",
        python_compiler="compiler",
        python_path=["."],
        prefix="/prefix",
        executable="/python",
    )

    assert runtime.get_total_memory() == 100
    assert runtime.get_free_memory() == 40
    assert runtime.get_max_memory() == 100
    assert runtime.get_usable_memory() == 60
    assert runtime.get_heap_inuse() == 60
    assert runtime.get_thread_count() == 7
    assert runtime.get_goroutine_count() == 7
    assert runtime.get_mem_stats()["thread_count"] == 7
    assert "Python Version:" in str(runtime)
    assert isinstance(runtime.refresh(), vsys.RuntimeInfo)

    assert vsys.get_total_memory() == 100
    assert vsys.get_free_memory() == 40
    assert vsys.get_max_memory() == 100
    assert vsys.total_memory() == 100
    assert vsys.free_memory() == 40
    assert vsys.max_memory() == 100
    assert vsys.total_goroutine_count() == 7
    assert vsys.get_goroutine_count() == 7
    assert vsys.get_runtime_info().executable == sys.executable
    py = vsys.new_python_info()
    assert py.executable == sys.executable
    assert "Python Version:" in str(py)


def test_memory_fallbacks_without_psutil(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "psutil":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert sysx._get_total_memory() == 0
    assert sysx._get_free_memory() == 0


def test_thread_count_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "threading":
            raise RuntimeError("boom")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert sysx.get_total_thread_count() == 0


def test_network_env_dump_and_readable_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = [
        (socket.AF_INET, None, None, None, ("127.0.0.1", 0)),
        (socket.AF_INET6, None, None, None, ("::1", 0)),
    ]
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: answers)
    assert vsys.get_ip_by_host("localhost") == ["127.0.0.1", "::1"]
    assert vsys.get_ip_by_host("bad") == ["127.0.0.1", "::1"]

    def raise_gaierror(*args: Any, **kwargs: Any) -> None:
        raise socket.gaierror()

    monkeypatch.setattr(socket, "getaddrinfo", raise_gaierror)
    assert vsys.get_ip_by_host("bad") == []
    assert vsys.get_multistage_reverse_proxy_ip({"X-Forwarded-For": "1.1.1.1, 2.2.2.2"}) == (
        "1.1.1.1"
    )
    assert vsys.get_multistage_reverse_proxy_ip({"X-Real-IP": "3.3.3.3"}) == "3.3.3.3"
    assert vsys.get_multistage_reverse_proxy_ip({"CF-Connecting-IP": "4.4.4.4"}) == "4.4.4.4"
    assert vsys.get_multistage_reverse_proxy_ip({}) == ""
    assert vsys.is_unknown("")
    assert vsys.is_unknown(" unknown ")
    assert not vsys.is_unknown("value")
    assert vsys.parse_cookies("") == {}
    assert vsys.parse_cookies("a=1; bad; b=2") == {"a": "1", "b": "2"}
    assert vsys.idn_to_ascii("例子.测试") == "xn--fsqu00a.xn--0zwm56d"
    assert sysx._readable_size(1) == "1 B"
    assert sysx._readable_size(2048) == "2.0 KB"
    assert "PB" in sysx._readable_size(2**60)
    assert isinstance(vsys.get_env_all(), dict)
    assert vsys.get_cpu_cores() >= 0
    output = vsys.dump_system_info()
    writer = io.StringIO()
    vsys.dump_system_info_to(writer)
    assert "=== System Info ===" in output
    assert writer.getvalue() == output


def test_cache_and_alias_accessors(monkeypatch: pytest.MonkeyPatch) -> None:
    vsys.reset_info_cache()
    host = vsys.HostInfo("cached-host", "1.1.1.1")
    os_info = vsys.OsInfo("Linux", "x86", "1", "/", "\n", ":")
    user = vsys.UserInfo("u", "/h/", "/c/", "/t/", "en", "US")
    runtime = vsys.RuntimeInfo("v", "impl", "compiler", [], "prefix", "exe")
    monkeypatch.setattr(sysx, "get_host_info", lambda: host)
    monkeypatch.setattr(sysx, "get_os_info", lambda: os_info)
    monkeypatch.setattr(sysx, "get_user_info", lambda: user)
    monkeypatch.setattr(sysx, "get_runtime_info", lambda: runtime)

    assert vsys.system_host_info() is host
    assert vsys.system_host_info() is host
    assert vsys.system_os_info() is os_info
    assert vsys.system_user_info() is user
    assert vsys.system_runtime_info() is runtime
    assert vsys.sys_host_info() is host
    assert vsys.sys_os_info() is os_info
    assert vsys.sys_user_info() is user
    assert vsys.sys_runtime_info() is runtime
    assert vsys.new_host_info() is host
    assert vsys.new_os_info() is os_info
    assert vsys.new_user_info() is user
    assert vsys.new_runtime_info() is runtime
    py = vsys.get_python_info()
    assert vsys.sys_python_info() is py
    assert vsys.get_python_info() is py
    vsys.reset_info_cache()
    assert vsys.get_python_info() is not py


def test_env_aliases_and_with_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNIFER_ENV", "123")
    monkeypatch.setenv("KNIFER_BOOL", "true")

    assert vsys.env("KNIFER_ENV") == "123"
    assert vsys.env_or_default("MISSING_ENV", "x") == "x"
    assert vsys.env_int("KNIFER_ENV", 0) == 123
    assert vsys.env_bool("KNIFER_BOOL", False) is True
    assert vsys.current_pid() == os.getpid()
    assert vsys.get_with_options("KNIFER_ENV") == "123"
    assert vsys.get_or_default_with_options("MISSING_ENV", "x") == "x"
    assert vsys.get_int_with_options("KNIFER_ENV", 0) == 123
    assert vsys.get_bool_with_options("KNIFER_BOOL", False) is True
    assert vsys.env_with_options("KNIFER_ENV") == "123"
    assert vsys.env_or_default_with_options("MISSING_ENV", "x") == "x"
    assert vsys.env_int_with_options("KNIFER_ENV", 0) == 123
    assert vsys.env_bool_with_options("KNIFER_BOOL", False) is True
    assert vsys.current_pid_with_options() == os.getpid()


def test_info_and_memory_with_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sysx, "_get_total_memory", lambda: 100)
    monkeypatch.setattr(sysx, "_get_free_memory", lambda: 40)
    monkeypatch.setattr(sysx, "get_total_thread_count", lambda: 7)
    vsys.reset_info_cache()

    assert isinstance(vsys.get_host_info_with_options(), vsys.HostInfo)
    assert isinstance(vsys.get_os_info_with_options(), vsys.OsInfo)
    assert isinstance(vsys.get_user_info_with_options(), vsys.UserInfo)
    assert isinstance(vsys.get_runtime_info_with_options(), vsys.RuntimeInfo)
    assert vsys.get_current_pid_with_options() == os.getpid()
    assert vsys.get_total_memory_with_options() == 100
    assert vsys.get_free_memory_with_options() == 40
    assert vsys.get_max_memory_with_options() == 100
    assert vsys.total_memory_with_options() == 100
    assert vsys.free_memory_with_options() == 40
    assert vsys.max_memory_with_options() == 100
    assert vsys.get_total_thread_count_with_options() == 7
    assert vsys.get_goroutine_count_with_options() == 7
    assert vsys.total_goroutine_count_with_options() == 7
    assert isinstance(vsys.sys_host_info_with_options(), vsys.HostInfo)
    assert isinstance(vsys.system_host_info_with_options(), vsys.HostInfo)
    assert isinstance(vsys.sys_os_info_with_options(), vsys.OsInfo)
    assert isinstance(vsys.system_os_info_with_options(), vsys.OsInfo)
    assert isinstance(vsys.sys_user_info_with_options(), vsys.UserInfo)
    assert isinstance(vsys.system_user_info_with_options(), vsys.UserInfo)
    assert isinstance(vsys.sys_runtime_info_with_options(), vsys.RuntimeInfo)
    assert isinstance(vsys.system_runtime_info_with_options(), vsys.RuntimeInfo)
    writer = io.StringIO()
    vsys.dump_system_info_with_options(writer)
    assert "=== System Info ===" in writer.getvalue()
    assert isinstance(vsys.new_host_info_with_options(), vsys.HostInfo)
    assert isinstance(vsys.new_os_info_with_options(), vsys.OsInfo)
    assert isinstance(vsys.new_user_info_with_options(), vsys.UserInfo)
    assert isinstance(vsys.new_runtime_info_with_options(), vsys.RuntimeInfo)
