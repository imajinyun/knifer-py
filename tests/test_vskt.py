# mypy: disable-error-code="no-untyped-def"

import socket
import time

import pytest

from kniferpy.vskt import (
    DEFAULT_BUFFER_SIZE,
    AppProtocol,
    FuncDecoder,
    FuncEncoder,
    IoAction,
    MsgDecoder,
    MsgEncoder,
    OpAccept,
    OpConnect,
    OpRead,
    OpWrite,
    SimpleIoAction,
    SocketRuntimeError,
    channel_dial,
    channel_dial_with_options,
    get_remote_address,
    is_connected,
    new_aio_client,
    new_aio_client_with_config,
    new_aio_client_with_conn,
    new_aio_client_with_options,
    new_aio_server,
    new_aio_server_addr,
    new_aio_server_addr_with_options,
    new_aio_server_with_options,
    new_aio_session,
    new_nio_client,
    new_nio_client_addr,
    new_nio_client_addr_with_options,
    new_nio_server,
    new_nio_server_addr,
    new_nio_server_addr_with_config,
    new_nio_server_addr_with_options,
    new_nio_server_with_config,
    new_nio_server_with_options,
    new_socket_config,
    new_socket_config_with_options,
    new_socket_error,
    new_socket_error_msg,
    new_socket_errorf,
    socket_connect,
    socket_connect_with_options,
    with_clock,
    with_connect_dialer,
    with_connect_network,
    with_connect_timeout,
    with_read_buffer_size,
    with_read_timeout,
    with_runner,
    with_thread_pool_size,
    with_thread_pool_size_func,
    with_write_buffer_size,
    with_write_timeout,
    wrap_socket_error,
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
    cfg = new_socket_config_with_options(
        [
            with_thread_pool_size(16),
            with_read_buffer_size(8192),
        ]
    )
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
            "127.0.0.1",
            19999,
            [with_connect_timeout(0.5), with_connect_network("tcp")],
        )


