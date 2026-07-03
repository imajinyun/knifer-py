from __future__ import annotations

import os

import pytest

from kniferpy import vsys


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
