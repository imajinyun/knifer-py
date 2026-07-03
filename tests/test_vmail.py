from __future__ import annotations

import email
from datetime import datetime, timezone
from email.message import Message as StdMessage
from pathlib import Path

import pytest

from kniferpy import vmail
from kniferpy.verr import KniferError, ValidationError

# --- Address ------------------------------------------------------------------


def test_new_address() -> None:
    addr = vmail.new_address("Kim", "kim@example.com")
    assert addr.name == "Kim"
    assert addr.email == "kim@example.com"
    assert str(addr) == "Kim <kim@example.com>"


def test_new_address_rejects_crlf() -> None:
    with pytest.raises(ValidationError):
        vmail.new_address("Kim\r\nBcc: evil@example.com", "kim@example.com")


def test_parse_address() -> None:
    addr = vmail.parse_address("Kim <kim@example.com>")
    assert addr.name == "Kim"
    assert addr.email == "kim@example.com"


def test_parse_address_bare() -> None:
    addr = vmail.parse_address("kim@example.com")
    assert addr.name == ""
    assert addr.email == "kim@example.com"


def test_parse_address_invalid() -> None:
    with pytest.raises(ValidationError):
        vmail.parse_address("not-an-address")


def test_parse_address_list() -> None:
    addrs = vmail.parse_address_list("a@example.com, Bob <b@example.com>")
    assert [a.email for a in addrs] == ["a@example.com", "b@example.com"]
    assert addrs[1].name == "Bob"


def test_parse_address_list_invalid() -> None:
    with pytest.raises(ValidationError):
        vmail.parse_address_list("a@example.com, broken")


# --- Attachment ---------------------------------------------------------------


def test_detect_content_type() -> None:
    assert vmail.detect_content_type("report.pdf") == "application/pdf"
    assert vmail.detect_content_type("noext") == vmail.TYPE_APPLICATION_OCTET_STREAM


def test_new_attachment_from_bytes() -> None:
    att = vmail.new_attachment("data.txt", b"hello")
    assert att.name == "data.txt"
    assert att.content_type == "text/plain"
    assert att.size == 5
    assert att.read() == b"hello"
    assert not att.is_inline


def test_new_attachment_strips_directory() -> None:
    att = vmail.new_attachment("/etc/passwd", b"x", "text/plain")
    assert att.name == "passwd"


def test_new_attachment_rejects_crlf_name() -> None:
    with pytest.raises(ValidationError):
        vmail.new_attachment("bad\r\nname.txt", b"x")


def test_new_inline_has_content_id() -> None:
    inline = vmail.new_inline("logo.png", "logo1", b"img", "image/png")
    assert inline.is_inline
    assert inline.content_id == "logo1"


