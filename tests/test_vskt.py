import socket
import time

import pytest

from kniferpy.vskt import (
    DEFAULT_BUFFER_SIZE,
    OpAccept,
    OpConnect,
    OpRead,
    OpWrite,
    SocketConfig,
    SocketRuntimeError,
    new_socket_config,
    new_socket_config_with_options,
    new_socket_error,
    new_socket_error_msg,
    new_socket_errorf,
    socket_connect,
    socket_connect_with_options,
    is_connected,
    get_remote_address,
    with_connect_timeout,
    with_connect_network,
    with_connect_dialer,
    with_thread_pool_size,
    with_read_timeout,
    with_write_timeout,
    with_read_buffer_size,
    with_write_buffer_size,
    with_clock,
    new_nio_server,
    new_nio_client,
    new_aio_server,
    new_aio_client,
    new_aio_session,
    SimpleIoAction,
    wrap_socket_error,
    channel_dial,
    new_nio_server_with_options,
    new_nio_client_addr,
    new_nio_client_addr_with_options,
    new_aio_server_addr,
)


# --- constants ------------------------------------------------------------


def test_constants():
    assert OpRead == "read"
    assert OpWrite == "write"
    assert OpConnect == "connect"
    assert OpAccept == "accept"
    assert DEFAULT_BUFFER_SIZE == 4096


# --- SocketConfig ---------------------------------------------------------


def test_new_socket_config_defaults():
    cfg = new_socket_config()
    assert cfg.thread_pool_size == 32
    assert cfg.read_timeout_ms == 30000
    assert cfg.write_timeout_ms == 30000
    assert cfg.read_buffer_size == 4096
    assert cfg.write_buffer_size == 4096


def test_new_socket_config_with_options():
    cfg = new_socket_config_with_options([
        with_thread_pool_size(16),
        with_read_buffer_size(8192),
    ])
    assert cfg.thread_pool_size == 16
    assert cfg.read_buffer_size == 8192


def test_socket_config_options():
    cfg = new_socket_config()
    with_thread_pool_size(8)(cfg)
    with_read_timeout(5000)(cfg)
    with_write_timeout(5000)(cfg)
    with_read_buffer_size(1024)(cfg)
    with_write_buffer_size(2048)(cfg)
    with_clock(lambda: time.time())(cfg)
    assert cfg.thread_pool_size == 8
    assert cfg.read_timeout_ms == 5000
    assert cfg.write_timeout_ms == 5000
    assert cfg.read_buffer_size == 1024
    assert cfg.write_buffer_size == 2048
    assert cfg.clock is not None


# --- SocketRuntimeError ---------------------------------------------------


def test_new_socket_error():
    err = new_socket_error(ValueError("bad"))
    assert isinstance(err, SocketRuntimeError)
    assert "bad" in str(err)


def test_new_socket_error_msg():
    err = new_socket_error_msg("something went wrong")
    assert "something went wrong" in str(err)


def test_new_socket_errorf():
    err = new_socket_errorf("port %d already in use", 8080)
    assert "port 8080 already in use" in str(err)


def test_wrap_socket_error():
    err = wrap_socket_error(ValueError("bad"), "connect failed")
    assert "connect failed" in str(err)
    assert "bad" in str(err)


# --- socket_connect (integration) -----------------------------------------


def test_socket_connect_failure():
    with pytest.raises(OSError):
        socket_connect("127.0.0.1", 19999, 0.5)


def test_socket_connect_with_options():
    with pytest.raises(OSError):
        socket_connect_with_options(
            "127.0.0.1", 19999,
            [with_connect_timeout(0.5), with_connect_network("tcp")],
        )


def test_socket_connect_with_custom_dialer():
    called = []

    def dialer(host: str, port: int) -> socket.socket:
        called.append((host, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock

    sock = socket_connect_with_options(
        "127.0.0.1", 12345,
        [with_connect_dialer(dialer)],
    )
    assert called == [("127.0.0.1", 12345)]
    sock.close()


# --- is_connected / get_remote_address ------------------------------------


def test_is_connected():
    assert is_connected(None) is False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert is_connected(sock) is True
    sock.close()


def test_get_remote_address():
    assert get_remote_address(None) is None


# --- channel_dial ---------------------------------------------------------


def test_channel_dial_failure():
    with pytest.raises(OSError):
        channel_dial(("127.0.0.1", 19999), 0.5)


# --- NIO server -----------------------------------------------------------


def test_new_nio_server():
    srv = new_nio_server(0)
    assert srv is not None
    srv.stop()


def test_new_nio_server_with_options():
    srv = new_nio_server_with_options(0, [with_thread_pool_size(4)])
    assert srv is not None
    srv.stop()


def test_nio_server_bind_free_port():
    srv = new_nio_server(0)
    srv.start()
    assert srv._server_socket is not None
    srv.stop()


# --- NIO client -----------------------------------------------------------


def test_new_nio_client():
    cli = new_nio_client("127.0.0.1", 19999)
    assert cli is not None
    cli.close()


def test_new_nio_client_addr():
    cli = new_nio_client_addr(("127.0.0.1", 19999))
    assert cli is not None
    cli.close()


def test_new_nio_client_addr_with_options():
    cli = new_nio_client_addr_with_options(
        ("127.0.0.1", 19999),
        [with_thread_pool_size(4)],
    )
    assert cli is not None
    cli.close()


# --- AIO server -----------------------------------------------------------


def test_new_aio_server():
    srv = new_aio_server(0)
    assert srv is not None
    srv.stop()


def test_new_aio_server_addr():
    srv = new_aio_server_addr(("127.0.0.1", 0), new_socket_config())
    assert srv is not None
    srv.stop()


# --- AIO client -----------------------------------------------------------


def test_new_aio_client():
    cli = new_aio_client(("127.0.0.1", 19999), SimpleIoAction())
    assert cli is not None
    cli.close()


def test_new_aio_client_connect_failure():
    cli = new_aio_client(("127.0.0.1", 19999), SimpleIoAction())
    with pytest.raises(OSError):
        cli.connect(0.5)
    cli.close()


# --- AIO session ----------------------------------------------------------


def test_new_aio_session():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    session = new_aio_session(sock, SimpleIoAction(), new_socket_config())
    assert session is not None
    session.close()


# --- NIO server start/stop cycle ------------------------------------------


def test_nio_server_start_stop():
    srv = new_nio_server(0)
    srv.start()
    srv.stop()
    # Should be able to stop twice
    srv.stop()


def test_aio_server_start_stop():
    srv = new_aio_server(0)
    srv.start()
    srv.stop()
    srv.stop()


# --- connect options are applied correctly --------------------------------


def test_connect_timeout_option():
    cfg = type("_cfg", (), {"timeout": 0.0})()
    with_connect_timeout(2.5)(cfg)
    assert cfg.timeout == 2.5


def test_connect_network_option():
    cfg = type("_cfg", (), {"network": ""})()
    with_connect_network("tcp4")(cfg)
    assert cfg.network == "tcp4"


def test_connect_dialer_option():
    cfg = type("_cfg", (), {"dialer": None})()
    fn = lambda h, p: None
    with_connect_dialer(fn)(cfg)
    assert cfg.dialer is fn