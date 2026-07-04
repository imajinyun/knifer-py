from __future__ import annotations

from pathlib import Path

from kniferpy.internal import httpx
from kniferpy.internal.httpx import (
    CookieJar,
    GlobalConfig,
    HTTPResponse,
    JSONValue,
    ResponseLike,
    SessionLike,
)

# Safe HTTP methods
get_string_safe = httpx.get_string_safe
get_bytes_safe = httpx.get_bytes_safe
download_file_safe = httpx.download_file_safe
get_json_safe = httpx.get_json_safe
post_json_safe = httpx.post_json_safe
put_json_safe = httpx.put_json_safe
delete_safe = httpx.delete_safe
patch_json_safe = httpx.patch_json_safe
head_safe = httpx.head_safe
options_safe = httpx.options_safe
get_with_params_safe = httpx.get_with_params_safe

# Form / Multipart
post_form_safe = httpx.post_form_safe
post_form_encoded_safe = httpx.post_form_encoded_safe
post_multipart_safe = httpx.post_multipart_safe

# Content Decoding
decode_response_body = httpx.decode_response_body

# MIME / Content-Type
get_mime_type = httpx.get_mime_type
get_ext_by_mime = httpx.get_ext_by_mime
parse_content_type = httpx.parse_content_type
get_charset_from_content_type = httpx.get_charset_from_content_type

# Cookie
parse_cookies = httpx.parse_cookies
make_cookie_header = httpx.make_cookie_header
make_set_cookie = httpx.make_set_cookie

# Auth headers
basic_auth_header = httpx.basic_auth_header
bearer_auth_header = httpx.bearer_auth_header

# Status codes
HTTP_STATUS = httpx.HTTP_STATUS
http_status_text = httpx.http_status_text
is_ok = httpx.is_ok
is_client_error = httpx.is_client_error
is_server_error = httpx.is_server_error
is_redirected = httpx.is_redirected

# URL building
build_url = httpx.build_url
to_params = httpx.to_params
encode_params = httpx.encode_params
decode_param_map = httpx.decode_param_map
decode_params = httpx.decode_params
url_with_form = httpx.url_with_form
is_https = httpx.is_https
is_http = httpx.is_http

# User agent
get_user_agent = httpx.get_user_agent
set_user_agent = httpx.set_user_agent

# Global config
snapshot_global_config = httpx.snapshot_global_config
reset_global_config = httpx.reset_global_config
configure_global_config = httpx.configure_global_config
set_global_timeout = httpx.set_global_timeout
get_global_timeout = httpx.get_global_timeout
set_global_max_redirects = httpx.set_global_max_redirects
get_global_max_redirects = httpx.get_global_max_redirects
set_global_max_response_bytes = httpx.set_global_max_response_bytes
get_global_max_response_bytes = httpx.get_global_max_response_bytes
set_global_follow_redirects = httpx.set_global_follow_redirects
get_global_follow_redirects = httpx.get_global_follow_redirects
set_global_header = httpx.set_global_header
add_global_header = httpx.add_global_header
remove_global_header = httpx.remove_global_header
clone_global_headers = httpx.clone_global_headers

# HTML utilities
html_escape = httpx.html_escape
html_unescape = httpx.html_unescape
clean_html = httpx.clean_html
filter_html_tag = httpx.filter_html_tag

# Content-Type helpers
build_content_type = httpx.build_content_type
is_default_content_type = httpx.is_default_content_type
is_form_urlencoded = httpx.is_form_urlencoded
guess_content_type = httpx.guess_content_type
get_charset_from_html = httpx.get_charset_from_html

# Cookie jar
set_cookie_jar = httpx.set_cookie_jar
get_cookie_jar = httpx.get_cookie_jar
close_cookie = httpx.close_cookie

# Global boundary / decode / EOF
set_global_boundary = httpx.set_global_boundary
get_global_boundary = httpx.get_global_boundary
set_global_decode_url = httpx.set_global_decode_url
is_global_decode_url = httpx.is_global_decode_url
set_ignore_eof_error = httpx.set_ignore_eof_error
is_ignore_eof_error = httpx.is_ignore_eof_error

__all__ = [
    "CookieJar",
    "GlobalConfig",
    "HTTPResponse",
    "JSONValue",
    "ResponseLike",
    "SessionLike",
    "HTTP_STATUS",
    "add_global_header",
    "basic_auth_header",
    "bearer_auth_header",
    "build_content_type",
    "build_url",
    "clean_html",
    "clone_global_headers",
    "close_cookie",
    "configure_global_config",
    "decode_param_map",
    "decode_params",
    "decode_response_body",
    "delete_safe",
    "download_file_safe",
    "encode_params",
    "filter_html_tag",
    "get_bytes_safe",
    "get_charset_from_content_type",
    "get_charset_from_html",
    "get_cookie_jar",
    "get_ext_by_mime",
    "get_global_boundary",
    "get_global_follow_redirects",
    "get_global_max_redirects",
    "get_global_max_response_bytes",
    "get_global_timeout",
    "get_json_safe",
    "get_mime_type",
    "get_string_safe",
    "get_user_agent",
    "get_with_params_safe",
    "guess_content_type",
    "head_safe",
    "html_escape",
    "html_unescape",
    "http_status_text",
    "is_client_error",
    "is_default_content_type",
    "is_form_urlencoded",
    "is_global_decode_url",
    "is_http",
    "is_https",
    "is_ignore_eof_error",
    "is_ok",
    "is_redirected",
    "is_server_error",
    "make_cookie_header",
    "make_set_cookie",
    "options_safe",
    "parse_content_type",
    "parse_cookies",
    "patch_json_safe",
    "post_form_encoded_safe",
    "post_form_safe",
    "post_json_safe",
    "post_multipart_safe",
    "put_json_safe",
    "remove_global_header",
    "reset_global_config",
    "set_cookie_jar",
    "set_global_boundary",
    "set_global_decode_url",
    "set_global_follow_redirects",
    "set_global_header",
    "set_global_max_redirects",
    "set_global_max_response_bytes",
    "set_global_timeout",
    "set_ignore_eof_error",
    "set_user_agent",
    "snapshot_global_config",
    "to_params",
    "url_with_form",
]