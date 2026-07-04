"""URL parsing, encoding, building, normalization, and resource opening.

Secure URL utilities for parsing, query manipulation, encoding, normalization,
type checking, and resource (file/HTTP) opening. All functions raise
:mod:`kniferpy.verr` types instead of returning sentinel errors.
"""

from __future__ import annotations

from urllib.parse import ParseResult

from kniferpy.internal import urlx
from kniferpy.internal.urlx import URLBuilder

__all__ = [
    "FileURLPrefix",
    "JarURLSeparator",
    "URLBuilder",
    "URLProtocolFile",
    "URLProtocolJar",
    "URLProtocolZip",
    "add_query",
    "append_query",
    "build_query",
    "complete",
    "content_length",
    "content_length_safe",
    "data_uri",
    "data_uri_base64",
    "decode",
    "decode_for_path",
    "decode_plus",
    "decode_query",
    "decode_query_first",
    "decode_query_map",
    "encode_all",
    "encode_blank",
    "encode_fragment",
    "encode_params",
    "encode_path",
    "encode_path_segment",
    "encode_query",
    "encode_query_map",
    "file_url",
    "file_urls",
    "form_url_encode",
    "get_query",
    "host",
    "is_absolute_url",
    "is_file_url",
    "is_http",
    "is_http_url",
    "is_https",
    "is_https_url",
    "is_jar_file_url",
    "is_jar_url",
    "is_private_host",
    "is_web_url",
    "new_url_builder",
    "normalize",
    "normalize_query",
    "normalize_with_options",
    "open_safe",
    "open_url",
    "parse",
    "parse_http",
    "parse_url_builder",
    "redact_userinfo",
    "remove_query",
    "size",
    "string_uri",
    "to_uri",
    "url_decode",
    "url_encode",
    "url_path",
    "validate_http_url",
]

# ── Parsing ───────────────────────────────────────────────────────────────────

parse = urlx.parse
parse_http = urlx.parse_http


# ── Query manipulation ────────────────────────────────────────────────────────

normalize_query = urlx.normalize_query
add_query = urlx.add_query
get_query = urlx.get_query
remove_query = urlx.remove_query
build_query = urlx.build_query
append_query = urlx.append_query
encode_query_map = urlx.encode_query_map
encode_params = urlx.encode_params
decode_query_first = urlx.decode_query_first
decode_query_map = urlx.decode_query_map


# ── Encoding / decoding ───────────────────────────────────────────────────────

encode_query = urlx.encode_query
decode_query = urlx.decode_query
encode_path_segment = urlx.encode_path_segment
encode_path = urlx.encode_path
encode_fragment = urlx.encode_fragment
decode = urlx.decode
decode_for_path = urlx.decode_for_path
url_encode = urlx.url_encode
url_decode = urlx.url_decode
decode_plus = urlx.decode_plus
encode_all = urlx.encode_all
form_url_encode = urlx.form_url_encode
encode_blank = urlx.encode_blank


# ── URL builder ───────────────────────────────────────────────────────────────

new_url_builder = urlx.new_url_builder
parse_url_builder = urlx.parse_url_builder


# ── Data URI ──────────────────────────────────────────────────────────────────

data_uri = urlx.data_uri
data_uri_base64 = urlx.data_uri_base64
string_uri = urlx.string_uri


# ── File URL ──────────────────────────────────────────────────────────────────

file_url = urlx.file_url
file_urls = urlx.file_urls


# ── URL helpers ───────────────────────────────────────────────────────────────

host = urlx.host
complete = urlx.complete
url_path = urlx.url_path
to_uri = urlx.to_uri


# ── Normalization ─────────────────────────────────────────────────────────────

normalize = urlx.normalize
normalize_with_options = urlx.normalize_with_options


# ── Type checks ───────────────────────────────────────────────────────────────

is_http_url = urlx.is_http_url
is_https_url = urlx.is_https_url
is_absolute_url = urlx.is_absolute_url
is_file_url = urlx.is_file_url
is_jar_url = urlx.is_jar_url
is_jar_file_url = urlx.is_jar_file_url
is_http = urlx.is_http
is_https = urlx.is_https
is_web_url = urlx.is_web_url


# ── Resource opening ──────────────────────────────────────────────────────────

open_url = urlx.open_url
open_safe = urlx.open_safe
content_length = urlx.content_length
content_length_safe = urlx.content_length_safe
size = urlx.size


# ── Validation ────────────────────────────────────────────────────────────────

validate_http_url = urlx.validate_http_url
is_private_host = urlx.is_private_host
redact_userinfo = urlx.redact_userinfo


# ── Constants ─────────────────────────────────────────────────────────────────

FileURLPrefix = urlx.FileURLPrefix
URLProtocolFile = urlx.URLProtocolFile
URLProtocolJar = urlx.URLProtocolJar
URLProtocolZip = urlx.URLProtocolZip
JarURLSeparator = urlx.JarURLSeparator