def test_new_attachment_file(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_bytes(b"file-content")
    att = vmail.new_attachment_file(path)
    assert att.name == "doc.txt"
    assert att.size == len(b"file-content")
    assert att.read() == b"file-content"


def test_new_inline_file(tmp_path: Path) -> None:
    path = tmp_path / "pic.png"
    path.write_bytes(b"pngdata")
    inline = vmail.new_inline_file(path, "pic1")
    assert inline.is_inline
    assert inline.content_id == "pic1"
    assert inline.read() == b"pngdata"


def test_attachment_too_large() -> None:
    att = vmail.new_attachment("big.bin", b"0123456789")
    with pytest.raises(ValidationError):
        att.validate(max_bytes=5)


# --- Message construction / validation ----------------------------------------


def _basic_message(**overrides: object) -> vmail.Message:
    kwargs: dict[str, object] = {
        "from_": "from@example.com",
        "to": "to@example.com",
        "subject": "Hi",
        "text": "Hello",
    }
    kwargs.update(overrides)
    return vmail.new_message(**kwargs)  # type: ignore[arg-type]


def test_new_message_basic() -> None:
    msg = _basic_message()
    assert msg.from_.email == "from@example.com"
    assert msg.recipients() == ["to@example.com"]
    assert msg.sender() == "from@example.com"


def test_new_message_missing_body() -> None:
    with pytest.raises(ValidationError):
        vmail.new_message(from_="a@example.com", to="b@example.com")


def test_new_message_missing_recipient() -> None:
    with pytest.raises(ValidationError):
        vmail.new_message(from_="a@example.com", text="hi")


def test_new_message_subject_crlf() -> None:
    with pytest.raises(ValidationError):
        _basic_message(subject="Hi\r\nBcc: x@example.com")


def test_recipients_dedup_across_fields() -> None:
    msg = _basic_message(
        to="dup@example.com",
        cc="dup@example.com",
        bcc="other@example.com",
    )
    assert msg.recipients() == ["dup@example.com", "other@example.com"]


def test_envelope_from_overrides_sender() -> None:
    msg = _basic_message(envelope_from="bounce@example.com")
    assert msg.sender() == "bounce@example.com"


def test_headers_from_mapping() -> None:
    msg = _basic_message(headers={"X-Custom": "value", "X-Multi": ["a", "b"]})
    assert ("X-Custom", ("value",)) in msg.headers
    assert ("X-Multi", ("a", "b")) in msg.headers


def test_header_rejects_crlf_value() -> None:
    with pytest.raises(ValidationError):
        _basic_message(headers={"X-Bad": "line1\r\nline2"})


# --- Rendering ----------------------------------------------------------------


def _parse(msg: vmail.Message) -> StdMessage:
    return email.message_from_bytes(msg.to_bytes())


def test_render_plain_text() -> None:
    msg = _basic_message(date=datetime(2026, 7, 3, tzinfo=timezone.utc))
    parsed = _parse(msg)
    assert parsed["From"] == "from@example.com"
    assert parsed["To"] == "to@example.com"
    assert parsed["Subject"] == "Hi"
    assert parsed["MIME-Version"] == "1.0"
    assert parsed.get_content_type() == "text/plain"


def test_render_multipart_alternative() -> None:
    msg = _basic_message(html="<p>Hello</p>")
    parsed = _parse(msg)
    assert parsed.get_content_type() == "multipart/alternative"
    subtypes = {p.get_content_type() for p in parsed.walk()}
    assert "text/plain" in subtypes
    assert "text/html" in subtypes


def test_render_with_attachment_is_mixed() -> None:
    msg = _basic_message(attachments=[vmail.new_attachment("a.txt", b"data")])
    parsed = _parse(msg)
    assert parsed.get_content_type() == "multipart/mixed"
    attachments = [p for p in parsed.walk() if p.get_content_disposition() == "attachment"]
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "a.txt"
    assert attachments[0].get_payload(decode=True) == b"data"


def test_render_with_inline_has_content_id() -> None:
    msg = _basic_message(
        html="<img src=cid:logo1>",
        inlines=[vmail.new_inline("logo.png", "logo1", b"img", "image/png")],
    )
    parsed = _parse(msg)
    cids = [p["Content-ID"] for p in parsed.walk() if p["Content-ID"]]
    assert "<logo1>" in cids


def test_render_reply_to_and_message_id() -> None:
    msg = _basic_message(reply_to="reply@example.com", message_id="abc123")
    parsed = _parse(msg)
    assert parsed["Reply-To"] == "reply@example.com"
    assert parsed["Message-ID"] == "<abc123>"


# --- Client / delivery --------------------------------------------------------


class _FakeSMTP:
    """Records sendmail calls without touching the network."""

    instances: list[_FakeSMTP] = []

    def __init__(self, host: str, port: int, **kwargs: object) -> None:
        self.host = host
        self.port = port
        self.kwargs = kwargs
        self.sent: list[tuple[str, list[str], bytes]] = []
        self.started_tls = False
        self.logged_in: tuple[str, str] | None = None
        self._extns = {"starttls"}
        self.quit_called = False
        _FakeSMTP.instances.append(self)

    def ehlo(self, name: object = None) -> None:  # noqa: ARG002
        pass

    def has_extn(self, name: str) -> bool:
        return name in self._extns

    def starttls(self, context: object = None) -> None:  # noqa: ARG002
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.logged_in = (username, password)

    def sendmail(self, sender: str, recipients: list[str], data: bytes) -> None:
        self.sent.append((sender, recipients, data))

    def quit(self) -> None:
        self.quit_called = True

    def close(self) -> None:
        pass


@pytest.fixture
def fake_smtp(monkeypatch: pytest.MonkeyPatch) -> type[_FakeSMTP]:
    _FakeSMTP.instances = []
    monkeypatch.setattr("smtplib.SMTP", _FakeSMTP)
    monkeypatch.setattr("smtplib.SMTP_SSL", _FakeSMTP)
    return _FakeSMTP


def test_client_send_uses_starttls(fake_smtp: type[_FakeSMTP]) -> None:
    client = vmail.Client(vmail.Config(host="smtp.example.com", port=587))
    client.send(_basic_message())
    conn = fake_smtp.instances[0]
    assert conn.started_tls
    assert conn.quit_called
    assert conn.sent[0][0] == "from@example.com"
    assert conn.sent[0][1] == ["to@example.com"]


def test_client_send_with_auth(fake_smtp: type[_FakeSMTP]) -> None:
    client = vmail.Client(
        vmail.Config(host="smtp.example.com", port=587, username="u", password="p")
    )
    client.send(_basic_message())
    assert fake_smtp.instances[0].logged_in == ("u", "p")


def test_mandatory_starttls_without_support_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _NoStartTLS(_FakeSMTP):
        def __init__(self, host: str, port: int, **kwargs: object) -> None:
            super().__init__(host, port, **kwargs)
            self._extns = set()

    _FakeSMTP.instances = []
    monkeypatch.setattr("smtplib.SMTP", _NoStartTLS)
    client = vmail.Client(vmail.Config(host="smtp.example.com", port=25))
    with pytest.raises(KniferError):
        client.send(_basic_message())


def test_plain_auth_refused_without_tls(fake_smtp: type[_FakeSMTP]) -> None:
    client = vmail.Client(
        vmail.Config(
            host="smtp.example.com",
            port=25,
            username="u",
            password="p",
            tls_policy=vmail.TLSPolicy.NONE,
        )
    )
    with pytest.raises(KniferError):
        client.send(_basic_message())


def test_plain_auth_allowed_when_opted_in(fake_smtp: type[_FakeSMTP]) -> None:
    client = vmail.Client(
        vmail.Config(
            host="smtp.example.com",
            port=25,
            username="u",
            password="p",
            tls_policy=vmail.TLSPolicy.NONE,
            allow_plain_auth=True,
        )
    )
    client.send(_basic_message())
    assert fake_smtp.instances[0].logged_in == ("u", "p")


def test_implicit_tls_uses_ssl(fake_smtp: type[_FakeSMTP]) -> None:
    client = vmail.Client(
        vmail.Config(
            host="smtp.example.com", port=465, tls_policy=vmail.TLSPolicy.IMPLICIT
        )
    )
    client.send(_basic_message())
    assert fake_smtp.instances[0].port == 465


def test_client_rejects_bad_address() -> None:
    with pytest.raises(ValidationError):
        vmail.Client(vmail.Config(host="", port=587))


# --- Module helpers -----------------------------------------------------------


def test_send_text(fake_smtp: type[_FakeSMTP]) -> None:
    vmail.send_text(
        "smtp.example.com", 587, "from@example.com", "to@example.com", "Hi", "body"
    )
    data = fake_smtp.instances[0].sent[0][2]
    assert b"body" in data


def test_send_html(fake_smtp: type[_FakeSMTP]) -> None:
    vmail.send_html(
        "smtp.example.com", 587, "from@example.com", "to@example.com", "Hi", "<p>hi</p>"
    )
    parsed = email.message_from_bytes(fake_smtp.instances[0].sent[0][2])
    assert parsed.get_content_type() == "text/html"


def test_quick_send_with_account_defaults(fake_smtp: type[_FakeSMTP]) -> None:
    account = vmail.Account(
        host="smtp.example.com",
        port=587,
        username="user@example.com",
        password="secret",
        from_name="Robot",
    )
    vmail.quick_send(account, to="to@example.com", subject="S", text="T")
    conn = fake_smtp.instances[0]
    assert conn.logged_in == ("user@example.com", "secret")
    parsed = email.message_from_bytes(conn.sent[0][2])
    assert parsed["From"] == "Robot <user@example.com>"


def test_account_without_from_raises() -> None:
    account = vmail.Account(host="smtp.example.com", port=587)
    with pytest.raises(ValidationError):
        vmail.quick_send(account, to="to@example.com", text="hi")


def test_send_account_text(fake_smtp: type[_FakeSMTP]) -> None:
    account = vmail.Account(
        host="smtp.example.com", port=587, from_="from@example.com"
    )
    vmail.send_account_text(account, "to@example.com", "Subject", "text body")
    assert fake_smtp.instances[0].sent[0][0] == "from@example.com"
