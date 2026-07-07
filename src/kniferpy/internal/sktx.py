"""Socket utilities with NIO/AIO patterns.

Ports knifer-go's internal/socket with Python-idiomatic mappings.

Errors use kniferpy.verr types with codes knifer.socket.<reason>.
"""

from __future__ import annotations

import concurrent.futures
import socket
from dataclasses import dataclass
from typing import Any, Callable

from kniferpy.verr import KniferError

# --- constants ----------------------------------------------------------------

DEFAULT_BUFFER_SIZE = 4096

# --- operations ---------------------------------------------------------------

OpRead = "read"
OpWrite = "write"
OpConnect = "connect"
OpAccept = "accept"

# --- errors -------------------------------------------------------------------


class SocketRuntimeError(KniferError):
    pass


def new_socket_error(err: Exception) -> SocketRuntimeError:
    return SocketRuntimeError(str(err))


def new_socket_error_msg(msg: str) -> SocketRuntimeError:
    return SocketRuntimeError(msg)


def new_socket_errorf(fmt: str, *args: Any) -> SocketRuntimeError:
    return SocketRuntimeError(fmt % args)


def wrap_socket_error(err: Exception, msg: str) -> SocketRuntimeError:
    return SocketRuntimeError(f"{msg}: {err}")


# --- config -------------------------------------------------------------------

ConfigOption = Callable[["SocketConfig"], None]


@dataclass
class SocketConfig:
    thread_pool_size: int = 32
    thread_pool_size_func: Callable[[], int] | None = None
    read_timeout_ms: int = 30000
    write_timeout_ms: int = 30000
    read_buffer_size: int = DEFAULT_BUFFER_SIZE
    write_buffer_size: int = DEFAULT_BUFFER_SIZE
    clock: Callable[[], float] | None = None
    runner: Callable[..., None] | None = None
    listener_factory: Callable[..., Any] | None = None
    conn_factory: Callable[..., Any] | None = None
    ip_parser: Callable[..., Any] | None = None


def new_socket_config() -> SocketConfig:
    return SocketConfig()


def with_thread_pool_size(n: int) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.thread_pool_size = n

    return apply


def with_thread_pool_size_func(f: Callable[[], int]) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.thread_pool_size_func = f

    return apply


def with_read_timeout(ms: int) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.read_timeout_ms = ms

    return apply


def with_write_timeout(ms: int) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.write_timeout_ms = ms

    return apply


def with_read_buffer_size(n: int) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.read_buffer_size = n

    return apply


def with_write_buffer_size(n: int) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.write_buffer_size = n

    return apply


def with_clock(clock: Callable[[], float]) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.clock = clock

    return apply


def with_runner(runner: Callable[..., None]) -> ConfigOption:
    def apply(cfg: SocketConfig) -> None:
        cfg.runner = runner

    return apply


def new_socket_config_with_options(opts: list[ConfigOption]) -> SocketConfig:
    cfg = new_socket_config()
    for opt in opts:
        if opt is not None:
            opt(cfg)
    return cfg


# --- connect options ----------------------------------------------------------

ConnectOption = Callable[["_ConnectConfig"], None]


@dataclass
class _ConnectConfig:
    timeout: float = 5.0
    network: str = "tcp"
    dialer: Callable[..., Any] | None = None


def with_connect_timeout(timeout: float) -> ConnectOption:
    def apply(cfg: _ConnectConfig) -> None:
        cfg.timeout = timeout

    return apply


def with_connect_network(network: str) -> ConnectOption:
    def apply(cfg: _ConnectConfig) -> None:
        cfg.network = network

    return apply


def with_connect_dialer(dialer: Callable[..., Any]) -> ConnectOption:
    def apply(cfg: _ConnectConfig) -> None:
        cfg.dialer = dialer

    return apply


# --- connect helpers ----------------------------------------------------------


def socket_connect(hostname: str, port: int, timeout: float) -> socket.socket:
    return socket_connect_with_options(hostname, port, [with_connect_timeout(timeout)])


