# mypy: disable-error-code="no-untyped-def"

import io
import os
import socket
import ssl
import uuid
from typing import cast

import pytest

from kniferpy import vnet
from kniferpy.internal import netx
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
    assert not vnet.matches_wildcard("192.168.bad.*", "192.168.1.5")
    assert not vnet.matches_wildcard("192.168.999.*", "192.168.1.5")


def test_hide_ip_part() -> None:
    assert vnet.hide_ip_part("1.2.3.4") == "1.2.3.*"
    assert vnet.hide_ip_part("no-dot") == "no-dot"
    assert vnet.hide_ip_part_long(0x01020304) == "1.2.3.*"


def test_valid_port() -> None:
    assert vnet.is_valid_port(0)
    assert vnet.is_valid_port(65535)
    assert not vnet.is_valid_port(-1)
    assert not vnet.is_valid_port(65536)


def test_ipv4_ipv6_error_paths() -> None:
    assert netx._parse("bad") is None
    assert netx._network("bad") is None
    with pytest.raises(ValidationError) as ipv6_exc:
        vnet.int_to_ipv6(-1)
    with pytest.raises(ValidationError) as ipv6_high_exc:
        vnet.int_to_ipv6(netx.IPV6_MAX + 1)
    with pytest.raises(ValidationError) as cidr_exc:
        vnet.last_ip("bad")
    with pytest.raises(ValidationError) as count_exc:
        vnet.address_count("bad")
    assert ipv6_exc.value.code == "knifer.net.ipv6_out_of_range"
    assert ipv6_high_exc.value.code == "knifer.net.ipv6_out_of_range"
    assert cidr_exc.value.code == "knifer.net.invalid_cidr"
    assert count_exc.value.code == "knifer.net.invalid_cidr"


def test_subnet_math_success_and_errors() -> None:
    assert vnet.mask_bit_by_mask("255.255.255.0") == 24
    assert vnet.mask_bit_by_mask_with_options("255.255.0.0") == 16
    assert vnet.count_by_mask_bit(30) == 2
    assert vnet.count_by_mask_bit(30, is_all=True) == 4
    assert vnet.mask_by_mask_bit(24) == "255.255.255.0"
    assert vnet.mask_by_ip_range("192.168.1.0", "192.168.1.255") == "255.255.255.0"
    assert vnet.mask_by_ip_range_with_options("192.168.1.1", "192.168.1.1") == ("255.255.255.255")
    assert vnet.count_by_ip_range("192.168.1.1", "192.168.1.3") == 3
    assert vnet.count_by_ip_range_with_options("192.168.1.1", "192.168.1.3") == 3
    assert vnet.format_ip_block("192.168.1.1", "255.255.255.0") == "192.168.1.1/24"
    assert vnet.format_ip_block_with_options("192.168.1.1", "255.255.255.0") == ("192.168.1.1/24")
    assert vnet.begin_ip("192.168.1.42", 24) == "192.168.1.0"
    assert vnet.begin_ip_with_options("192.168.1.42", 24) == "192.168.1.0"
    assert vnet.begin_ip_long("192.168.1.42", 24) == vnet.ipv4_to_long("192.168.1.0")
    assert vnet.begin_ip_long_with_options("192.168.1.42", 24) == vnet.ipv4_to_long("192.168.1.0")
    assert vnet.end_ip("192.168.1.42", 24) == "192.168.1.255"
    assert vnet.end_ip_with_options("192.168.1.42", 24) == "192.168.1.255"
    assert vnet.end_ip_long("192.168.1.42", 24) == vnet.ipv4_to_long("192.168.1.255")
    assert vnet.end_ip_long_with_options("192.168.1.42", 24) == vnet.ipv4_to_long("192.168.1.255")
    assert vnet.is_mask_valid("255.255.255.0")
    assert not vnet.is_mask_valid("255.0.255.0")
    assert vnet.is_mask_valid_with_options("255.255.0.0")
    assert vnet.is_mask_bit_valid(0)
    assert vnet.is_mask_bit_valid(32)
    assert not vnet.is_mask_bit_valid(33)
    assert vnet.list_ips("192.168.1.0/30") == ["192.168.1.1", "192.168.1.2"]
    assert vnet.list_ips_with_options("192.168.1.0/30", is_all=True) == [
        "192.168.1.0",
        "192.168.1.1",
        "192.168.1.2",
        "192.168.1.3",
    ]
    assert vnet.list_ip_cidr("192.168.1.42", 30) == ["192.168.1.41", "192.168.1.42"]
    assert vnet.list_ip_cidr_with_options("192.168.1.42", 30, is_all=True)[0] == ("192.168.1.40")
    assert vnet.list_ip_range("192.168.1.1", "192.168.1.3") == [
        "192.168.1.1",
        "192.168.1.2",
        "192.168.1.3",
    ]
    assert vnet.list_ip_range_with_options("192.168.1.1", "192.168.1.2") == [
        "192.168.1.1",
        "192.168.1.2",
    ]

    for func, args in (
        (vnet.mask_bit_by_mask, ("255.0.255.0",)),
        (vnet.count_by_mask_bit, (33,)),
        (vnet.mask_by_mask_bit, (-1,)),
        (vnet.mask_by_ip_range, ("bad", "192.168.1.1")),
        (vnet.count_by_ip_range, ("bad", "192.168.1.1")),
        (vnet.format_ip_block, ("bad", "255.255.255.0")),
        (vnet.begin_ip, ("bad", 24)),
        (vnet.begin_ip, ("192.168.1.1", 33)),
        (vnet.end_ip, ("bad", 24)),
        (vnet.end_ip, ("192.168.1.1", 33)),
        (vnet.list_ips, ("bad",)),
        (vnet.list_ip_cidr, ("bad", 24)),
        (vnet.list_ip_range, ("192.168.1.3", "192.168.1.1")),
    ):
        with pytest.raises(ValidationError):
            func(*args)


