from __future__ import annotations

import contextlib
import mimetypes
import smtplib
import ssl
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from email.message import EmailMessage
from email.utils import format_datetime, formataddr, getaddresses, parseaddr
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any, cast

from kniferpy.verr import KniferError, ValidationError

DEFAULT_MAX_ATTACHMENT_BYTES = 25 << 20
DEFAULT_TIMEOUT = 10.0
DEFAULT_LOCAL_NAME = "localhost"

CHARSET_UTF8 = "utf-8"
CHARSET_ASCII = "us-ascii"

TYPE_TEXT_PLAIN = "text/plain"
TYPE_TEXT_HTML = "text/html"
TYPE_APPLICATION_OCTET_STREAM = "application/octet-stream"


class Encoding(StrEnum):
    """Content-Transfer-Encoding used for text parts."""

    BASE64 = "base64"
    QUOTED_PRINTABLE = "quoted-printable"
    SEVEN_BIT = "7bit"
    EIGHT_BIT = "8bit"


class TLSPolicy(Enum):
    """Controls SMTP transport security."""

    UNKNOWN = 0
    MANDATORY_STARTTLS = 1
    IMPLICIT = 2
    OPPORTUNISTIC_STARTTLS = 3
    NONE = 4


# --- Errors -------------------------------------------------------------------


def _invalid_address(detail: str = "") -> ValidationError:
    message = "mail: invalid address"
    if detail:
        message = f"{message}: {detail}"
    return ValidationError(message=message, code="knifer.mail.invalid_address")


def _invalid_header(detail: str = "") -> ValidationError:
    message = "mail: invalid header"
    if detail:
        message = f"{message}: {detail}"
    return ValidationError(message=message, code="knifer.mail.invalid_header")


def _missing_from() -> ValidationError:
    return ValidationError(message="mail: missing from address", code="knifer.mail.missing_from")


def _missing_recipient() -> ValidationError:
    return ValidationError(
        message="mail: missing recipient", code="knifer.mail.missing_recipient"
    )


def _missing_body() -> ValidationError:
    return ValidationError(message="mail: missing body", code="knifer.mail.missing_body")


def _tls_required() -> KniferError:
    return KniferError(message="mail: tls required", code="knifer.mail.tls_required")


def _plain_auth() -> KniferError:
    return KniferError(
        message="mail: plaintext auth disabled", code="knifer.mail.plain_auth"
    )


def _attachment_too_large() -> ValidationError:
    return ValidationError(
        message="mail: attachment too large", code="knifer.mail.attachment_too_large"
    )


# --- Validation helpers -------------------------------------------------------


def _has_crlf(value: str) -> bool:
    return "\r" in value or "\n" in value


def _validate_email(email: str) -> str:
    email = email.strip()
    if not email or _has_crlf(email) or " " in email:
        raise _invalid_address(email)
    name, addr = parseaddr(email)
    if name or addr != email:
        raise _invalid_address(email)
    local, sep, domain = addr.rpartition("@")
    if not sep or not local or not domain:
        raise _invalid_address(email)
    return addr


# --- Address ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Address:
    """An RFC 5322 mailbox address."""

    name: str
    email: str

    def __str__(self) -> str:
        return formataddr((self.name, self.email))


def new_address(name: str, email: str) -> Address:
    if _has_crlf(name):
        raise _invalid_address("name contains CR/LF")
    return Address(name=name, email=_validate_email(email))


def parse_address(value: str) -> Address:
    if _has_crlf(value):
        raise _invalid_address(value)
    name, addr = parseaddr(value.strip())
    if not addr:
        raise _invalid_address(value)
    return Address(name=name, email=_validate_email(addr))


def parse_address_list(value: str) -> list[Address]:
    if _has_crlf(value):
        raise _invalid_address(value)
    parsed = getaddresses([value.strip()])
    if not parsed:
        raise _invalid_address(value)
    addresses: list[Address] = []
    for name, addr in parsed:
        if not addr:
            raise _invalid_address(value)
        addresses.append(Address(name=name, email=_validate_email(addr)))
    return addresses


AddressInput = str | Address | Iterable["str | Address"]


def _coerce_address(value: str | Address) -> Address:
    if isinstance(value, Address):
        return new_address(value.name, value.email)
    return parse_address(value)