def socket_connect_with_options(
    hostname: str, port: int, opts: list[ConnectOption]
) -> socket.socket:
    cfg = _ConnectConfig()
    for opt in opts:
        if opt is not None:
            opt(cfg)

    if cfg.dialer is not None:
        return cfg.dialer(hostname, port)  # type: ignore[no-any-return]

    addr = (hostname, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(cfg.timeout)
    sock.connect(addr)
    return sock


def socket_connect_addr(addr: tuple[str, int], timeout: float) -> socket.socket:
    return socket_connect_addr_with_options(addr, [with_connect_timeout(timeout)])


def socket_connect_addr_with_options(
    addr: tuple[str, int], opts: list[ConnectOption]
) -> socket.socket:
    return socket_connect_with_options(addr[0], addr[1], opts)


def get_remote_address(conn: socket.socket | None) -> Any:
    if conn is None:
        return None
    return conn.getpeername()


def is_connected(conn: socket.socket | None) -> bool:
    return conn is not None


def channel_dial(addr: tuple[str, int], timeout: float) -> socket.socket:
    return socket_connect_addr(addr, timeout)


def channel_dial_with_options(addr: tuple[str, int], opts: list[ConnectOption]) -> socket.socket:
    return socket_connect_addr_with_options(addr, opts)


# --- nio server --------------------------------------------------------------


class NioServer:
    def __init__(self, port: int, config: SocketConfig | None = None):
        self._port = port
        self._config = config or new_socket_config()
        self._server_socket: socket.socket | None = None
        self._pool: concurrent.futures.ThreadPoolExecutor | None = None

    def start(self) -> None:
        self._pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._config.thread_pool_size
        )
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("0.0.0.0", self._port))
        self._server_socket.listen(10)

    def stop(self) -> None:
        if self._server_socket is not None:
            self._server_socket.close()
            self._server_socket = None
        if self._pool is not None:
            self._pool.shutdown(wait=True)
            self._pool = None


def new_nio_server(port: int) -> NioServer:
    return NioServer(port)


def new_nio_server_with_options(port: int, opts: list[ConfigOption]) -> NioServer:
    cfg = new_socket_config_with_options(opts)
    return NioServer(port, cfg)


def new_nio_server_with_config(port: int, cfg: SocketConfig) -> NioServer:
    return NioServer(port, cfg)


def new_nio_server_addr(addr: tuple[str, int]) -> NioServer:
    return NioServer(addr[1])


def new_nio_server_addr_with_options(addr: tuple[str, int], opts: list[ConfigOption]) -> NioServer:
    cfg = new_socket_config_with_options(opts)
    return NioServer(addr[1], cfg)


def new_nio_server_addr_with_config(addr: tuple[str, int], cfg: SocketConfig) -> NioServer:
    return NioServer(addr[1], cfg)


# --- nio client --------------------------------------------------------------


class NioClient:
    def __init__(self, host: str, port: int, config: SocketConfig | None = None):
        self._host = host
        self._port = port
        self._config = config or new_socket_config()
        self._conn: socket.socket | None = None

    def connect(self, timeout: float = 5.0) -> None:
        self._conn = socket_connect(self._host, self._port, timeout)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def new_nio_client(host: str, port: int) -> NioClient:
    return NioClient(host, port)


def new_nio_client_with_options(host: str, port: int, opts: list[ConfigOption]) -> NioClient:
    cfg = new_socket_config_with_options(opts)
    return NioClient(host, port, cfg)


def new_nio_client_addr(addr: tuple[str, int]) -> NioClient:
    return NioClient(addr[0], addr[1])


def new_nio_client_addr_with_options(addr: tuple[str, int], opts: list[ConfigOption]) -> NioClient:
    cfg = new_socket_config_with_options(opts)
    return NioClient(addr[0], addr[1], cfg)


# --- aio -----------------------------------------------------------------------


class AioSession:
    def __init__(self, conn: socket.socket, action: Any, config: SocketConfig):
        self._conn = conn
        self._action = action
        self._config = config
        self._read_buffer = bytearray(config.read_buffer_size)

    def read(self) -> None:
        n = self._conn.recv_into(self._read_buffer)
        if n > 0:
            self._action.on_read(self, bytes(self._read_buffer[:n]))

    def write(self, data: bytes) -> None:
        self._conn.sendall(data)

    def close(self) -> None:
        self._conn.close()


