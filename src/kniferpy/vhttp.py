from __future__ import annotations

from pathlib import Path

from kniferpy.internal import httpx
from kniferpy.internal.httpx import (
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

__all__ = [
    "GlobalConfig",
    "HTTPResponse",
    "JSONValue",
    "ResponseLike",
    "SessionLike",
    "HTTP_STATUS",
    "get_string_safe",
    "get_bytes_safe",
    "download_file_safe",
    "get_json_safe",
    "post_json_safe",
    "put_json_safe",
    "delete_safe",
    "patch_json_safe",
    "head_safe",
    "options_safe",
    "get_with_params_safe",
    "post_form_safe",
    "post_form_encoded_safe",
    "post_multipart_safe",
    "decode_response_body",
    "get_mime_type",
    "get_ext_by_mime",
    "parse_content_type",
    "get_charset_from_content_type",
    "parse_cookies",
    "make_cookie_header",
    "make_set_cookie",
    "basic_auth_header",
    "bearer_auth_header",
    "http_status_text",
    "is_ok",
    "is_client_error",
    "is_server_error",
    "is_redirected",
    "build_url",
    "to_params",
    "encode_params",
    "decode_param_map",
    "decode_params",
    "url_with_form",
    "is_https",
    "is_http",
    "get_user_agent",
    "set_user_agent",
    "snapshot_global_config",
    "reset_global_config",
    "configure_global_config",
    "set_global_timeout",
    "get_global_timeout",
    "set_global_max_redirects",
    "get_global_max_redirects",
    "set_global_max_response_bytes",
    "get_global_max_response_bytes",
    "set_global_follow_redirects",
    "get_global_follow_redirects",
    "set_global_header",
    "add_global_header",
    "remove_global_header",
    "clone_global_headers",
    "html_escape",
    "html_unescape",
    "clean_html",
    "filter_html_tag",
]