def test_constants_and_with_options_aliases() -> None:
    assert vnet.LOCAL_IP == "127.0.0.1"
    assert vnet.IP_SPLIT_MARK == "-"
    assert vnet.IP_MASK_SPLIT_MARK == "/"
    assert vnet.IP_MASK_MAX == 32
    assert vnet.PORT_RANGE_MIN == 1024
    assert vnet.PORT_RANGE_MAX == 65535
    assert vnet.SSL == "SSL"
    assert vnet.TLSv12 == "TLSv1.2"
    assert vnet.TLSv13 == "TLSv1.3"
    assert vnet.is_ip_with_options("127.0.0.1")
    assert vnet.is_ipv4_with_options("127.0.0.1")
    assert vnet.is_ipv6_with_options("::1")
    assert vnet.is_inner_ip_with_options("127.0.0.1")
    assert vnet.ipv4_to_long_with_options("1.2.3.4") == 0x01020304
    assert vnet.ipv4_to_long_default_with_options("bad", 9) == 9
    assert vnet.ipv6_to_int_with_options("::1") == 1
    assert vnet.ipv6_to_big_int("::1") == 1
    assert vnet.ipv6_to_big_int_with_options("::1") == 1
    assert vnet.big_int_to_ipv6(1) == "::1"
    assert vnet.is_in_range_with_options("192.168.1.1", "192.168.1.0/24")
    assert vnet.matches_wildcard_with_options("192.168.*.*", "192.168.1.1")


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
        assert vnet.tls_version("unknown") == ssl.PROTOCOL_TLS

    def test_tls_builder_server_name_and_unknown_versions(self) -> None:
        builder = vnet.new_tls_config_builder()
        assert builder.set_min_version("unknown") is builder
        assert builder.set_max_version("unknown") is builder
        assert builder.set_server_name("example.com") is builder
        assert builder.build().check_hostname is True
        assert vnet.new_cert_pool() is not None

    def test_add_root_ca_helpers_call_builder(self) -> None:
        class Builder:
            def __init__(self) -> None:
                self.files: list[str] = []
                self.data: list[bytes] = []

            def add_root_ca_file(self, path: str) -> None:
                self.files.append(path)

            def add_root_ca_bytes(self, data: bytes) -> None:
                self.data.append(data)

        builder = Builder()
        vnet.add_root_ca_file_with_options(builder, "/tmp/ca.pem")
        vnet.add_root_ca_reader(builder, io.BytesIO(b"ca"))
        vnet.add_root_ca_reader_with_options(builder, io.BytesIO(b"ca2"))
        assert builder.files == ["/tmp/ca.pem"]
        assert builder.data == [b"ca", b"ca2"]


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

    def test_dns_with_monkeypatched_getaddrinfo(self, monkeypatch) -> None:
        answers = [
            (socket.AF_INET, None, None, None, ("127.0.0.1", 0)),
            (socket.AF_INET6, None, None, None, ("::1", 0)),
        ]

        monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: answers)
        assert vnet.get_dns_info("localhost", ["A", "AAAA", "MX", "TXT"]) == {
            "A": ["127.0.0.1"],
            "AAAA": ["::1"],
            "MX": [],
            "TXT": [],
        }
        assert vnet.get_dns_info_with_options("localhost", ["A"]) == {"A": ["127.0.0.1"]}
        assert vnet.get_ip_by_host("localhost") == ["127.0.0.1", "::1"]
        assert vnet.get_ip_by_host_with_options("localhost") == ["127.0.0.1", "::1"]

        def raise_gaierror(*args, **kwargs):
            raise socket.gaierror()

        monkeypatch.setattr(socket, "getaddrinfo", raise_gaierror)
        assert vnet.get_ip_by_host("bad") == []
        assert vnet.get_dns_info("bad", ["A"]) == {"A": []}


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

    def test_connect_ping_netcat_with_monkeypatched_socket(self, monkeypatch) -> None:
        sent: list[bytes] = []

        class FakeSocket:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def sendall(self, data: bytes) -> None:
                sent.append(data)

            def getpeername(self):
                return ("127.0.0.1", 8080)

        fake = FakeSocket()
        monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: fake)

        assert vnet.ping("127.0.0.1", 80)
        assert vnet.ping_with_options("127.0.0.1", 80)
        assert vnet.is_open_with_options("127.0.0.1", 80)
        assert vnet.connect("127.0.0.1", 80) is fake  # type: ignore[comparison-overlap]
        assert vnet.connect_with_options("127.0.0.1", 80) is fake  # type: ignore[comparison-overlap]
        assert vnet.is_connected(cast(socket.socket, fake)) is True
        vnet.netcat("127.0.0.1", 80, b"hello")
        vnet.netcat_with_options("127.0.0.1", 80, b"world")
        assert sent == [b"hello", b"world"]
        assert vnet.get_remote_address(cast(socket.socket, fake)) == "127.0.0.1:8080"

        def fail_connection(*args, **kwargs):
            raise OSError("closed")

        monkeypatch.setattr(socket, "create_connection", fail_connection)
        assert not vnet.ping("127.0.0.1", 80)
        assert vnet.connect("127.0.0.1", 80) is None
        with pytest.raises(ValidationError) as exc_info:
            vnet.netcat("127.0.0.1", 80, b"boom")
        assert exc_info.value.code == "knifer.net.netcat_failed"

    def test_is_connected_and_remote_address_error_paths(self) -> None:
        class BrokenSocket:
            def getpeername(self):
                raise OSError("not connected")

        assert not vnet.is_connected(cast(socket.socket, BrokenSocket()))
        assert vnet.get_remote_address(cast(socket.socket, BrokenSocket())) == ""


