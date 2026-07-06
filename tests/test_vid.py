import random
import re

import pytest

from kniferpy import vid
from kniferpy.internal import idx
from kniferpy.verr import ValidationError

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


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


def test_uuid_aliases_and_with_options() -> None:
    assert _UUID_RE.match(vid.fast_uuid())
    assert len(vid.fast_simple_uuid()) == 32
    assert len(vid.UUID()) == 32
    assert _UUID_RE.match(vid.random_uuid_with_options())
    assert len(vid.simple_uuid_with_options()) == 32
    assert _UUID_RE.match(vid.fast_uuid_with_options())
    assert len(vid.fast_simple_uuid_with_options()) == 32


def test_nano_id_custom_alphabet_and_aliases() -> None:
    assert vid.nano_id(4, "A") == "AAAA"
    assert len(vid.nano_id_n(5)) == 5
    assert len(vid.nano_id_with_options(6)) == 6
    assert len(vid.nano_id_n_with_options(7)) == 7
    with pytest.raises(ValidationError) as exc_info:
        vid.nano_id(1, "")
    assert exc_info.value.code == "knifer.id.alphabet"


def test_object_id_counter_and_with_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(idx.time, "time", lambda: 1_700_000_000)
    monkeypatch.setattr(idx.secrets, "token_bytes", lambda n: b"\x01" * n)
    monkeypatch.setattr(idx, "_object_id_counter", 0xFFFFFE)

    first = vid.object_id()
    second = vid.object_id_with_options()

    assert first.startswith((1_700_000_000 & 0xFFFFFFFF).to_bytes(4, "big").hex())
    assert first.endswith("ffffff")
    assert second.endswith("000000")


def test_snowflake_accessors_default_ids_and_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(idx.os, "getpid", lambda: 0x1234)
    assert idx._default_ids() == (0x1234 & 31, (0x1234 >> 8) & 31)
    assert vid.get_worker_id(0) == (0x1234 & 31)
    assert vid.get_datacenter_id() == ((0x1234 >> 8) & 31)

    generator = vid.new_isolated_snowflake(3, 4)
    assert generator.worker_id() == 3
    assert generator.datacenter_id() == 4
    assert vid.create_snowflake_with_options(1, 2).worker_id() == 1
    assert vid.get_snowflake_with_worker(5).worker_id() == 5
    assert vid.get_snowflake_with_worker_with_options(6).worker_id() == 6
    assert vid.get_snowflake_with_worker_datacenter(7, 8).datacenter_id() == 8
    assert vid.get_snowflake_with_worker_datacenter_with_options(9, 10).worker_id() == 9


def test_configure_default_snowflake_and_clock_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    default = vid.configure_default_snowflake(1, 1)
    assert vid.get_snowflake_with_options() is default
    assert vid.snowflake_next_id_with_options() < vid.snowflake_next_id_with_options()
    assert vid.snowflake_next_id_str_with_options().isdigit()

    generator = vid.create_snowflake(1, 1)
    monkeypatch.setattr(generator, "_last_timestamp", 1000)
    monkeypatch.setattr(generator, "_now_ms", lambda: 999)
    with pytest.raises(ValidationError) as exc_info:
        generator.next_id()
    assert exc_info.value.code == "knifer.id.clock"


def test_snowflake_sequence_wrap_waits_next_millis(monkeypatch: pytest.MonkeyPatch) -> None:
    generator = vid.create_snowflake(1, 1)
    monkeypatch.setattr(generator, "_last_timestamp", 1000)
    monkeypatch.setattr(generator, "_sequence", idx._SEQUENCE_MASK)
    monkeypatch.setattr(generator, "_now_ms", lambda: 1000)
    monkeypatch.setattr(generator, "_wait_next_millis", lambda last: 1001)

    value = generator.next_id()

    assert value & idx._SEQUENCE_MASK == 0


def test_fallback_random_provider_seed_and_reset() -> None:
    provider_calls: list[str] = []

    def provider() -> random.Random:
        provider_calls.append("provider")
        return random.Random(123)

    vid.configure_default_fallback_random_source_provider(provider)
    assert idx._fallback_random_provider() is not None
    assert provider_calls == ["provider"]
    vid.set_fallback_random_seed(42)
    assert idx._fallback_random is not None
    vid.reset_default_fallback_random_source()
    assert idx._fallback_random is None
