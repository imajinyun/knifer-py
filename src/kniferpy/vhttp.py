from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal import httpx
from kniferpy.internal.httpx import (
    CharsetConfig,
    CharsetOption,
    # Types / Data Classes
    Client,
    # ClientOption
    ClientOption,
    ContentType,
    CookieJar,
    FormFile,
    GlobalConfig,
    Header,
    # HTML/Charset option types
    HTMLCleanConfig,
    HTMLCleanOption,
    HTMLFilterConfig,
    HTMLFilterOption,
    HTTPError,
    HTTPRequest,
    HTTPResponse,
    JSONValue,
    Method,
    RequestOption,
    ResponseLike,
    SaveConfig,
    SaveOption,
    SessionLike,
    # SimpleServer
    SimpleServer,
    URLPolicy,
    UserAgent,
    create_server,
    create_server_with_options,
    # Request constructors (builder pattern)
    delete,
    delete_safe_r,
    # Save to file / writer
    download,
    # Download helpers
    download_bytes_e,
    download_bytes_e_with_options,
    download_bytes_safe_e,
    download_file,
    download_file_safe,
    download_file_safe_with_options,
    download_file_with_options,
    download_safe,
    download_string_e,
    download_string_e_with_options,
    download_string_safe_e,
    download_with_options,
    # Error constructors
    errorf,
    errorf_with_code,
    get,
    get_safe_r,
    # Shortcut wrappers
    get_string_e,
    get_string_e_with_options,
    get_string_safe_e,
    get_with_params_e,
    get_with_params_e_with_options,
    get_with_timeout_e,
    head,
    head_safe_r,
    # Client constructors
    new_client,
    new_client_with_config,
    new_error,
    new_error_with_code,
    new_isolated_client,
    new_isolated_request,
    new_request,
    new_request_with_config,
    new_safe_request,
    new_simple_server,
    new_simple_server_addr,
    new_simple_server_addr_with_options,
    new_simple_server_with_options,
    options,
    options_safe_r,
    # UserAgent parser
    parse_user_agent,
    patch,
    patch_safe_r,
    post,
    post_form_e,
    post_form_e_with_options,
    post_form_safe_e,
    post_json_e,
    post_json_e_with_options,
    post_json_safe_e,
    post_safe_r,
    post_string_e,
    post_string_e_with_options,
    post_string_safe_e,
    put,
    put_safe_r,
    # RequestOption constructors
    with_allowed_hosts,
    with_charset,
    with_client_global_config,
    with_client_request_options,
    with_content_type,
    with_follow_redirects,
    with_global_config,
    with_header,
    with_headers,
    with_max_redirects,
    with_max_response_bytes,
    # SaveOption constructors
    with_save_create_parents,
    with_save_default_filename,
    with_save_dir_perm,
    with_save_file_perm,
    with_save_overwrite,
    # Scoped global config
    with_scoped_global_config,
    with_session,
    with_timeout,
    with_tls_config,
    with_url_policy,
    with_user_agent,
)

# Safe HTTP methods (existing)
get_string_safe = httpx.get_string_safe
get_bytes_safe = httpx.get_bytes_safe
download_file_safe = httpx.download_file_safe  # noqa: F811
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
configure_default_transport_provider = httpx.configure_default_transport_provider
reset_default_transport = httpx.reset_default_transport
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
clean_html_with_options = httpx.clean_html_with_options
filter_html_tag = httpx.filter_html_tag
filter_html_tag_with_options = httpx.filter_html_tag_with_options

# HTML option constructors
with_html_tag_regexp = httpx.with_html_tag_regexp
with_html_comment_regexp = httpx.with_html_comment_regexp
with_html_filter_compile_func = httpx.with_html_filter_compile_func

# Content-Type helpers
build_content_type = httpx.build_content_type
is_default_content_type = httpx.is_default_content_type
is_form_urlencoded = httpx.is_form_urlencoded
guess_content_type = httpx.guess_content_type
get_charset_from_html = httpx.get_charset_from_html
get_charset_from_html_with_options = httpx.get_charset_from_html_with_options
get_charset_from_content_type_with_options = httpx.get_charset_from_content_type_with_options

