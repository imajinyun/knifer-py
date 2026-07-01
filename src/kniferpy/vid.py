from __future__ import annotations

from kniferpy.internal import idx
from kniferpy.internal.idx import (
    DEFAULT_NANO_ID_LENGTH,
    NANO_ID_ALPHABET,
    Snowflake,
)

__all__ = [
    "DEFAULT_NANO_ID_LENGTH",
    "NANO_ID_ALPHABET",
    "Snowflake",
    "random_uuid",
    "simple_uuid",
    "nano_id",
    "object_id",
    "create_snowflake",
    "get_snowflake",
    "snowflake_next_id",
    "snowflake_next_id_str",
]


def random_uuid() -> str:
    return idx.random_uuid()


def simple_uuid() -> str:
    return idx.simple_uuid()


def nano_id(length: int = DEFAULT_NANO_ID_LENGTH, alphabet: str = NANO_ID_ALPHABET) -> str:
    return idx.nano_id(length, alphabet)


def object_id() -> str:
    return idx.object_id()


def create_snowflake(worker_id: int = 0, datacenter_id: int = 0) -> Snowflake:
    return Snowflake(worker_id, datacenter_id)


def get_snowflake() -> Snowflake:
    return idx.get_snowflake()


def snowflake_next_id() -> int:
    return idx.snowflake_next_id()


def snowflake_next_id_str() -> str:
    return idx.snowflake_next_id_str()