def new_aio_session(conn: socket.socket, action: Any, config: SocketConfig) -> AioSession:
    return AioSession(conn, action, config)


class SimpleIoAction:
    def on_read(self, session: AioSession, buf: bytes) -> None:
        pass


class AioServer:
    def __init__(self, port: int, config: SocketConfig | None = None):
        self._port = port
        self._config = config or new_socket_config()
        self._server_socket: socket.socket | None = None
        self._pool: concurrent.futures.ThreadPoolExecutor | None = None

    def _get_thread_pool_size(self) -> int:
        if self._config.thread_pool_size_func is not None:
            return self._config.thread_pool_size_func()
        return self._config.thread_pool_size

    def start(self) -> None:
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=self._get_thread_pool_size())
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("0.0.0.0", self._port))
        self._server_socket.listen(10)

    def stop(self) -> None:
        if self._server_socket is not None:
            self._server_socket.close()
            self._server_socket = None
        if self._pool is not None:
            self._pool.shutdown(wait=True)
            self._pool = None


def new_aio_server(port: int) -> AioServer:
    return AioServer(port)


def new_aio_server_with_options(port: int, opts: list[ConfigOption]) -> AioServer:
    cfg = new_socket_config_with_options(opts)
    return AioServer(port, cfg)


def new_aio_server_addr(addr: tuple[str, int], cfg: SocketConfig) -> AioServer:
    return AioServer(addr[1], cfg)


def new_aio_server_addr_with_options(
    addr: tuple[str, int], cfg: SocketConfig, opts: list[ConfigOption]
) -> AioServer:
    for opt in opts:
        if opt is not None:
            opt(cfg)
    return AioServer(addr[1], cfg)


class AioClient:
    def __init__(self, addr: tuple[str, int], action: Any, config: SocketConfig | None = None):
        self._addr = addr
        self._action = action
        self._config = config or new_socket_config()
        self._conn: socket.socket | None = None
        self._session: AioSession | None = None

    def connect(self, timeout: float = 5.0) -> None:
        self._conn = socket_connect_addr(self._addr, timeout)
        self._session = new_aio_session(self._conn, self._action, self._config)

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
        if self._conn is not None:
            self._conn.close()


def new_aio_client(addr: tuple[str, int], action: Any) -> AioClient:
    return AioClient(addr, action)


def new_aio_client_with_options(
    addr: tuple[str, int], action: Any, opts: list[ConnectOption]
) -> AioClient:
    cfg = new_socket_config()
    return AioClient(addr, action, cfg)


def new_aio_client_with_config(addr: tuple[str, int], action: Any, cfg: SocketConfig) -> AioClient:
    return AioClient(addr, action, cfg)


def new_aio_client_with_conn(conn: socket.socket, action: Any, cfg: SocketConfig) -> AioClient:
    client = AioClient((conn.getpeername()[0], conn.getpeername()[1]), action, cfg)
    client._conn = conn
    client._session = new_aio_session(conn, action, cfg)
    return client


# --- protocol -----------------------------------------------------------------


class IoAction:
    def on_read(self, session: AioSession, buf: Any) -> None:
        pass


class MsgDecoder:
    def decode(self, session: AioSession, buf: bytes) -> tuple[Any | None, bool]:
        return (None, False)


class MsgEncoder:
    def encode(self, session: AioSession, buf: bytearray, msg: Any) -> None:
        pass


class AppProtocol:
    pass


class FuncDecoder:
    def __init__(self, func: Callable[..., Any]):
        self._func = func

    def decode(self, session: AioSession, buf: bytes) -> Any:
        return self._func(session, buf)


class FuncEncoder:
    def __init__(self, func: Callable[..., Any]):
        self._func = func

    def encode(self, session: AioSession, buf: bytearray, msg: Any) -> None:
        self._func(session, buf, msg)