def test_port_helpers_with_monkeypatched_socket(monkeypatch) -> None:
    busy = {1001}

    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def bind(self, addr):
            host, port = addr
            if port in busy:
                raise OSError("busy")

    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: FakeSocket())

    assert not vnet.is_usable_local_port(-1)
    assert vnet.is_usable_local_port(1000)
    assert not vnet.is_usable_local_port(1001)
    assert vnet.is_usable_local_port_with_options(1000)
    assert vnet.get_usable_local_port_from(1000) == 1000
    assert vnet.get_usable_local_port_from_with_options(1000) == 1000
    assert vnet.get_usable_local_port_in_range(1001, 1002) == 1002
    assert vnet.get_usable_local_port_in_range_with_options(1001, 1002) == 1002
    assert vnet.get_usable_local_ports(2, 1000, 1002) == [1000, 1002]
    assert vnet.get_usable_local_ports_with_options(1, 1000, 1000) == [1000]
    with pytest.raises(ValidationError):
        vnet.get_usable_local_port_in_range(1001, 1001)
    with pytest.raises(ValidationError):
        vnet.get_usable_local_ports(3, 1000, 1002)

    generator = vnet.new_local_port_generator(vnet.PORT_RANGE_MAX)
    assert generator.gen() == vnet.PORT_RANGE_MAX
    assert generator.gen() == vnet.PORT_RANGE_MIN
    assert vnet.new_local_port_generator_with_options(2000).gen() == 2000


