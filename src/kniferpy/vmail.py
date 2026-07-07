"""SMTP mail composition and delivery backed by the standard library.

Build validated :class:`Message` values with :func:`new_message`, render them to
RFC 5322 bytes with :meth:`Message.to_bytes`, and deliver them through
:class:`Client` or the :func:`send`/:func:`send_text`/:func:`send_html`
one-shot helpers. :class:`Account` plus :func:`quick_send` carry reusable sender
defaults. Addresses are validated and parsed via :func:`new_address`,
:func:`parse_address`, and :func:`parse_address_list`; attachments and inline
parts come from :func:`new_attachment`, :func:`new_attachment_file`,
:func:`new_inline`, and :func:`new_inline_file`.

Security defaults mirror knifer-go: STARTTLS is mandatory unless a weaker
:class:`TLSPolicy` is chosen, plaintext ``AUTH`` is refused unless explicitly
allowed, header and address fields reject CR/LF injection, and attachments are
size-limited. MIME rendering is delegated to :mod:`email.message`.

knifer-go's functional ``With*`` message/client options collapse into keyword
arguments (``new_message(...)``, ``Config``, ``Account``); its pluggable
``BoundaryGenerator``, ``SenderProvider``, custom ``DialContext``, and
``SendCloser.Dial`` reuse hooks are intentionally omitted in favor of the
stdlib :class:`smtplib.SMTP` client and a :meth:`Client.connection` context
manager. Errors raise :mod:`kniferpy.verr` types instead of returning
sentinels.
"""

from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal.mailx import (
    CHARSET_ASCII,
    CHARSET_UTF8,
    DEFAULT_MAX_ATTACHMENT_BYTES,
    TYPE_APPLICATION_OCTET_STREAM,
    TYPE_TEXT_HTML,
    TYPE_TEXT_PLAIN,
    Account,
    Address,
    Attachment,
    Client,
    Config,
    Encoding,
    Header,
    Message,
    TLSPolicy,
    _attachment_too_large,
    _invalid_address,
    _invalid_header,
    _missing_body,
    _missing_from,
    _missing_recipient,
    _plain_auth,
    _tls_required,
    detect_content_type,
    new_address,
    new_attachment,
    new_attachment_file,
    new_attachment_reader,
    new_header,
    new_inline,
    new_inline_file,
    new_inline_reader,
    new_message,
    parse_address,
    parse_address_list,
    quick_send,
    send,
    send_account_html,
    send_account_text,
    send_html,
    send_text,
)

# ── Go-compat sentinel errors ──────────────────────────────────────────────────

ErrInvalidAddress = _invalid_address()
ErrInvalidHeader = _invalid_header()
ErrMissingFrom = _missing_from()
ErrMissingRecipient = _missing_recipient()
ErrMissingBody = _missing_body()
ErrTLSRequired = _tls_required()
ErrPlainAuth = _plain_auth()
ErrAttachmentTooLarge = _attachment_too_large()

# ── Go-compat standalone Encoding constants ────────────────────────────────────

EncodingBase64 = Encoding.BASE64
EncodingQuotedPrintable = Encoding.QUOTED_PRINTABLE
Encoding7Bit = Encoding.SEVEN_BIT
Encoding8Bit = Encoding.EIGHT_BIT

# ── Go-compat standalone TLSPolicy constants ───────────────────────────────────

TLSPolicyUnknown = TLSPolicy.UNKNOWN
TLSMandatoryStartTLS = TLSPolicy.MANDATORY_STARTTLS
TLSImplicit = TLSPolicy.IMPLICIT
TLSOpportunisticStartTLS = TLSPolicy.OPPORTUNISTIC_STARTTLS
TLSNone = TLSPolicy.NONE

# ── Go-compat type aliases ─────────────────────────────────────────────────────

BoundaryGenerator = Callable[[], str]
Charset = str
ContentType = str
MessageOption = Callable[[Any], None]
QuickOption = Callable[[Any], None]
Sender = Callable[..., None]
SenderFunc = Callable[..., None]
SenderProvider = Callable[..., Any]
DialContextFunc = Callable[..., Any]
ClientOption = Callable[[Any], None]
SendCloser = Any

# ── Go-compat new_client constructor ───────────────────────────────────────────


def new_client(host: str, port: int, **kwargs: Any) -> Client:
    """Create an SMTP client (Go compat)."""
    return Client(Config(host=host, port=port, **kwargs))


__all__ = [
    "CHARSET_ASCII",
    "CHARSET_UTF8",
    "DEFAULT_MAX_ATTACHMENT_BYTES",
    "TYPE_APPLICATION_OCTET_STREAM",
    "TYPE_TEXT_HTML",
    "TYPE_TEXT_PLAIN",
    "Account",
    "Address",
    "Attachment",
    "Client",
    "Config",
    "Encoding",
    "Header",
    "Message",
    "TLSPolicy",
    "detect_content_type",
    "new_address",
    "new_attachment",
    "new_attachment_file",
    "new_attachment_reader",
    "new_client",
    "new_header",
    "new_inline",
    "new_inline_file",
    "new_inline_reader",
    "new_message",
    "parse_address",
    "parse_address_list",
    "quick_send",
    "send",
    "send_account_html",
    "send_account_text",
    "send_html",
    "send_text",
    # Go-compat sentinel errors
    "ErrInvalidAddress",
    "ErrInvalidHeader",
    "ErrMissingFrom",
    "ErrMissingRecipient",
    "ErrMissingBody",
    "ErrTLSRequired",
    "ErrPlainAuth",
    "ErrAttachmentTooLarge",
    # Go-compat standalone Encoding constants
    "EncodingBase64",
    "EncodingQuotedPrintable",
    "Encoding7Bit",
    "Encoding8Bit",
    # Go-compat standalone TLSPolicy constants
    "TLSPolicyUnknown",
    "TLSMandatoryStartTLS",
    "TLSImplicit",
    "TLSOpportunisticStartTLS",
    "TLSNone",
    # Go-compat type aliases
    "BoundaryGenerator",
    "Charset",
    "ContentType",
    "MessageOption",
    "QuickOption",
    "Sender",
    "SenderFunc",
    "SenderProvider",
    "DialContextFunc",
    "ClientOption",
    "SendCloser",
]
