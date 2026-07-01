from kniferpy import vurl
from kniferpy.verr import SecurityError, ValidationError


def test_validate_http_url_allows_expected_host() -> None:
    assert vurl.validate_http_url(
        "https://api.example.com/health",
        allowed_hosts={"api.example.com"},
        resolver=lambda host: ["93.184.216.34"],
    )


def test_validate_http_url_rejects_private_host() -> None:
    try:
        vurl.validate_http_url("http://127.0.0.1:8000")
    except SecurityError as err:
        assert err.code == "url.private_host"
    else:
        raise AssertionError("expected SecurityError")


def test_validate_http_url_rejects_unlisted_host() -> None:
    try:
        vurl.validate_http_url(
            "https://evil.example.com",
            allowed_hosts={"api.example.com"},
            resolver=lambda host: ["93.184.216.34"],
        )
    except SecurityError as err:
        assert err.code == "url.host_not_allowed"
    else:
        raise AssertionError("expected SecurityError")


def test_validate_http_url_rejects_non_http_scheme() -> None:
    try:
        vurl.validate_http_url("file:///tmp/data.txt")
    except ValidationError as err:
        assert err.code == "url.invalid"
    else:
        raise AssertionError("expected ValidationError")


def test_normalize_query_sorts_parameters() -> None:
    assert vurl.normalize_query("https://example.com/path?b=2&a=1") == (
        "https://example.com/path?a=1&b=2"
    )


def test_add_and_get_query() -> None:
    url = vurl.add_query(
        "https://example.com/path?a=1",
        {"b": 2, "enabled": True, "skip": None},
    )

    assert url == "https://example.com/path?a=1&b=2&enabled=true"
    assert vurl.get_query(url) == {"a": "1", "b": "2", "enabled": "true"}


def test_remove_query_and_redact_userinfo() -> None:
    assert vurl.remove_query("https://example.com/path?a=1&b=2", {"a"}) == (
        "https://example.com/path?b=2"
    )
    assert vurl.redact_userinfo("https://user:pass@example.com:8443/path") == (
        "https://***@example.com:8443/path"
    )
    assert vurl.redact_userinfo("https://example.com/path") == "https://example.com/path"