def test_address_and_local_interface_helpers(monkeypatch) -> None:
    answers = [
        (socket.AF_INET, None, None, None, ("10.0.0.2", 0)),
        (socket.AF_INET6, None, None, None, ("fe80::1", 0)),
        (socket.AF_INET6, None, None, None, ("2001:db8::1", 0)),
    ]
    monkeypatch.setattr(socket, "gethostname", lambda: "host")
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: answers)

    assert vnet.build_inet_socket_address("example.com:8443", 443) == ("example.com", 8443)
    assert vnet.build_inet_socket_address("example.com", 443) == ("example.com", 443)
    assert vnet.build_inet_socket_address_with_options("example.com:8443", 443) == (
        "example.com",
        8443,
    )
    assert vnet.create_address("example.com", 443) == ("example.com", 443)
    assert vnet.create_address_with_options("example.com", 443) == ("example.com", 443)
    assert vnet.get_network_interface("lo") is None
    assert vnet.get_network_interface_with_options("lo") is None
    assert vnet.get_network_interfaces() == {}
    assert vnet.get_network_interfaces_with_options() == {}
    assert "10.0.0.2" in vnet.local_ipv4s()
    assert "2001:db8::1" in vnet.local_ipv6s()
    assert "127.0.0.1" in vnet.local_ips()
    assert vnet.local_ipv4s_with_options()
    assert vnet.local_ipv6s_with_options()
    assert vnet.local_ips_with_options()
    assert vnet.to_ip_list(["b", "a", "a"]) == ["a", "b"]
    assert vnet.local_address_list(lambda ip: ip == "127.0.0.1") == ["127.0.0.1"]
    assert vnet.local_address_list_with_options(lambda ip: ip == "127.0.0.1") == ["127.0.0.1"]
    assert vnet.get_localhost_str() == "127.0.0.1"
    assert vnet.get_localhost() == "127.0.0.1"
    assert vnet.get_localhost_str_with_options() == "127.0.0.1"
    assert vnet.get_localhost_with_options() == "127.0.0.1"
    assert vnet.get_local_host_name() == "host"
    assert vnet.get_local_host_name_with_options() == "host"


def test_local_ips_gaierror_and_interface_address_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *args, **kwargs: (_ for _ in ()).throw(socket.gaierror())
    )
    assert vnet.local_ipv4s() == ["127.0.0.1"]
    assert vnet.local_ipv6s() == []
    assert vnet.local_ips() == ["127.0.0.1"]
    assert netx._get_interface_addresses() == []


def test_mac_and_hardware_helpers(monkeypatch) -> None:
    monkeypatch.setattr(uuid, "getnode", lambda: 0x001122334455)
    assert vnet.get_local_mac_address() == "00-11-22-33-44-55"
    assert vnet.get_local_mac_address_with_options(":") == "00:11:22:33:44:55"
    assert vnet.get_mac_address("127.0.0.1") == "00-11-22-33-44-55"
    assert vnet.get_mac_address_with_options("127.0.0.1", ":") == "00:11:22:33:44:55"
    assert vnet.get_hardware_address("127.0.0.1") == "00:11:22:33:44:55"
    assert vnet.get_hardware_address_with_options("127.0.0.1") == "00:11:22:33:44:55"
    assert vnet.get_local_hardware_address() == "00:11:22:33:44:55"
    assert vnet.get_local_hardware_address_with_options() == "00:11:22:33:44:55"


def test_misc_cookie_proxy_and_interface_address_helpers(monkeypatch) -> None:
    assert vnet.is_unknown("unknown")
    assert vnet.is_unknown(" N/A ")
    assert not vnet.is_unknown("127.0.0.1")
    assert vnet.parse_cookies("a=1; empty=; bad; b=2") == {"a": "1", "empty": "", "b": "2"}
    assert vnet.get_multistage_reverse_proxy_ip({"X-Forwarded-For": "1.1.1.1, 2.2.2.2"}) == (
        "1.1.1.1"
    )
    assert (
        vnet.get_multistage_reverse_proxy_ip({"X-Forwarded-For": "unknown", "X-Real-IP": "3.3.3.3"})
        == "3.3.3.3"
    )
    assert vnet.get_multistage_reverse_proxy_ip({}) == ""

    monkeypatch.setattr(
        netx,
        "_get_interface_addresses",
        lambda: [("lo", ["127.0.0.1"]), ("eth0", ["10.0.0.1"])],
    )
    assert vnet.local_address_list_by_interface() == ["127.0.0.1", "10.0.0.1"]
    assert vnet.local_address_list_by_interface(lambda iface: iface == "eth0") == ["10.0.0.1"]
    assert vnet.local_address_list_by_interface(None, lambda addr: addr.startswith("127.")) == [
        "127.0.0.1"
    ]
    assert vnet.parse_cookies("broken") == {}
    assert vnet.get_multistage_reverse_proxy_ip({"Proxy-Client-IP": "4.4.4.4"}) == "4.4.4.4"


# ---------------------------------------------------------------------------
# Multipart
# ---------------------------------------------------------------------------


