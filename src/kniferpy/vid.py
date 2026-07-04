from __future__ import annotations

from kniferpy.internal import idx
from kniferpy.internal.idx import (
    DEFAULT_NANO_ID_LENGTH,
    NANO_ID_ALPHABET,
    Snowflake,
    configure_default_fallback_random_source_provider,
    reset_default_fallback_random_source,
    set_fallback_random_seed,
)

__all__ = [
    "DEFAULT_NANO_ID_LENGTH",
    "NANO_ID_ALPHABET",
    "Snowflake",
    "UUID",
    "random_uuid",
    "fast_uuid",
    "simple_uuid",
    "fast_simple_uuid",
    "nano_id",
    "nano_id_n",
    "object_id",
    "create_snowflake",
    "new_isolated_snowflake",
    "get_snowflake",
    "configure_default_snowflake",
    "get_snowflake_with_worker",
    "get_snowflake_with_worker_datacenter",
    "get_datacenter_id",
    "get_worker_id",
    "snowflake_next_id",
    "snowflake_next_id_str",
    "configure_default_fallback_random_source_provider",
    "reset_default_fallback_random_source",
    "set_fallback_random_seed",
]

DEFAULT_NANO_ID_LENGTH = idx.DEFAULT_NANO_ID_LENGTH
NANO_ID_ALPHABET = idx.NANO_ID_ALPHABET

UUID = idx.UUID


def random_uuid() -> str:
    return idx.random_uuid()


def fast_uuid() -> str:
    return idx.fast_uuid()


def simple_uuid() -> str:
    return idx.simple_uuid()


def fast_simple_uuid() -> str:
    return idx.fast_simple_uuid()


def nano_id(length: int = DEFAULT_NANO_ID_LENGTH, alphabet: str = NANO_ID_ALPHABET) -> str:
    return idx.nano_id(length, alphabet)


def nano_id_n(n: int) -> str:
    return idx.nano_id_n(n)


def object_id() -> str:
    return idx.object_id()


def create_snowflake(worker_id: int = 0, datacenter_id: int = 0) -> Snowflake:
    return idx.create_snowflake(worker_id, datacenter_id)


def new_isolated_snowflake(worker_id: int = 0, datacenter_id: int = 0) -> Snowflake:
    return idx.new_isolated_snowflake(worker_id, datacenter_id)


def get_snowflake() -> Snowflake:
    return idx.get_snowflake()


def configure_default_snowflake(worker_id: int = 0, datacenter_id: int = 0) -> Snowflake:
    return idx.configure_default_snowflake(worker_id, datacenter_id)


def get_snowflake_with_worker(worker_id: int) -> Snowflake:
    return idx.get_snowflake_with_worker(worker_id)


def get_snowflake_with_worker_datacenter(worker_id: int, datacenter_id: int) -> Snowflake:
    return idx.get_snowflake_with_worker_datacenter(worker_id, datacenter_id)


def get_datacenter_id(max_datacenter_id: int = 31) -> int:
    return idx.get_datacenter_id(max_datacenter_id)


def get_worker_id(datacenter_id: int, max_worker_id: int = 31) -> int:
    return idx.get_worker_id(datacenter_id, max_worker_id)


def snowflake_next_id() -> int:
    return idx.snowflake_next_id()


def snowflake_next_id_str() -> str:
    return idx.snowflake_next_id_str()


def configure_default_fallback_random_source_provider(provider):
    return idx.configure_default_fallback_random_source_provider(provider)


def reset_default_fallback_random_source():
    return idx.reset_default_fallback_random_source()


def set_fallback_random_seed(seed: int) -> None:
    return idx.set_fallback_random_seed(seed)