def _coerce_addresses(value: AddressInput | None) -> tuple[Address, ...]:
    if value is None:
        return ()
    if isinstance(value, Address):
        return (new_address(value.name, value.email),)
    if isinstance(value, str):
        return tuple(parse_address_list(value))
    out: list[Address] = []
    for item in value:
        if isinstance(item, Address):
            out.append(new_address(item.name, item.email))
        elif isinstance(item, str):
            out.extend(parse_address_list(item))
        else:  # pragma: no cover - defensive
            raise _invalid_address(f"unsupported address type {type(item).__name__}")
    return tuple(out)


# --- Attachment ---------------------------------------------------------------


def detect_content_type(name: str) -> str:
    guessed, _ = mimetypes.guess_type(name)
    return guessed or TYPE_APPLICATION_OCTET_STREAM


def _split_content_type(content_type: str) -> tuple[str, str]:
    main, sep, sub = content_type.partition("/")
    if not sep or not main.strip() or not sub.strip():
        return "application", "octet-stream"
    return main.strip(), sub.strip()


class Header:
    """Ordered email header collection with inspection and mutation.

    Headers are stored as (name, values) tuples. Duplicate names are allowed;
    each ``Add`` call appends a new entry.
    """

    __slots__ = ("_entries",)

    def __init__(self) -> None:
        self._entries: list[tuple[str, tuple[str, ...]]] = []

    def add(self, name: str, *values: str) -> None:
        if _has_crlf(name) or any(_has_crlf(v) for v in values):
            raise _invalid_header(name)
        self._entries.append((name, values))

    def set(self, name: str, *values: str) -> None:
        if _has_crlf(name) or any(_has_crlf(v) for v in values):
            raise _invalid_header(name)
        # Remove existing entries with the same name, then add.
        self._entries = [(n, v) for n, v in self._entries if n != name]
        self._entries.append((name, values))

    def values(self, name: str) -> list[str]:
        result: list[str] = []
        for n, v in self._entries:
            if n == name:
                result.extend(v)
        return result

    def to_tuples(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return tuple(self._entries)


def new_header() -> Header:
    """Create a new Header."""
    return Header()


@dataclass(frozen=True, slots=True)
class Attachment:
    """A MIME file part loaded from bytes or lazily from a filesystem path."""

    name: str
    content_type: str
    size: int
    content_id: str = ""
    is_inline: bool = False
    _data: bytes | None = field(default=None, repr=False)
    _path: Path | None = field(default=None, repr=False)

    def read(self) -> bytes:
        if self._data is not None:
            return self._data
        if self._path is not None:
            return self._path.read_bytes()
        raise _invalid_header("attachment has no content")

    def validate(self, max_bytes: int) -> None:
        if not self.name.strip() or _has_crlf(self.name) or _has_crlf(self.content_id):
            raise _invalid_header(self.name)
        if max_bytes > 0 and self.size > max_bytes:
            raise _attachment_too_large()


def _new_bytes_attachment(
    name: str, content: bytes, content_type: str, content_id: str, inline: bool
) -> Attachment:
    name = name.strip()
    if not name or _has_crlf(name) or _has_crlf(content_id):
        raise _invalid_header(name)
    resolved = content_type or detect_content_type(name)
    data = bytes(content)
    return Attachment(
        name=Path(name).name,
        content_type=resolved,
        size=len(data),
        content_id=content_id.strip("<>"),
        is_inline=inline,
        _data=data,
    )


def _new_file_attachment(path: str | Path, content_id: str, inline: bool) -> Attachment:
    resolved_path = Path(path)
    info = resolved_path.stat()
    return Attachment(
        name=resolved_path.name,
        content_type=detect_content_type(resolved_path.name),
        size=info.st_size,
        content_id=content_id.strip("<>"),
        is_inline=inline,
        _path=resolved_path,
    )


def new_attachment(name: str, content: bytes, content_type: str = "") -> Attachment:
    return _new_bytes_attachment(name, content, content_type, "", False)


def new_attachment_file(path: str | Path) -> Attachment:
    return _new_file_attachment(path, "", False)


def new_inline(name: str, content_id: str, content: bytes, content_type: str = "") -> Attachment:
    return _new_bytes_attachment(name, content, content_type, content_id, True)


def new_inline_file(path: str | Path, content_id: str) -> Attachment:
    return _new_file_attachment(path, content_id, True)


# --- Message ------------------------------------------------------------------


HeadersInput = Mapping[str, str | Sequence[str]] | Sequence[tuple[str, Sequence[str]]]


def _validate_header(name: str, values: Sequence[str]) -> tuple[str, tuple[str, ...]]:
    name = name.strip()
    if not name or _has_crlf(name) or ":" in name:
        raise _invalid_header(name)
    for value in values:
        if _has_crlf(value):
            raise _invalid_header(name)
    return name, tuple(values)


def _coerce_headers(headers: HeadersInput | None) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if headers is None:
        return ()
    pairs: Iterable[tuple[str, str | Sequence[str]]]
    pairs = headers.items() if isinstance(headers, Mapping) else headers
    out: list[tuple[str, tuple[str, ...]]] = []
    for name, value in pairs:
        values: Sequence[str] = (value,) if isinstance(value, str) else tuple(value)
        out.append(_validate_header(name, values))
    return tuple(out)


@dataclass(frozen=True, slots=True)
class Message:
    """An email message with text, HTML, inline files, and attachments."""

    from_: Address
    to: tuple[Address, ...] = ()
    cc: tuple[Address, ...] = ()
    bcc: tuple[Address, ...] = ()
    reply_to: tuple[Address, ...] = ()
    subject: str = ""
    text: str = ""
    html: str = ""
    headers: tuple[tuple[str, tuple[str, ...]], ...] = ()
    attachments: tuple[Attachment, ...] = ()
    inlines: tuple[Attachment, ...] = ()
    date: datetime | None = None
    message_id: str = ""
    charset: str = CHARSET_UTF8
    encoding: Encoding = Encoding.QUOTED_PRINTABLE
    envelope_from: str = ""
    max_attachment_bytes: int = DEFAULT_MAX_ATTACHMENT_BYTES

    def validate(self) -> None:
        if not (self.to or self.cc or self.bcc):
            raise _missing_recipient()
        if not self.text and not self.html:
            raise _missing_body()
        for addr in (*self.to, *self.cc, *self.bcc):
            if _has_crlf(addr.name):
                raise _invalid_address(addr.name)
            _validate_email(addr.email)
        if _has_crlf(self.from_.name) or _has_crlf(self.subject) or _has_crlf(self.message_id):
            raise _invalid_header()
        _validate_email(self.from_.email)
        if self.envelope_from:
            _validate_email(self.envelope_from)
        for attachment in (*self.attachments, *self.inlines):
            attachment.validate(self.max_attachment_bytes)

    def recipients(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for addr in (*self.to, *self.cc, *self.bcc):
            key = addr.email.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(addr.email)
        return out

    def sender(self) -> str:
        if self.envelope_from:
            return self.envelope_from
        return self.from_.email

    def to_bytes(self) -> bytes:
        return _render(self)

    def write_to(self, writer) -> int:
        """Write the rendered message to ``writer`` and return byte count."""
        data = _render(self)
        writer.write(data)
        return len(data)


def new_message(
    *,
    from_: str | Address,
    to: AddressInput | None = None,
    cc: AddressInput | None = None,
    bcc: AddressInput | None = None,
    reply_to: AddressInput | None = None,
    subject: str = "",
    text: str = "",
    html: str = "",
    headers: HeadersInput | None = None,
    attachments: Iterable[Attachment] | None = None,
    inlines: Iterable[Attachment] | None = None,
    date: datetime | None = None,
    message_id: str = "",
    charset: str = CHARSET_UTF8,
    encoding: Encoding = Encoding.QUOTED_PRINTABLE,
    envelope_from: str = "",
    max_attachment_bytes: int = DEFAULT_MAX_ATTACHMENT_BYTES,
) -> Message:
    if _has_crlf(subject):
        raise _invalid_header("subject contains CR/LF")
    if _has_crlf(message_id):
        raise _invalid_header("message-id contains CR/LF")
    if not charset.strip() or _has_crlf(charset):
        raise _invalid_header("charset")
    message = Message(
        from_=_coerce_address(from_),
        to=_coerce_addresses(to),
        cc=_coerce_addresses(cc),
        bcc=_coerce_addresses(bcc),
        reply_to=_coerce_addresses(reply_to),
        subject=subject,
        text=text,
        html=html,
        headers=_coerce_headers(headers),
        attachments=tuple(attachments or ()),
        inlines=tuple(inlines or ()),
        date=date if date is not None else datetime.now().astimezone(),
        message_id=message_id.strip("<>"),
        charset=charset,
        encoding=encoding,
        envelope_from=_validate_email(envelope_from) if envelope_from else "",
        max_attachment_bytes=max_attachment_bytes,
    )
    message.validate()
    return message


# --- Rendering ----------------------------------------------------------------


def _add_file_part(part: EmailMessage, attachment: Attachment, inline: bool) -> None:
    maintype, subtype = _split_content_type(
        attachment.content_type or detect_content_type(attachment.name)
    )
    data = attachment.read()
    if inline:
        cid = attachment.content_id or attachment.name
        part.add_related(
            data,
            maintype=maintype,
            subtype=subtype,
            cid=f"<{cid.strip('<>')}>",
            filename=attachment.name,
        )
    else:
        part.add_attachment(
            data, maintype=maintype, subtype=subtype, filename=attachment.name
        )


def _render(message: Message) -> bytes:
    message.validate()
    em = EmailMessage()
    em["From"] = str(message.from_)
    em["To"] = ", ".join(str(addr) for addr in message.to)
    if message.cc:
        em["Cc"] = ", ".join(str(addr) for addr in message.cc)
    if message.reply_to:
        em["Reply-To"] = ", ".join(str(addr) for addr in message.reply_to)
    if message.subject:
        em["Subject"] = message.subject
    if message.date is not None:
        em["Date"] = format_datetime(message.date)
    if message.message_id:
        em["Message-ID"] = f"<{message.message_id}>"
    for name, values in message.headers:
        em[name] = ", ".join(values)

    cte = str(message.encoding)
    if message.text and message.html:
        em.set_content(message.text, subtype="plain", charset=message.charset, cte=cte)
        em.add_alternative(message.html, subtype="html", charset=message.charset, cte=cte)
        body_part = cast(EmailMessage, em.get_payload(-1))
    elif message.html:
        em.set_content(message.html, subtype="html", charset=message.charset, cte=cte)
        body_part = em
    else:
        em.set_content(message.text, subtype="plain", charset=message.charset, cte=cte)
        body_part = em

    for inline in message.inlines:
        _add_file_part(body_part, inline, inline=True)
    for attachment in message.attachments:
        _add_file_part(em, attachment, inline=False)

    return em.as_bytes()


# --- SMTP client --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Config:
    """SMTP delivery configuration."""

    host: str
    port: int
    username: str = ""
    password: str = ""
    local_name: str = DEFAULT_LOCAL_NAME
    tls_policy: TLSPolicy = TLSPolicy.MANDATORY_STARTTLS
    tls_context: ssl.SSLContext | None = None
    allow_plain_auth: bool = False
    timeout: float = DEFAULT_TIMEOUT


@dataclass(frozen=True, slots=True)
class Account:
    """SMTP server, authentication, and default sender settings."""

    host: str
    port: int
    username: str = ""
    password: str = ""
    from_: str = ""
    from_name: str = ""
    tls_policy: TLSPolicy = TLSPolicy.UNKNOWN
    tls_context: ssl.SSLContext | None = None
    allow_plain_auth: bool = False
    timeout: float = 0.0
    local_name: str = ""


class _Connection:
    """A reusable, open SMTP connection."""

    def __init__(self, smtp: smtplib.SMTP) -> None:
        self._smtp = smtp

    def send(self, message: Message) -> None:
        message.validate()
        self._smtp.sendmail(message.sender(), message.recipients(), message.to_bytes())


class Client:
    """Sends messages through an SMTP server."""

    def __init__(self, config: Config) -> None:
        if not config.host or config.port <= 0:
            raise _invalid_address("invalid smtp address")
        if config.tls_policy is TLSPolicy.UNKNOWN:
            config = _replace_policy(config, TLSPolicy.MANDATORY_STARTTLS)
        self._config = config

    @property
    def config(self) -> Config:
        return self._config

    @contextlib.contextmanager
    def connection(self) -> Iterator[_Connection]:
        smtp = _open(self._config)
        try:
            yield _Connection(smtp)
        finally:
            try:
                smtp.quit()
            except smtplib.SMTPException:
                smtp.close()

    def send(self, message: Message) -> None:
        message.validate()
        with self.connection() as conn:
            conn.send(message)


def _replace_policy(config: Config, policy: TLSPolicy) -> Config:
    return Config(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        local_name=config.local_name,
        tls_policy=policy,
        tls_context=config.tls_context,
        allow_plain_auth=config.allow_plain_auth,
        timeout=config.timeout,
    )


def _open(config: Config) -> smtplib.SMTP:
    context = config.tls_context or ssl.create_default_context()
    local_name = config.local_name or None
    smtp: smtplib.SMTP
    is_tls = False
    if config.tls_policy is TLSPolicy.IMPLICIT:
        smtp = smtplib.SMTP_SSL(
            config.host, config.port, timeout=config.timeout, context=context
        )
        smtp.ehlo(config.local_name or None)  # type: ignore[arg-type]
        is_tls = True
    else:
        smtp = smtplib.SMTP(
            config.host, config.port, local_hostname=local_name, timeout=config.timeout
        )
        smtp.ehlo(config.local_name or None)  # type: ignore[arg-type]
        if config.tls_policy in (
            TLSPolicy.MANDATORY_STARTTLS,
            TLSPolicy.OPPORTUNISTIC_STARTTLS,
        ):
            if smtp.has_extn("starttls"):
                smtp.starttls(context=context)
                smtp.ehlo(config.local_name or None)  # type: ignore[arg-type]
                is_tls = True
            elif config.tls_policy is TLSPolicy.MANDATORY_STARTTLS:
                smtp.close()
                raise _tls_required()

    if config.username:
        if not is_tls and not config.allow_plain_auth:
            smtp.close()
            raise _plain_auth()
        smtp.login(config.username, config.password)
    return smtp


# --- Module-level send helpers ------------------------------------------------


def _client_kwargs_to_config(host: str, port: int, kwargs: dict[str, Any]) -> Config:
    return Config(host=host, port=port, **kwargs)


def send(host: str, port: int, message: Message, **client_kwargs: Any) -> None:
    Client(_client_kwargs_to_config(host, port, client_kwargs)).send(message)


def send_text(
    host: str,
    port: int,
    from_: str | Address,
    to: AddressInput,
    subject: str,
    text: str,
    **client_kwargs: Any,
) -> None:
    message = new_message(from_=from_, to=to, subject=subject, text=text)
    send(host, port, message, **client_kwargs)


def send_html(
    host: str,
    port: int,
    from_: str | Address,
    to: AddressInput,
    subject: str,
    html: str,
    **client_kwargs: Any,
) -> None:
    message = new_message(from_=from_, to=to, subject=subject, html=html)
    send(host, port, message, **client_kwargs)


def _account_config(account: Account) -> Config:
    policy = account.tls_policy
    if policy is TLSPolicy.UNKNOWN:
        policy = TLSPolicy.MANDATORY_STARTTLS
    return Config(
        host=account.host,
        port=account.port,
        username=account.username,
        password=account.password,
        local_name=account.local_name or DEFAULT_LOCAL_NAME,
        tls_policy=policy,
        tls_context=account.tls_context,
        allow_plain_auth=account.allow_plain_auth,
        timeout=account.timeout if account.timeout > 0 else DEFAULT_TIMEOUT,
    )


def _account_from(account: Account) -> str | Address:
    from_ = account.from_.strip() or account.username.strip()
    if not from_:
        raise _missing_from()
    if account.from_name:
        return new_address(account.from_name, from_)
    return from_


def quick_send(
    account: Account,
    *,
    to: AddressInput,
    subject: str = "",
    text: str = "",
    html: str = "",
    cc: AddressInput | None = None,
    bcc: AddressInput | None = None,
    reply_to: AddressInput | None = None,
    headers: HeadersInput | None = None,
    attachments: Iterable[Attachment] | None = None,
    inlines: Iterable[Attachment] | None = None,
    date: datetime | None = None,
    message_id: str = "",
    charset: str = CHARSET_UTF8,
    encoding: Encoding = Encoding.QUOTED_PRINTABLE,
    envelope_from: str = "",
) -> None:
    message = new_message(
        from_=_account_from(account),
        to=to,
        subject=subject,
        text=text,
        html=html,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        headers=headers,
        attachments=attachments,
        inlines=inlines,
        date=date,
        message_id=message_id,
        charset=charset,
        encoding=encoding,
        envelope_from=envelope_from,
    )
    Client(_account_config(account)).send(message)


def send_account_text(
    account: Account, to: AddressInput, subject: str, text: str, **kwargs: Any
) -> None:
    quick_send(account, to=to, subject=subject, text=text, **kwargs)


def send_account_html(
    account: Account, to: AddressInput, subject: str, html: str, **kwargs: Any
) -> None:
    quick_send(account, to=to, subject=subject, html=html, **kwargs)


# Reader-based attachments
def new_attachment_reader(name: str, reader: Callable[[], bytes], *, content_type: str = "") -> Attachment:
    return _new_bytes_attachment(name, reader(), content_type, "", False)


def new_inline_reader(name: str, content_id: str, reader: Callable[[], bytes], *, content_type: str = "") -> Attachment:
    return _new_bytes_attachment(name, reader(), content_type, content_id, True)
