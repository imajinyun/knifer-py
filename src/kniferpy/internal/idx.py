from __future__ import annotations

import os
import secrets
import threading
import time
import uuid
from typing import Callable

from kniferpy.verr import ValidationError

# Matches knifer-go internal/id nanoIDAlphabet (URL-safe, 64 characters).
NANO_ID_ALPHABET = "_-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DEFAULT_NANO_ID_LENGTH = 21

# Snowflake bit layout aligned with knifer-go internal/id.
_WORKER_ID_BITS = 5
_DATACENTER_ID_BITS = 5
_SEQUENCE_BITS = 12
_MAX_WORKER_ID = -1 ^ (-1 << _WORKER_ID_BITS)
_MAX_DATACENTER_ID = -1 ^ (-1 << _DATACENTER_ID_BITS)
_SEQUENCE_MASK = -1 ^ (-1 << _SEQUENCE_BITS)
_WORKER_ID_SHIFT = _SEQUENCE_BITS
_DATACENTER_SHIFT = _SEQUENCE_BITS + _WORKER_ID_BITS
_TIMESTAMP_SHIFT = _SEQUENCE_BITS + _WORKER_ID_BITS + _DATACENTER_ID_BITS
_EPOCH = 1288834974657

_object_id_counter = secrets.randbelow(0xFFFFFF)
_object_id_lock = threading.Lock()


def random_uuid() -> str:
    return str(uuid.uuid4())


def fast_uuid() -> str:
    return str(uuid.uuid4())


def simple_uuid() -> str:
    return uuid.uuid4().hex


def fast_simple_uuid() -> str:
    return uuid.uuid4().hex


# Legacy alias
UUID = simple_uuid


def nano_id(length: int = DEFAULT_NANO_ID_LENGTH, alphabet: str = NANO_ID_ALPHABET) -> str:
    if length <= 0:
        raise ValidationError(message="nano_id length must be positive", code="knifer.id.length")
    if not alphabet:
        raise ValidationError(
            message="nano_id alphabet must not be empty", code="knifer.id.alphabet"
        )
    return "".join(secrets.choice(alphabet) for _ in range(length))


def nano_id_n(n: int) -> str:
    return nano_id(length=n)


def _next_object_id_counter() -> int:
    global _object_id_counter
    with _object_id_lock:
        _object_id_counter = (_object_id_counter + 1) & 0xFFFFFF
        return _object_id_counter


def object_id() -> str:
    timestamp = int(time.time()) & 0xFFFFFFFF
    random_part = secrets.token_bytes(5)
    counter = _next_object_id_counter()
    raw = timestamp.to_bytes(4, "big") + random_part + counter.to_bytes(3, "big")
    return raw.hex()


class Snowflake:
    """A Twitter-style Snowflake generator matching the knifer-go bit layout."""

    def __init__(self, worker_id: int = 0, datacenter_id: int = 0) -> None:
        if not 0 <= worker_id <= _MAX_WORKER_ID:
            raise ValidationError(
                message=f"worker_id must be in [0, {_MAX_WORKER_ID}]",
                code="knifer.id.worker",
                context={"worker_id": worker_id},
            )
        if not 0 <= datacenter_id <= _MAX_DATACENTER_ID:
            raise ValidationError(
                message=f"datacenter_id must be in [0, {_MAX_DATACENTER_ID}]",
                code="knifer.id.datacenter",
                context={"datacenter_id": datacenter_id},
            )
        self._worker_id = worker_id
        self._datacenter_id = datacenter_id
        self._sequence = 0
        self._last_timestamp = -1
        self._lock = threading.Lock()

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last: int) -> int:
        now = self._now_ms()
        while now <= last:
            now = self._now_ms()
        return now

    def next_id(self) -> int:
        with self._lock:
            now = self._now_ms()
            if now < self._last_timestamp:
                raise ValidationError(
                    message="clock moved backwards; refusing to generate id",
                    code="knifer.id.clock",
                    context={"now": now, "last": self._last_timestamp},
                )
            if now == self._last_timestamp:
                self._sequence = (self._sequence + 1) & _SEQUENCE_MASK
                if self._sequence == 0:
                    now = self._wait_next_millis(self._last_timestamp)
            else:
                self._sequence = 0
            self._last_timestamp = now
            return (
                ((now - _EPOCH) << _TIMESTAMP_SHIFT)
                | (self._datacenter_id << _DATACENTER_SHIFT)
                | (self._worker_id << _WORKER_ID_SHIFT)
                | self._sequence
            )

    def next_id_str(self) -> str:
        return str(self.next_id())


_default_snowflake_lock = threading.Lock()
_default_snowflake: Snowflake | None = None


def _default_ids() -> tuple[int, int]:
    worker = os.getpid() & _MAX_WORKER_ID
    datacenter = (os.getpid() >> 8) & _MAX_DATACENTER_ID
    return worker, datacenter


def get_snowflake() -> Snowflake:
    global _default_snowflake
    with _default_snowflake_lock:
        if _default_snowflake is None:
            worker, datacenter = _default_ids()
            _default_snowflake = Snowflake(worker, datacenter)
        return _default_snowflake


def configure_default_snowflake(worker_id: int = 0, datacenter_id: int = 0) -> Snowflake:
    global _default_snowflake
    with _default_snowflake_lock:
        _default_snowflake = Snowflake(worker_id, datacenter_id)
        return _default_snowflake


def snowflake_next_id() -> int:
    return get_snowflake().next_id()


def snowflake_next_id_str() -> str:
    return get_snowflake().next_id_str()


def create_snowflake(worker_id: int = 0, datacenter_id: int = 0) -> Snowflake:
    return Snowflake(worker_id, datacenter_id)


def new_isolated_snowflake(worker_id: int = 0, datacenter_id: int = 0) -> Snowflake:
    return Snowflake(worker_id, datacenter_id)


def get_snowflake_with_worker(worker_id: int) -> Snowflake:
    return Snowflake(worker_id, 0)


def get_snowflake_with_worker_datacenter(worker_id: int, datacenter_id: int) -> Snowflake:
    return Snowflake(worker_id, datacenter_id)


def get_datacenter_id(max_datacenter_id: int = _MAX_DATACENTER_ID) -> int:
    return (os.getpid() >> 8) & max_datacenter_id


def get_worker_id(datacenter_id: int, max_worker_id: int = _MAX_WORKER_ID) -> int:
    return os.getpid() & max_worker_id


# --- Fallback random source --------------------------------------------------

import random as _random
import threading as _threading

_fallback_random_lock = _threading.Lock()
_fallback_random: _random.Random | None = None
_fallback_random_provider: Callable[[], _random.Random] = lambda: _random.Random()


def configure_default_fallback_random_source_provider(provider: Callable[[], _random.Random] | None) -> None:
    global _fallback_random, _fallback_random_provider
    with _fallback_random_lock:
        _fallback_random = None
        if provider is None:
            _fallback_random_provider = lambda: _random.Random()
            return
        _fallback_random_provider = provider


def reset_default_fallback_random_source() -> None:
    configure_default_fallback_random_source_provider(None)


def set_fallback_random_seed(seed: int) -> None:
    global _fallback_random
    with _fallback_random_lock:
        _fallback_random = _random.Random(seed)
