import re

import pytest

from kniferpy import vid
from kniferpy.verr import ValidationError

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def test_uuid_shapes() -> None:
    value = vid.random_uuid()
    assert _UUID_RE.match(value)
    simple = vid.simple_uuid()
    assert len(simple) == 32
    assert "-" not in simple
    assert vid.random_uuid() != vid.random_uuid()


def test_nano_id() -> None:
    default = vid.nano_id()
    assert len(default) == vid.DEFAULT_NANO_ID_LENGTH
    assert all(ch in vid.NANO_ID_ALPHABET for ch in default)
    assert len(vid.nano_id(10)) == 10
    assert len(set(vid.nano_id(16) for _ in range(50))) > 1
    with pytest.raises(ValidationError):
        vid.nano_id(0)


def test_object_id() -> None:
    value = vid.object_id()
    assert len(value) == 24
    assert re.fullmatch(r"[0-9a-f]{24}", value)
    assert vid.object_id() != vid.object_id()


def test_snowflake() -> None:
    generator = vid.create_snowflake(worker_id=1, datacenter_id=2)
    first = generator.next_id()
    second = generator.next_id()
    assert isinstance(first, int)
    assert second > first
    ids = {generator.next_id() for _ in range(1000)}
    assert len(ids) == 1000
    assert generator.next_id_str().isdigit()


def test_snowflake_validation() -> None:
    with pytest.raises(ValidationError):
        vid.create_snowflake(worker_id=99)
    with pytest.raises(ValidationError):
        vid.create_snowflake(datacenter_id=99)


def test_default_snowflake() -> None:
    assert vid.get_snowflake() is vid.get_snowflake()
    assert vid.snowflake_next_id() < vid.snowflake_next_id()
    assert vid.snowflake_next_id_str().isdigit()
