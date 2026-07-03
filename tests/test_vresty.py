from __future__ import annotations

import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from kniferpy.vresty import (
    Client,
    ContentType,
    GlobalConfig,
    Header,
    HTTPError,
    HTTPResponse,
    Method,
    URLPolicy,
    add_global_header,
    build_basic_auth,
    build_content_type,
    clone_global_headers,
    close_cookie,
    configure_global_config,
    delete,
    download_bytes_e,
    download_file,
    download_file_with_options,
    download_string_e,
    get,
    get_charset_from_content_type,
    get_charset_from_html,
    get_global_follow_redirects,
    get_global_max_redirects,
    get_global_max_response_bytes,
    get_global_timeout,
    get_global_user_agent,
    get_mime_type,
    get_string_e,
    guess_content_type,
    head,
    http_errorf,
    is_default_content_type,
    is_form_url_encoded,
    is_http,
    is_https,
    new_client,
    new_client_with_config,
    new_http_error,
    new_isolated_client,
    new_request,
    new_safe_request,
    options,
    patch,
    post,
    post_form_e,
    post_json_e,
    post_string_e,
    put,
    remove_global_header,
    reset_global_config,
    set_global_follow_redirects,
    set_global_header,
    set_global_max_redirects,
    set_global_max_response_bytes,
    set_global_timeout,
    set_global_user_agent,
    snapshot_global_config,
    to_params,
    url_with_form,
    with_charset,
    with_content_type,
    with_header,
    with_headers,
    with_scoped_global_config,
    with_timeout,
    with_url_policy,
    with_user_agent,
)


