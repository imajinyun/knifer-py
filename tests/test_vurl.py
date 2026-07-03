import pytest

from kniferpy import vurl
from kniferpy.verr import SecurityError, ValidationError


def test_validate_http_url_allows_expected_host() -> None:
    assert vurl.validate_http_url(
        "https://api.example.com/health",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
    )


def test_validate_http_url_rejects_private_host() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://127.0.0.1:8000")
    assert exc_info.value.code == "url.private_host"


def test_validate_http_url_rejects_unlisted_host() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url(
            "https://evil.example.com",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
        )
    assert exc_info.value.code == "url.host_not_allowed"


def test_validate_http_url_rejects_non_http_scheme() -> None:
    with pytest.raises(ValidationError) as exc_info:
        vurl.validate_http_url("file:///tmp/data.txt")
    assert exc_info.value.code == "url.invalid"


def test_validate_http_url_rejects_ftp_scheme() -> None:
    with pytest.raises(ValidationError) as exc_info:
        vurl.validate_http_url("ftp://example.com/file")
    assert exc_info.value.code == "url.invalid"


def test_validate_http_url_no_hostname() -> None:
    with pytest.raises(ValidationError) as exc_info:
        vurl.validate_http_url("http://")
    assert exc_info.value.code == "url.invalid"


def test_validate_http_url_allowed_hosts_case_insensitive() -> None:
    assert vurl.validate_http_url(
        "https://API.Example.COM/health",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
    )


def test_validate_http_url_loopback_rejected() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://localhost:3000")
    assert exc_info.value.code == "url.private_host"


def test_validate_http_url_link_local_rejected() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://169.254.1.1")
    assert exc_info.value.code == "url.private_host"


def test_validate_http_url_private_range_rejected() -> None:
    with pytest.raises(SecurityError) as exc_info:
        vurl.validate_http_url("http://10.0.0.1")
    assert exc_info.value.code == "url.private_host"


def test_is_private_host() -> None:
    assert vurl.is_private_host("127.0.0.1")
    assert vurl.is_private_host("10.0.0.1")
    assert vurl.is_private_host("192.168.1.1")
    assert vurl.is_private_host("172.16.0.1")
    assert vurl.is_private_host("::1")
    assert not vurl.is_private_host("93.184.216.34")


def test_normalize_query_sorts_parameters() -> None:
    assert vurl.normalize_query("https://example.com/path?b=2&a=1") == (
        "https://example.com/path?a=1&b=2"
    )


def test_normalize_query_no_query() -> None:
    assert vurl.normalize_query("https://example.com/path") == "https://example.com/path"


def test_add_and_get_query() -> None:
    url = vurl.add_query(
        "https://example.com/path?a=1",
        {"b": 2, "enabled": True, "skip": None},
    )
    assert url == "https://example.com/path?a=1&b=2&enabled=true"
    assert vurl.get_query(url) == {"a": "1", "b": "2", "enabled": "true"}


def test_add_query_bool_values() -> None:
    url = vurl.add_query("https://example.com/path", {"flag": False, "on": True})
    assert "flag=false" in url
    assert "on=true" in url


def test_add_query_float_value() -> None:
    url = vurl.add_query("https://example.com/path", {"pi": 3.14})
    assert "pi=3.14" in url


def test_remove_query_and_redact_userinfo() -> None:
    assert vurl.remove_query("https://example.com/path?a=1&b=2", {"a"}) == (
        "https://example.com/path?b=2"
    )
    assert vurl.redact_userinfo("https://user:pass@example.com:8443/path") == (
        "https://***@example.com:8443/path"
    )
    assert vurl.redact_userinfo("https://example.com/path") == "https://example.com/path"


def test_remove_query_all() -> None:
    assert vurl.remove_query("https://example.com/path?a=1&b=2", {"a", "b"}) == (
        "https://example.com/path"
    )


def test_redact_userinfo_custom_replacement() -> None:
    result = vurl.redact_userinfo(
        "https://user:pass@example.com/path", replacement="REDACTED"
    )
    assert result == "https://REDACTED@example.com/path"


def test_redact_userinfo_no_userinfo() -> None:
    assert vurl.redact_userinfo("https://example.com/path") == "https://example.com/path"


def test_parse_url() -> None:
    parsed = vurl.parse("https://example.com:8080/path?a=1")
    assert parsed.scheme == "https"
    assert parsed.hostname == "example.com"
    assert parsed.port == 8080
    assert parsed.path == "/path"
    assert parsed.query == "a=1"


def test_get_query_empty() -> None:
    assert vurl.get_query("https://example.com/path") == {}