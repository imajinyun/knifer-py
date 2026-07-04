import pytest

from kniferpy import vnet
from kniferpy.verr import ValidationError


def test_ip_type_detection() -> None:
    assert vnet.is_ip("127.0.0.1")
    assert vnet.is_ip("::1")
    assert not vnet.is_ip("not-an-ip")
    assert vnet.is_ipv4("192.168.0.1")
    assert not vnet.is_ipv4("::1")
    assert vnet.is_ipv6("2001:db8::1")
    assert not vnet.is_ipv6("192.168.0.1")


def test_inner_ip() -> None:
    assert vnet.is_inner_ip("127.0.0.1")
    assert vnet.is_inner_ip("10.0.0.1")
    assert vnet.is_inner_ip("192.168.1.1")
    assert vnet.is_inner_ip("169.254.1.1")
    assert vnet.is_inner_ip("::1")
    assert not vnet.is_inner_ip("8.8.8.8")
    assert not vnet.is_inner_ip("bad")


def test_ipv4_long_roundtrip() -> None:
    value = vnet.ipv4_to_long("1.2.3.4")
    assert value == 0x01020304
    assert vnet.long_to_ipv4(value) == "1.2.3.4"
    assert vnet.ipv4_to_long_default("bad", 42) == 42
    with pytest.raises(ValidationError):
        vnet.ipv4_to_long("999.1.1.1")
    with pytest.raises(ValidationError):
        vnet.long_to_ipv4(-1)


def test_ipv6_int_roundtrip() -> None:
    value = vnet.ipv6_to_int("::1")
    assert value == 1
    assert vnet.int_to_ipv6(value) == "::1"
    with pytest.raises(ValidationError):
        vnet.ipv6_to_int("192.168.0.1")


def test_cidr_range_and_membership() -> None:
    assert vnet.is_in_range("192.168.1.5", "192.168.1.0/24")
    assert not vnet.is_in_range("192.168.2.5", "192.168.1.0/24")
    assert not vnet.is_in_range("::1", "192.168.1.0/24")
    assert vnet.first_ip("192.168.1.0/24") == "192.168.1.0"
    assert vnet.last_ip("192.168.1.0/24") == "192.168.1.255"
    assert vnet.address_count("192.168.1.0/24") == 256
    with pytest.raises(ValidationError):
        vnet.first_ip("nope")


def test_wildcard_matching() -> None:
    assert vnet.matches_wildcard("192.168.*.*", "192.168.1.5")
    assert not vnet.matches_wildcard("192.168.*.*", "10.0.0.1")
    assert not vnet.matches_wildcard("192.168.*", "192.168.1.5")
    assert not vnet.matches_wildcard("192.168.1.5", "::1")


def test_hide_ip_part() -> None:
    assert vnet.hide_ip_part("1.2.3.4") == "1.2.3.*"
    assert vnet.hide_ip_part("no-dot") == "no-dot"
    assert vnet.hide_ip_part_long(0x01020304) == "1.2.3.*"


def test_valid_port() -> None:
    assert vnet.is_valid_port(0)
    assert vnet.is_valid_port(65535)
    assert not vnet.is_valid_port(-1)
    assert not vnet.is_valid_port(65536)


# ---------------------------------------------------------------------------
# TLS
# ---------------------------------------------------------------------------


class TestTLS:
    def test_create_tls_config(self) -> None:
        ctx = vnet.create_tls_config()
        assert ctx is not None

    def test_tls_config_builder(self) -> None:
        builder = vnet.new_tls_config_builder()
        builder.set_min_version("TLSv1.2")
        builder.set_max_version("TLSv1.3")
        ctx = builder.build()
        assert ctx is not None

    def test_tls_version_mapping(self) -> None:
        assert vnet.tls_version("TLSv1.2") > 0
        assert vnet.tls_version("TLSv1.3") > 0


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------


class TestDNS:
    def test_get_ip_by_host_localhost(self) -> None:
        ips = vnet.get_ip_by_host("localhost")
        assert "127.0.0.1" in ips or "::1" in ips

    def test_get_dns_info_localhost(self) -> None:
        info = vnet.get_dns_info("localhost", ["A", "AAAA"])
        assert "A" in info
        assert "AAAA" in info

    def test_get_dns_info_bad_host(self) -> None:
        info = vnet.get_dns_info("this.host.does.not.exist.xyz123", ["A"])
        assert info["A"] == []

    def test_idn_to_ascii(self) -> None:
        assert vnet.idn_to_ascii("example.com") == "example.com"


# ---------------------------------------------------------------------------
# TCP Ping / Connect
# ---------------------------------------------------------------------------


class TestPingConnect:
    def test_ping_invalid_host(self) -> None:
        assert not vnet.ping("255.255.255.255", 12345, timeout=0.5)

    def test_is_open_invalid(self) -> None:
        assert not vnet.is_open("255.255.255.255", 12345, timeout=0.5)

    def test_is_connected_none(self) -> None:
        assert not vnet.is_connected(None)


# ---------------------------------------------------------------------------
# Multipart
# ---------------------------------------------------------------------------


class TestMultipart:
    def test_parse_multipart_form_text_fields(self) -> None:
        boundary = "----TestBoundary"
        body = (
            f"------TestBoundary\r\n"
            f'Content-Disposition: form-data; name="field1"\r\n'
            f"\r\n"
            f"value1\r\n"
            f"------TestBoundary\r\n"
            f'Content-Disposition: form-data; name="field2"\r\n'
            f"\r\n"
            f"value2\r\n"
            f"------TestBoundary--\r\n"
        ).encode("utf-8")
        content_type = f"multipart/form-data; boundary=----TestBoundary"

        form = vnet.parse_multipart_form(body, content_type)
        assert form.is_loaded()
        assert form.get_param("field1") == "value1"
        assert form.get_param("field2") == "value2"
        assert form.get_param("missing") == ""

    def test_parse_multipart_form_file(self) -> None:
        boundary = "----TestBoundary"
        body = (
            f"------TestBoundary\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            f"Content-Type: text/plain\r\n"
            f"\r\n"
            f"hello world\r\n"
            f"------TestBoundary--\r\n"
        ).encode("utf-8")
        content_type = f"multipart/form-data; boundary=----TestBoundary"

        form = vnet.parse_multipart_form(body, content_type)
        file_entry = form.get_file("file")
        assert file_entry is not None
        assert vnet.upload_file_name(file_entry) == "test.txt"
        assert vnet.upload_file_size(file_entry) == 11
        assert vnet.upload_file_content_type(file_entry) == "text/plain"

    def test_multipart_no_boundary(self) -> None:
        with pytest.raises(ValidationError):
            vnet.parse_multipart_form(b"data", "multipart/form-data")

    def test_upload_setting(self) -> None:
        setting = vnet.UploadSetting(max_file_size=1024)
        assert setting.max_file_size == 1024

    def test_save_uploaded_file(self, tmp_path) -> None:
        entry = ("test.txt", b"hello", "text/plain")
        path = vnet.save_uploaded_file(entry, str(tmp_path))
        assert path.endswith("test.txt")
        assert (tmp_path / "test.txt").read_bytes() == b"hello"

    def test_save_uploaded_file_no_overwrite(self, tmp_path) -> None:
        (tmp_path / "test.txt").write_bytes(b"existing")
        entry = ("test.txt", b"hello", "text/plain")
        with pytest.raises(ValidationError):
            vnet.save_uploaded_file(entry, str(tmp_path))
