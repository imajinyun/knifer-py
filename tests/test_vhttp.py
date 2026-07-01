from pathlib import Path
from typing import Any

from kniferpy import vhttp
from kniferpy.verr import DecodeError, SecurityError


class FakeResponse:
    def __init__(self, text: str = "ok", content: bytes = b"ok") -> None:
        self.text = text
        self.content = content

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, response: FakeResponse | None = None) -> None:
        self.response = response or FakeResponse()
        self.called_with: str | None = None
        self.timeout: float | None = None
        self.post_payload: Any = None

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.called_with = url
        self.timeout = timeout
        return self.response

    def post(self, url: str, json: Any, timeout: float) -> FakeResponse:
        self.called_with = url
        self.post_payload = json
        self.timeout = timeout
        return self.response


def test_get_string_safe_uses_provider_and_timeout() -> None:
    session = FakeSession()

    body = vhttp.get_string_safe(
        "https://api.example.com/health",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
        timeout=1.0,
    )

    assert body == "ok"
    assert session.called_with == "https://api.example.com/health"
    assert session.timeout == 1.0


def test_get_string_safe_rejects_large_response() -> None:
    session = FakeSession(FakeResponse(text="hello", content=b"hello"))

    try:
        vhttp.get_string_safe(
            "https://api.example.com/health",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
            session=session,
            max_bytes=3,
        )
    except SecurityError as err:
        assert err.code == "http.response_too_large"
    else:
        raise AssertionError("expected SecurityError")


def test_get_bytes_safe_returns_content() -> None:
    session = FakeSession(FakeResponse(text="ignored", content=b"\x00\x01"))

    body = vhttp.get_bytes_safe(
        "https://api.example.com/file",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
    )

    assert body == b"\x00\x01"


def test_download_file_safe_writes_content(tmp_path: Path) -> None:
    session = FakeSession(FakeResponse(text="hello", content=b"hello"))
    target = tmp_path / "nested" / "download.txt"

    written = vhttp.download_file_safe(
        "https://api.example.com/file",
        target,
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
    )

    assert written == target
    assert target.read_bytes() == b"hello"


def test_get_json_safe_decodes_response() -> None:
    session = FakeSession(FakeResponse(text='{"ok": true}', content=b'{"ok": true}'))

    body = vhttp.get_json_safe(
        "https://api.example.com/status",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
    )

    assert body == {"ok": True}


def test_get_json_safe_wraps_decode_errors() -> None:
    session = FakeSession(FakeResponse(text="{bad", content=b"{bad"))

    try:
        vhttp.get_json_safe(
            "https://api.example.com/status",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
            session=session,
        )
    except DecodeError as err:
        assert err.code == "http.response_json_invalid"
    else:
        raise AssertionError("expected DecodeError")


def test_post_json_safe_returns_object() -> None:
    session = FakeSession(FakeResponse(text='{"ok": true}', content=b'{"ok": true}'))

    body = vhttp.post_json_safe(
        "https://api.example.com/create",
        {"name": "kniferpy"},
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
        session=session,
        timeout=2.0,
    )

    assert body == {"ok": True}
    assert session.called_with == "https://api.example.com/create"
    assert session.post_payload == {"name": "kniferpy"}
    assert session.timeout == 2.0


def test_post_json_safe_rejects_non_object_response() -> None:
    session = FakeSession(FakeResponse(text="[1]", content=b"[1]"))

    try:
        vhttp.post_json_safe(
            "https://api.example.com/create",
            {"name": "kniferpy"},
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
            session=session,
        )
    except SecurityError as err:
        assert err.code == "http.response_not_object"
    else:
        raise AssertionError("expected SecurityError")
