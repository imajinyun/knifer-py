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

from kniferpy.internal import mailx
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
)

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
]

detect_content_type = mailx.detect_content_type
new_address = mailx.new_address
new_attachment = mailx.new_attachment
new_attachment_file = mailx.new_attachment_file
new_attachment_reader = mailx.new_attachment_reader
new_inline = mailx.new_inline
new_inline_file = mailx.new_inline_file
new_inline_reader = mailx.new_inline_reader
new_message = mailx.new_message
parse_address = mailx.parse_address
parse_address_list = mailx.parse_address_list
quick_send = mailx.quick_send
send = mailx.send
send_account_html = mailx.send_account_html
send_account_text = mailx.send_account_text
send_html = mailx.send_html
send_text = mailx.send_text
new_header = mailx.new_header