def test_socket_connect_with_custom_dialer():
    called = []

    def dialer(host: str, port: int) -> socket.socket:
        called.append((host, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock

    sock = socket_connect_with_options(
        "127.0.0.1",
        12345,
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

    def fn(h, p):
        return None

    with_connect_dialer(fn)(cfg)
    assert cfg.dialer is fn


class FakeSocket:
    def __init__(self, incoming: bytes = b"") -> None:
        self.incoming = incoming
        self.sent: list[bytes] = []
        self.closed = False

    def recv_into(self, buffer: bytearray) -> int:
        n = min(len(buffer), len(self.incoming))
        buffer[:n] = self.incoming[:n]
        return n

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True

    def getpeername(self):
        return ("127.0.0.1", 12345)


class RecordingAction(SimpleIoAction):
    def __init__(self) -> None:
        self.reads: list[bytes] = []

    def on_read(self, session, buf: bytes) -> None:
        self.reads.append(buf)


def test_more_socket_config_options() -> None:
    def runner(*args, **kwargs) -> None:
        return None

    cfg = new_socket_config_with_options(
        [
            with_thread_pool_size_func(lambda: 3),
            with_runner(runner),
            with_read_timeout(1),
            with_write_timeout(2),
            None,  # type: ignore[list-item]
        ]
    )

    assert cfg.thread_pool_size_func() == 3  # type: ignore[misc]
    assert cfg.runner is runner
    assert cfg.read_timeout_ms == 1
    assert cfg.write_timeout_ms == 2


def test_nio_server_constructor_variants() -> None:
    cfg = new_socket_config()
    assert new_nio_server_with_config(0, cfg)._config is cfg
    assert new_nio_server_addr(("127.0.0.1", 0))._port == 0
    server = new_nio_server_addr_with_options(("127.0.0.1", 0), [with_thread_pool_size(2)])
    assert server._config.thread_pool_size == 2
    assert new_nio_server_addr_with_config(("127.0.0.1", 0), cfg)._config is cfg


def test_nio_client_connect_and_close_with_fake_dialer() -> None:
    fake = FakeSocket()
    client = new_nio_client_addr_with_options(
        ("127.0.0.1", 12345),
        [with_connect_dialer(lambda host, port: fake)],  # type: ignore[list-item]
    )
    # NioClient.connect uses socket_connect, so exercise close branch directly.
    client._conn = fake  # type: ignore[assignment]
    client.close()
    assert fake.closed


def test_aio_session_read_write_and_zero_read() -> None:
    action = RecordingAction()
    sock = FakeSocket(b"hello")
    session = new_aio_session(
        sock,  # type: ignore[arg-type]
        action,
        new_socket_config_with_options([with_read_buffer_size(10)]),
    )

    session.read()
    session.write(b"out")
    session.close()

    assert action.reads == [b"hello"]
    assert sock.sent == [b"out"]
    assert sock.closed

    empty_action = RecordingAction()
    empty = new_aio_session(FakeSocket(b""), empty_action, new_socket_config())  # type: ignore[arg-type]
    empty.read()
    assert empty_action.reads == []


def test_aio_server_client_constructor_variants() -> None:
    cfg = new_socket_config_with_options([with_thread_pool_size_func(lambda: 2)])
    server = new_aio_server_with_options(0, [with_thread_pool_size(2)])
    server_addr = new_aio_server_addr_with_options(
        ("127.0.0.1", 0), cfg, [with_thread_pool_size(4)]
    )
    action = SimpleIoAction()
    fake = FakeSocket()

    assert server._config.thread_pool_size == 2
    assert server_addr._config.thread_pool_size == 4
    client = new_aio_client_with_options(("127.0.0.1", 1), action, [with_connect_timeout(1.0)])
    assert client._addr == (
        "127.0.0.1",
        1,
    )
    assert new_aio_client_with_config(("127.0.0.1", 1), action, cfg)._config is cfg
    client = new_aio_client_with_conn(fake, action, cfg)  # type: ignore[arg-type]
    assert client._conn is fake  # type: ignore[comparison-overlap]
    assert client._session is not None
    client.close()
    assert fake.closed


def test_aio_server_thread_pool_size_func() -> None:
    cfg = new_socket_config_with_options([with_thread_pool_size_func(lambda: 5)])
    server = new_aio_server_addr(("127.0.0.1", 0), cfg)
    assert server._get_thread_pool_size() == 5


def test_protocol_encoder_decoder_defaults_and_funcs() -> None:
    session = new_aio_session(FakeSocket(), SimpleIoAction(), new_socket_config())  # type: ignore[arg-type]
    msg_decoder = MsgDecoder()
    msg_encoder = MsgEncoder()
    io_action = IoAction()
    protocol = AppProtocol()
    decoded_calls: list[bytes] = []
    encoded_calls: list[bytes] = []

    assert msg_decoder.decode(session, b"data") == (None, False)
    msg_encoder.encode(session, bytearray(), object())
    io_action.on_read(session, b"data")
    assert isinstance(protocol, AppProtocol)

    def decode(sess, buf: bytes):
        decoded_calls.append(buf)
        return None, True

    decoder = FuncDecoder(decode)
    encoder = FuncEncoder(lambda sess, buf, msg: encoded_calls.append(bytes(buf) + msg))

    assert decoder.decode(session, b"in") == (None, True)
    encoder.encode(session, bytearray(b"out"), b"!")
    assert decoded_calls == [b"in"]
    assert encoded_calls == [b"out!"]


def test_channel_dial_with_options_and_remote_address() -> None:
    fake = FakeSocket()
    sock = channel_dial_with_options(("127.0.0.1", 1), [with_connect_dialer(lambda h, p: fake)])
    assert sock is fake  # type: ignore[comparison-overlap]
    assert get_remote_address(fake) == ("127.0.0.1", 12345)  # type: ignore[arg-type]