class _TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ok':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/json':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'hello': 'world'}).encode())
        elif self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', f'http://{self.server.server_address[0]}:{self.server.server_address[1]}/ok')
            self.end_headers()
        elif self.path == '/echo':
            body = b''
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/status/404':
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
        elif self.path == '/status/500':
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Internal Error')
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'default')

    def do_POST(self):
        body = b''
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
        if self.path == '/echo':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/json':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'received': body.decode()}).encode())
        elif self.path == '/form':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(body)

    def do_PUT(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(body)

    def do_DELETE(self):
        self.send_response(204)
        self.end_headers()

    def do_PATCH(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Allow', 'GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS')
        self.end_headers()

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope='module')
def test_server():
    server = HTTPServer(('127.0.0.1', 0), _TestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    addr = server.server_address
    url = f'http://{addr[0]}:{addr[1]}'
    yield url
    server.shutdown()
    thread.join()


class TestHTTPRequest:
    def test_get_ok(self, test_server):
        resp = get(f'{test_server}/ok').execute()
        assert resp.is_ok()
        assert resp.status_code == 200
        assert resp.body_text() == 'OK'

    def test_get_json(self, test_server):
        resp = get(f'{test_server}/json').execute()
        assert resp.is_ok()
        assert resp.json() == {'hello': 'world'}

    def test_get_404(self, test_server):
        resp = get(f'{test_server}/status/404').execute()
        assert not resp.is_ok()
        assert resp.status_code == 404
        assert resp.body_text() == 'Not Found'

    def test_get_500(self, test_server):
        resp = get(f'{test_server}/status/500').execute()
        assert not resp.is_ok()
        assert resp.status_code == 500

    def test_post_echo(self, test_server):
        resp = post(f'{test_server}/echo').body_string('hello post').execute()
        assert resp.is_ok()
        assert resp.body_text() == 'hello post'

    def test_put(self, test_server):
        resp = put(f'{test_server}/echo').body_string('put data').execute()
        assert resp.is_ok()
        assert resp.body_text() == 'put data'

    def test_delete(self, test_server):
        resp = delete(f'{test_server}/echo').execute()
        assert resp.status_code == 204

    def test_patch(self, test_server):
        resp = patch(f'{test_server}/echo').body_string('patch data').execute()
        assert resp.is_ok()
        assert resp.body_text() == 'patch data'

    def test_head(self, test_server):
        resp = head(f'{test_server}/ok').execute()
        assert resp.is_ok()
        assert resp.headers.get('Content-Type') == 'text/plain'

    def test_options(self, test_server):
        resp = options(f'{test_server}/ok').execute()
        assert resp.is_ok()
        assert 'Allow' in resp.headers

    def test_body_string(self, test_server):
        resp = post(f'{test_server}/echo').body_string('test').execute()
        assert resp.body_text() == 'test'

    def test_body_json(self, test_server):
        resp = post(f'{test_server}/json').body_json('{"key":"value"}').execute()
        assert resp.is_ok()

    def test_content_type(self, test_server):
        req = post(f'{test_server}/echo').body_string('data')
        req.content_type('text/plain')
        resp = req.execute()
        assert resp.is_ok()

    def test_charset(self, test_server):
        resp = get(f'{test_server}/ok').charset('UTF-8').execute()
        assert resp.is_ok()

    def test_charset_latin1(self, test_server):
        resp = get(f'{test_server}/ok').charset('ISO-8859-1').execute()
        assert resp.is_ok()

    def test_query_param(self, test_server):
        resp = get(f'{test_server}/echo').query('a', '1').query('b', '2').execute()
        assert resp.is_ok()

    def test_header(self, test_server):
        resp = get(f'{test_server}/echo').header('X-Custom', 'test').execute()
        assert resp.is_ok()

    def test_headers(self, test_server):
        resp = get(f'{test_server}/echo').headers({'X-A': '1', 'X-B': '2'}).execute()
        assert resp.is_ok()

    def test_basic_auth(self, test_server):
        resp = get(f'{test_server}/ok').basic_auth('user', 'pass').execute()
        assert resp.is_ok()

    def test_bearer_auth(self, test_server):
        resp = get(f'{test_server}/ok').bearer_auth('token123').execute()
        assert resp.is_ok()

    def test_bearer_auth_header_present(self, test_server):
        req = get(f'{test_server}/ok').bearer_auth('token123')
        auth_vals = req._headers.get('Authorization', [])
        assert len(auth_vals) == 1
        assert auth_vals[0] == 'Bearer token123'

    def test_cookie(self, test_server):
        resp = get(f'{test_server}/ok').cookie('session', 'abc').execute()
        assert resp.is_ok()

    def test_with_options(self, test_server):
        resp = get(f'{test_server}/ok', with_timeout(5.0)).execute()
        assert resp.is_ok()

    def test_with_header_option(self, test_server):
        resp = get(f'{test_server}/ok', with_header('X-Opt', 'val')).execute()
        assert resp.is_ok()

    def test_with_headers_option(self, test_server):
        resp = get(f'{test_server}/ok', with_headers({'X-H1': '1', 'X-H2': '2'})).execute()
        assert resp.is_ok()

    def test_with_user_agent(self, test_server):
        resp = get(f'{test_server}/ok', with_user_agent('MyApp/1.0')).execute()
        assert resp.is_ok()

    def test_with_content_type_option(self, test_server):
        resp = post(f'{test_server}/echo', with_content_type('text/plain')).body_string('data').execute()
        assert resp.is_ok()

    def test_with_charset_option(self, test_server):
        resp = get(f'{test_server}/ok', with_charset('UTF-8')).execute()
        assert resp.is_ok()

    def test_response_error(self, test_server):
        resp = get('http://invalid-host-that-does-not-exist.example').execute()
        assert resp.err is not None

    def test_post_form(self, test_server):
        resp = post(f'{test_server}/form').form({'key': 'value'}).execute()
        assert resp.is_ok()

    def test_post_json_string(self, test_server):
        resp = post(f'{test_server}/json').body_json('{"test": true}').execute()
        assert resp.is_ok()

    def test_chainable_api(self, test_server):
        resp = (
            get(f'{test_server}/ok')
            .header('X-Custom', 'val')
            .query('page', '1')
            .timeout(5.0)
            .execute()
        )
        assert resp.is_ok()

    def test_must_execute_success(self, test_server):
        resp = get(f'{test_server}/ok').must_execute()
        assert resp.is_ok()

    def test_must_execute_failure(self):
        with pytest.raises(HTTPError):
            get('http://invalid-host-that-does-not-exist.example').must_execute()

    def test_new_request(self, test_server):
        resp = new_request(Method.GET, f'{test_server}/ok').execute()
        assert resp.is_ok()

    def test_new_request_with_method(self, test_server):
        resp = new_request(Method.POST, f'{test_server}/echo').body_string('new').execute()
        assert resp.is_ok()

    def test_get_string_e(self, test_server):
        body, err = get_string_e(f'{test_server}/ok')
        assert err is None
        assert body == 'OK'

    def test_post_string_e(self, test_server):
        body, err = post_string_e(f'{test_server}/echo', 'hello')
        assert err is None
        assert body == 'hello'

    def test_post_form_e(self, test_server):
        body, err = post_form_e(f'{test_server}/form', {'x': 'y'})
        assert err is None

    def test_post_json_e(self, test_server):
        body, err = post_json_e(f'{test_server}/json', '{"a":1}')
        assert err is None
        assert 'a' in body

    def test_download_bytes_e(self, test_server):
        content, err = download_bytes_e(f'{test_server}/ok')
        assert err is None
        assert content == b'OK'

    def test_download_string_e(self, test_server):
        content, err = download_string_e(f'{test_server}/ok')
        assert err is None
        assert content == 'OK'

    def test_download_file(self, test_server):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = os.path.join(tmpdir, 'test.txt')
            size, err = download_file(f'{test_server}/ok', dest)
            assert err is None
            assert size > 0
            assert os.path.exists(dest)
            assert Path(dest).read_text() == 'OK'

    def test_download_file_with_options(self, test_server):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = os.path.join(tmpdir, 'test2.txt')
            size, err = download_file_with_options(f'{test_server}/ok', dest, [])
            assert err is None
            assert size > 0
            assert os.path.exists(dest)

    def test_content_type_constants(self):
        assert ContentType.JSON == 'application/json'
        assert ContentType.FORM_URL_ENCODED == 'application/x-www-form-urlencoded'
        assert ContentType.TEXT_PLAIN == 'text/plain'
        assert ContentType.TEXT_HTML == 'text/html'
        assert ContentType.TEXT_XML == 'text/xml'
        assert ContentType.XML == 'application/xml'
        assert ContentType.OCTET_STREAM == 'application/octet-stream'
        assert ContentType.EVENT_STREAM == 'text/event-stream'
        assert ContentType.MULTIPART == 'multipart/form-data'

    def test_method_constants(self):
        assert Method.GET == 'GET'
        assert Method.POST == 'POST'
        assert Method.PUT == 'PUT'
        assert Method.DELETE == 'DELETE'
        assert Method.PATCH == 'PATCH'
        assert Method.HEAD == 'HEAD'
        assert Method.OPTIONS == 'OPTIONS'
        assert Method.TRACE == 'TRACE'
        assert Method.CONNECT == 'CONNECT'

    def test_header_constants(self):
        assert Header.AUTHORIZATION == 'Authorization'
        assert Header.CONTENT_TYPE == 'Content-Type'
        assert Header.USER_AGENT == 'User-Agent'
        assert Header.COOKIE == 'Cookie'
        assert Header.ACCEPT == 'Accept'
        assert Header.LOCATION == 'Location'

    def test_build_basic_auth(self):
        result = build_basic_auth('user', 'pass')
        assert result.startswith('Basic ')

    def test_build_content_type(self):
        assert build_content_type(ContentType.JSON, 'UTF-8') == 'application/json; charset=UTF-8'
        assert build_content_type(ContentType.JSON, '') == 'application/json'

    def test_guess_content_type_json(self):
        assert guess_content_type('{"key": "value"}') == ContentType.JSON
        assert guess_content_type('[1, 2, 3]') == ContentType.JSON

    def test_guess_content_type_html(self):
        assert guess_content_type('<!DOCTYPE html>') == ContentType.TEXT_HTML
        assert guess_content_type('<html>') == ContentType.TEXT_HTML

    def test_guess_content_type_xml(self):
        assert guess_content_type('<?xml version="1.0"?>') == ContentType.XML

    def test_guess_content_type_plain(self):
        assert guess_content_type('hello world') == ContentType.TEXT_PLAIN
        assert guess_content_type('') == ''

    def test_is_form_url_encoded(self):
        assert is_form_url_encoded(ContentType.FORM_URL_ENCODED) is True
        assert is_form_url_encoded(ContentType.JSON) is False

    def test_is_default_content_type(self):
        assert is_default_content_type(ContentType.TEXT_PLAIN) is True
        assert is_default_content_type(ContentType.JSON) is True
        assert is_default_content_type(ContentType.MULTIPART) is False

    def test_get_charset_from_content_type(self):
        assert get_charset_from_content_type('text/html; charset=utf-8') == 'utf-8'
        assert get_charset_from_content_type('text/html') == ''
        assert get_charset_from_content_type('') == ''

    def test_get_charset_from_html(self):
        html = '<html><head><meta charset="utf-8"></head></html>'
        assert get_charset_from_html(html) == 'utf-8'

    def test_get_mime_type(self):
        assert get_mime_type('file.json') == 'application/json'
        assert get_mime_type('file.html') == 'text/html'
        assert get_mime_type('file.txt') == 'text/plain'
        assert get_mime_type('file.png') == 'image/png'
        assert get_mime_type('file.xyz') == 'application/octet-stream'

    def test_is_https(self):
        assert is_https('https://example.com') is True
        assert is_https('http://example.com') is False

    def test_is_http(self):
        assert is_http('http://example.com') is True
        assert is_http('https://example.com') is False

    def test_to_params(self):
        assert to_params({'a': '1', 'b': '2'}) == 'a=1&b=2'

    def test_url_with_form(self):
        result = url_with_form('http://example.com', {'a': '1'})
        assert '?' in result
        assert 'a=1' in result

    def test_url_with_form_existing_query(self):
        result = url_with_form('http://example.com?x=1', {'a': '1'})
        assert 'x=1' in result
        assert 'a=1' in result

    def test_new_http_error(self):
        err = new_http_error('test error', ValueError('cause'))
        assert err.message == 'test error'
        assert err.cause is not None

    def test_http_errorf(self):
        err = http_errorf('error %d', 42)
        assert err.message == 'error 42'

    def test_response_is_ok(self):
        resp = HTTPResponse(status_code=200)
        assert resp.is_ok()
        resp = HTTPResponse(status_code=404)
        assert not resp.is_ok()

    def test_response_content_length(self):
        resp = HTTPResponse(headers={'Content-Length': '42'})
        assert resp.content_length() == 42
        resp = HTTPResponse(headers={})
        assert resp.content_length() == 0

    def test_response_body_bytes(self):
        resp = HTTPResponse(body=b'test')
        assert resp.body_bytes() == b'test'

    def test_response_body_text(self):
        resp = HTTPResponse(text='test')
        assert resp.body_text() == 'test'

    def test_url_policy_defaults(self):
        policy = URLPolicy()
        assert policy.allowed_schemes == ['http', 'https']
        assert policy.allowed_hosts == []
        assert policy.reject_private is True
        assert policy.lookup_ip is None

    def test_url_policy_custom(self):
        policy = URLPolicy(
            allowed_schemes=['https'],
            allowed_hosts=['example.com'],
            reject_private=False
        )
        assert policy.allowed_schemes == ['https']
        assert policy.allowed_hosts == ['example.com']
        assert policy.reject_private is False


class TestGlobalConfig:
    def test_snapshot_global_config(self):
        cfg = snapshot_global_config()
        assert isinstance(cfg, GlobalConfig)

    def test_set_global_timeout(self):
        set_global_timeout(30.0)
        assert get_global_timeout() == 30.0
        set_global_timeout(0.0)
        assert get_global_timeout() == 0.0

    def test_set_global_max_redirects(self):
        set_global_max_redirects(5)
        assert get_global_max_redirects() == 5
        set_global_max_redirects(10)
        assert get_global_max_redirects() == 10

    def test_set_global_user_agent(self):
        set_global_user_agent('TestAgent')
        assert get_global_user_agent() == 'TestAgent'
        set_global_user_agent('')
        assert get_global_user_agent() == ''

    def test_set_global_follow_redirects(self):
        set_global_follow_redirects(False)
        assert get_global_follow_redirects() is False
        set_global_follow_redirects(True)
        assert get_global_follow_redirects() is True

    def test_set_global_max_response_bytes(self):
        set_global_max_response_bytes(1024)
        assert get_global_max_response_bytes() == 1024
        set_global_max_response_bytes(0)
        assert get_global_max_response_bytes() == 0

    def test_set_global_header(self):
        set_global_header('X-Global', 'val')
        headers = clone_global_headers()
        assert 'X-Global' in headers
        assert headers['X-Global'] == ['val']
        remove_global_header('X-Global')
        headers = clone_global_headers()
        assert 'X-Global' not in headers

    def test_add_global_header(self):
        add_global_header('X-Add', 'v1')
        add_global_header('X-Add', 'v2')
        headers = clone_global_headers()
        assert 'X-Add' in headers
        assert len(headers['X-Add']) == 2
        remove_global_header('X-Add')

    def test_close_cookie(self):
        close_cookie()
        cfg = snapshot_global_config()
        assert cfg.cookie_disabled is True
        close_cookie()
        reset_global_config()

    def test_reset_global_config(self):
        set_global_timeout(99.0)
        set_global_header('X-Test', 'v')
        reset_global_config()
        assert get_global_timeout() == 0.0
        headers = clone_global_headers()
        assert 'X-Test' not in headers

    def test_configure_global_config(self):
        reset_global_config()
        cfg = GlobalConfig(timeout=25.0, max_redirects=5, default_user_agent='Test')
        configure_global_config(cfg)
        assert get_global_timeout() == 25.0
        assert get_global_max_redirects() == 5
        assert get_global_user_agent() == 'Test'
        reset_global_config()

    def test_with_scoped_global_config(self):
        reset_global_config()
        cfg = GlobalConfig(timeout=50.0)
        results = []

        def fn():
            results.append(get_global_timeout())

        with_scoped_global_config(cfg, fn)
        assert results[0] == 50.0
        assert get_global_timeout() == 0.0


class TestClient:
    def test_new_client(self):
        client = new_client()
        assert isinstance(client, Client)

    def test_new_isolated_client(self):
        client = new_isolated_client()
        assert isinstance(client, Client)

    def test_new_client_with_config(self):
        cfg = GlobalConfig(timeout=10.0, follow_redirects=True)
        client = new_client_with_config(cfg, [])
        assert isinstance(client, Client)

    def test_client_get(self, test_server):
        client = new_client()
        resp = client.get(f'{test_server}/ok').execute()
        assert resp.is_ok()

    def test_client_post(self, test_server):
        client = new_client()
        resp = client.post(f'{test_server}/echo').body_string('data').execute()
        assert resp.is_ok()


class TestSafe:
    def test_safe_get_ok(self, test_server):
        policy = URLPolicy(
            allowed_schemes=['http'],
            allowed_hosts=['127.0.0.1'],
            reject_private=False
        )
        resp = new_safe_request(Method.GET, f'{test_server}/ok', with_url_policy(policy)).execute()
        assert resp.is_ok()

    def test_safe_post_ok(self, test_server):
        policy = URLPolicy(
            allowed_schemes=['http'],
            allowed_hosts=['127.0.0.1'],
            reject_private=False
        )
        resp = new_safe_request(Method.POST, f'{test_server}/echo', with_url_policy(policy)).body_string('data').execute()
        assert resp.is_ok()

    def test_with_url_policy(self, test_server):
        policy = URLPolicy(
            allowed_schemes=['http'],
            allowed_hosts=['127.0.0.1'],
            reject_private=False
        )
        resp = get(f'{test_server}/ok', with_url_policy(policy)).execute()
        assert resp.is_ok()

    def test_url_policy_rejects_private(self, test_server):
        policy = URLPolicy(
            allowed_schemes=['http'],
            allowed_hosts=['127.0.0.1'],
            reject_private=True
        )
        resp = get(f'{test_server}/ok', with_url_policy(policy)).execute()
        assert resp.err is not None


class TestMethodConstants:
    def test_method_get(self):
        assert Method.GET == 'GET'

    def test_method_post(self):
        assert Method.POST == 'POST'

    def test_method_put(self):
        assert Method.PUT == 'PUT'

    def test_method_delete(self):
        assert Method.DELETE == 'DELETE'

    def test_method_patch(self):
        assert Method.PATCH == 'PATCH'

    def test_method_head(self):
        assert Method.HEAD == 'HEAD'

    def test_method_options(self):
        assert Method.OPTIONS == 'OPTIONS'

    def test_method_trace(self):
        assert Method.TRACE == 'TRACE'

    def test_method_connect(self):
        assert Method.CONNECT == 'CONNECT'