class TestMultipart:
    def test_parse_multipart_form_text_fields(self) -> None:
        body = (
            b"------TestBoundary\r\n"
            b'Content-Disposition: form-data; name="field1"\r\n'
            b"\r\n"
            b"value1\r\n"
            b"------TestBoundary\r\n"
            b'Content-Disposition: form-data; name="field2"\r\n'
            b"\r\n"
            b"value2\r\n"
            b"------TestBoundary--\r\n"
        )
        content_type = "multipart/form-data; boundary=----TestBoundary"

        form = vnet.parse_multipart_form(body, content_type)
        assert form.is_loaded()
        assert form.get_param("field1") == "value1"
        assert form.get_param("field2") == "value2"
        assert form.get_param("missing") == ""

    def test_parse_multipart_form_file(self) -> None:
        body = (
            b"------TestBoundary\r\n"
            b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"hello world\r\n"
            b"------TestBoundary--\r\n"
        )
        content_type = "multipart/form-data; boundary=----TestBoundary"

        form = vnet.parse_multipart_form(body, content_type)
        file_entry = form.get_file("file")
        assert file_entry is not None
        assert vnet.upload_file_name(file_entry) == "test.txt"
        assert vnet.upload_file_size(file_entry) == 11
        assert vnet.upload_file_content_type(file_entry) == "text/plain"

    def test_multipart_form_maps_and_multiple_values(self) -> None:
        body = (
            b"------TestBoundary\r\n"
            b'Content-Disposition: form-data; name="field"\r\n'
            b"\r\n"
            b"value1\r\n"
            b"------TestBoundary\r\n"
            b'Content-Disposition: form-data; name="field"\r\n'
            b"\r\n"
            b"value2\r\n"
            b"------TestBoundary\r\n"
            b'Content-Disposition: form-data; name="file"; filename="a.txt"\r\n'
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"a\r\n"
            b"------TestBoundary--\r\n"
        )
        form = vnet.parse_multipart_form(body, "multipart/form-data; boundary=----TestBoundary")
        assert form.get_param_names() == ["field"]
        assert form.get_array_param("field") == ["value1", "value2"]
        assert form.get_param_map() == {"field": "value1"}
        assert form.get_param_list_map() == {"field": ["value1", "value2"]}
        assert form.get_file_param_names() == ["file"]
        assert form.get_file_map()["file"][0] == "a.txt"
        assert form.get_file_list("file")[0][1] == b"a"
        assert form.get_file_list_value_map()["file"][0][2] == "text/plain"

    def test_multipart_file_filters_limits_and_save(self, tmp_path) -> None:
        body = (
            b"------TestBoundary\r\n"
            b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"hello\r\n"
            b"------TestBoundary--\r\n"
        )
        content_type = "multipart/form-data; boundary=----TestBoundary"
        skipped = vnet.parse_multipart_form(
            body,
            content_type,
            vnet.UploadSetting(file_exts=[".png"]),
        )
        assert skipped.get_file("file") is None
        with pytest.raises(ValidationError) as ext_exc:
            vnet.parse_multipart_form(
                body, content_type, vnet.UploadSetting(allow_file_exts=[".png"])
            )
        assert ext_exc.value.code == "knifer.net.file_ext_not_allowed"
        with pytest.raises(ValidationError) as size_exc:
            vnet.parse_multipart_form(body, content_type, vnet.UploadSetting(max_file_size=1))
        assert size_exc.value.code == "knifer.net.file_too_large"

        form = vnet.parse_multipart_form(body, content_type)
        file_entry = form.get_file("file")
        assert file_entry is not None
        saved = vnet.save_uploaded_file(file_entry, str(tmp_path), "saved.txt")
        assert os.path.exists(saved)
        with pytest.raises(ValidationError) as exists_exc:
            vnet.save_uploaded_file(file_entry, str(tmp_path), "saved.txt")
        assert exists_exc.value.code == "knifer.net.file_exists"
        overwritten = vnet.save_uploaded_file(
            file_entry, str(tmp_path), "saved.txt", overwrite=True
        )
        assert overwritten == saved

    def test_multipart_no_boundary(self) -> None:
        with pytest.raises(ValidationError):
            vnet.parse_multipart_form(b"data", "multipart/form-data")


def test_tls_root_ca_error_paths() -> None:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with pytest.raises(ssl.SSLError):
        vnet.add_root_ca_bytes(ctx, b"not a cert")
    builder = vnet.new_tls_config_builder()
    with pytest.raises(FileNotFoundError):
        builder.add_root_ca_file("/path/that/does/not/exist.pem")
    with pytest.raises(ssl.SSLError):
        builder.add_root_ca_bytes(b"not a cert")

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