# Charset option constructors
with_charset_regexp = httpx.with_charset_regexp
with_meta_charset_regexp = httpx.with_meta_charset_regexp

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
    # Types
    "Client",
    "ClientOption",
    "CookieJar",
    "FormFile",
    "GlobalConfig",
    "HTTPError",
    "HTTPRequest",
    "HTTPResponse",
    "JSONValue",
    "RequestOption",
    "ResponseLike",
    "SaveConfig",
    "SaveOption",
    "SessionLike",
    "SimpleServer",
    "URLPolicy",
    "UserAgent",
    # HTML/Charset option types
    "HTMLCleanConfig",
    "HTMLCleanOption",
    "HTMLFilterConfig",
    "HTMLFilterOption",
    "CharsetConfig",
    "CharsetOption",
    # Constants
    "Method",
    "Header",
    "ContentType",
    "HTTP_STATUS",
    # ClientOption
    "with_client_global_config",
    "with_client_request_options",
    # RequestOption
    "with_allowed_hosts",
    "with_charset",
    "with_content_type",
    "with_follow_redirects",
    "with_global_config",
    "with_header",
    "with_headers",
    "with_max_redirects",
    "with_max_response_bytes",
    "with_session",
    "with_timeout",
    "with_tls_config",
    "with_url_policy",
    "with_user_agent",
    # SaveOption
    "with_save_create_parents",
    "with_save_default_filename",
    "with_save_dir_perm",
    "with_save_file_perm",
    "with_save_overwrite",
    # Error
    "errorf",
    "errorf_with_code",
    "new_error",
    "new_error_with_code",
    # Request constructors (builder)
    "delete",
    "delete_safe_r",
    "get",
    "get_safe_r",
    "head",
    "head_safe_r",
    "new_isolated_request",
    "new_request",
    "new_request_with_config",
    "new_safe_request",
    "options",
    "options_safe_r",
    "patch",
    "patch_safe_r",
    "post",
    "post_safe_r",
    "put",
    "put_safe_r",
    # Client
    "new_client",
    "new_client_with_config",
    "new_isolated_client",
    # Shortcut wrappers
    "get_string_e",
    "get_string_e_with_options",
    "get_string_safe_e",
    "get_with_params_e",
    "get_with_params_e_with_options",
    "get_with_timeout_e",
    "post_form_e",
    "post_form_e_with_options",
    "post_form_safe_e",
    "post_json_e",
    "post_json_e_with_options",
    "post_json_safe_e",
    "post_string_e",
    "post_string_e_with_options",
    "post_string_safe_e",
    # Download
    "download_bytes_e",
    "download_bytes_e_with_options",
    "download_bytes_safe_e",
    "download_string_e",
    "download_string_e_with_options",
    "download_string_safe_e",
    # Save
    "download",
    "download_file",
    "download_file_safe_with_options",
    "download_file_with_options",
    "download_safe",
    "download_with_options",
    # SimpleServer
    "create_server",
    "create_server_with_options",
    "new_simple_server",
    "new_simple_server_addr",
    "new_simple_server_addr_with_options",
    "new_simple_server_with_options",
    # UserAgent
    "parse_user_agent",
    # Scoped
    "with_scoped_global_config",
    # Safe HTTP
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
    # Form
    "post_form_safe",
    "post_form_encoded_safe",
    "post_multipart_safe",
    # Content Decoding
    "decode_response_body",
    # MIME
    "get_mime_type",
    "get_ext_by_mime",
    "parse_content_type",
    "get_charset_from_content_type",
    # Cookie
    "parse_cookies",
    "make_cookie_header",
    "make_set_cookie",
    # Auth
    "basic_auth_header",
    "bearer_auth_header",
    # Status
    "http_status_text",
    "is_ok",
    "is_client_error",
    "is_server_error",
    "is_redirected",
    # URL
    "build_url",
    "to_params",
    "encode_params",
    "decode_param_map",
    "decode_params",
    "url_with_form",
    "is_https",
    "is_http",
    # User Agent
    "get_user_agent",
    "set_user_agent",
    # Global Config
    "snapshot_global_config",
    "reset_global_config",
    "configure_global_config",
    "configure_default_transport_provider",
    "reset_default_transport",
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
    # HTML
    "html_escape",
    "html_unescape",
    "clean_html",
    "clean_html_with_options",
    "filter_html_tag",
    "filter_html_tag_with_options",
    # HTML option constructors
    "with_html_tag_regexp",
    "with_html_comment_regexp",
    "with_html_filter_compile_func",
    # Content-Type
    "build_content_type",
    "is_default_content_type",
    "is_form_urlencoded",
    "guess_content_type",
    "get_charset_from_html",
    "get_charset_from_html_with_options",
    "get_charset_from_content_type_with_options",
    # Charset option constructors
    "with_charset_regexp",
    "with_meta_charset_regexp",
    # Cookie Jar
    "set_cookie_jar",
    "get_cookie_jar",
    "close_cookie",
    # Global
    "set_global_boundary",
    "get_global_boundary",
    "set_global_decode_url",
    "is_global_decode_url",
    "set_ignore_eof_error",
    "is_ignore_eof_error",
    # Go-compat type aliases
    "ContentDecoder",
    "NewRequestFunc",
    "MultipartWriterFactory",
    "MultipartWriter",
    "ServerOption",
    "StaticOption",
    "ListenAndServeFunc",
    # Go-compat functions
    "set_global_user_agent",
    "get_global_user_agent",
    "get_with_timeout_e_with_options",
    "reset_server_starters",
]

# ── Go-compat type aliases ──────────────────────────────────────────────────

ContentDecoder = Callable[[Any], Any]
NewRequestFunc = Callable[[str, str, Any], Any]
MultipartWriterFactory = Callable[[Any], Any]
MultipartWriter = Any
ServerOption = Callable[[Any], None]
StaticOption = Callable[[Any], None]
ListenAndServeFunc = Callable[[Any], Any]

# ── Go-compat standalone functions ──────────────────────────────────────────

set_global_user_agent = httpx.set_user_agent
get_global_user_agent = httpx.get_user_agent
get_with_timeout_e_with_options = httpx.get_with_timeout_e


def reset_server_starters() -> None:
    """Reset server starters (Go compat, no-op in Python)."""
    pass
