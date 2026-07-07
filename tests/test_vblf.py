from pathlib import Path

import pytest

from kniferpy import vblf
from kniferpy.internal import blfx
from kniferpy.verr import ValidationError


def test_func_filter_add_and_contains() -> None:
    f = vblf.new_default_filter(1_000_000)
    assert f.add("knifer-go") is True
    # Re-adding a known value returns False (may already exist).
    assert f.add("knifer-go") is False
    assert f.contains("knifer-go") is True
    assert f.contains("definitely-absent-value") is False


def test_func_filter_no_false_negatives() -> None:
    f = vblf.new_default_filter(2_000_000)
    words = [f"user-{i}" for i in range(500)]
    for w in words:
        f.add(w)
    # A Bloom filter never reports a false negative.
    for w in words:
        assert f.contains(w) is True


def test_func_filter_custom_hash() -> None:
    f = vblf.new_func_filter(1024, lambda s: len(s))
    f.add("abcd")
    assert f.contains("abcd") is True
    # Same hash bucket (length) is treated as present -> collision by design.
    assert f.contains("wxyz") is True


def test_func_filter_machine64() -> None:
    f = vblf.new_func_filter(4096, machine_num=vblf.MACHINE_64)
    assert f.add("value") is True
    assert f.contains("value") is True


def test_func_filter_validation() -> None:
    with pytest.raises(ValidationError):
        vblf.new_func_filter(0)
    with pytest.raises(ValidationError):
        vblf.new_func_filter(0x80000000)
    with pytest.raises(ValidationError):
        vblf.new_func_filter(1024, machine_num=16)


def test_algorithm_specific_filters() -> None:
    for factory in (
        vblf.new_elf_filter,
        vblf.new_fnv_filter,
        vblf.new_hf_filter,
        vblf.new_hf_ip_filter,
        vblf.new_js_filter,
        vblf.new_pjw_filter,
        vblf.new_rs_filter,
        vblf.new_sdbm_filter,
        vblf.new_tianl_filter,
    ):
        f = factory(1_000_000)
        f.add("abc")
        assert f.contains("abc") is True


def test_bit_set_bloom_filter() -> None:
    f = vblf.new_bit_set_bloom_filter(200, 100, 4)
    f.add("hello")
    assert f.contains("hello") is True
    assert f.contains("not-added") is False
    prob = f.false_positive_probability()
    assert 0.0 <= prob <= 1.0


def test_bit_set_init_from_lines() -> None:
    f = vblf.new_bit_set_bloom_filter(200, 10, 3)
    f.init_from_lines(["alpha\n", "beta\r\n", "gamma"])
    assert f.contains("alpha") is True
    assert f.contains("beta") is True
    assert f.contains("gamma") is True


def test_bit_set_init_from_file(tmp_path: Path) -> None:
    path = tmp_path / "words.txt"
    path.write_text("one\ntwo\nthree\n", encoding="utf-8")
    f = vblf.new_bit_set_bloom_filter(200, 10, 3)
    f.init_from_file(path)
    assert f.contains("one") is True
    assert f.contains("three") is True


def test_bit_set_validation() -> None:
    with pytest.raises(ValidationError):
        vblf.new_bit_set_bloom_filter(0, 10, 3)
    with pytest.raises(ValidationError):
        vblf.new_bit_set_bloom_filter(200, 0, 3)
    with pytest.raises(ValidationError):
        vblf.new_bit_set_bloom_filter(200, 10, 0)
    with pytest.raises(ValidationError):
        vblf.new_bit_set_bloom_filter(200, 10, 9)


def test_bitmap_bloom_filter_default() -> None:
    f = vblf.new_bitmap_bloom_filter(5)
    assert f.add("knifer-go") is True
    assert f.contains("knifer-go") is True
    assert f.contains("absent") is False


def test_bitmap_bloom_filter_with_filters() -> None:
    f = vblf.new_bitmap_bloom_filter_with_filters(
        1,
        vblf.new_js_filter(1_000_000),
        vblf.new_sdbm_filter(1_000_000),
    )
    f.add("composite")
    assert f.contains("composite") is True


def test_bitmap_bloom_filter_validation() -> None:
    with pytest.raises(ValidationError):
        vblf.new_bitmap_bloom_filter(4)


def test_e_style_constructors() -> None:
    bitset, bitset_err = vblf.new_bit_set_bloom_filter_e(200, 10, 3)
    bitmap, bitmap_err = vblf.new_bitmap_bloom_filter_e(5)
    custom, custom_err = vblf.new_bitmap_bloom_filter_with_filters_e(
        1, vblf.new_js_filter(1_000), vblf.new_sdbm_filter(1_000)
    )
    func, func_err = vblf.new_func_filter_e(1_000)
    machine, machine_err = vblf.new_func_filter_with_machine_num_e(1_000, vblf.MACHINE_64)

    assert bitset_err is None and isinstance(bitset, vblf.BitSetBloomFilter)
    assert bitmap_err is None and isinstance(bitmap, vblf.BitMapBloomFilter)
    assert custom_err is None and custom.add("x")
    assert func_err is None and func.add("x")
    assert machine_err is None and machine.add("x")


def test_new_default_bloom_filter_alias_and_hash_aliases() -> None:
    bloom = vblf.new_default_bloom_filter(1_000)
    bloom.add("alias")

    assert bloom.contains("alias")
    assert vblf.BloomRSHash("x") == vblf.rs_hash("x")
    assert vblf.BloomJSHash("x") == vblf.js_hash("x")
    assert vblf.BloomPJWHash("x") == vblf.pjw_hash("x")
    assert vblf.BloomELFHash("x") == vblf.elf_hash("x")
    assert vblf.BloomBKDRHash("x") == vblf.bkdr_hash("x")
    assert vblf.BloomSDBMHash("x") == vblf.sdbm_hash("x")
    assert vblf.BloomDJBHash("x") == vblf.djb_hash("x")
    assert vblf.BloomFNVHash("x") == vblf.fnv_hash_string("x")


def test_int_map_and_long_map() -> None:
    int_map = vblf.new_int_map(2)
    long_map = vblf.new_long_map(2)

    int_map.add(33)
    long_map.add(65)
    assert int_map.contains(33)
    assert long_map.contains(65)
    int_map.remove(33)
    long_map.remove(65)
    assert not int_map.contains(33)
    assert not long_map.contains(65)
    with pytest.raises(ValidationError):
        vblf.new_int_map(0)
    with pytest.raises(ValidationError):
        vblf.new_long_map(0)


def test_internal_bitmap_and_file_options(tmp_path: Path) -> None:
    bitmap = blfx._BitMap(2, vblf.MACHINE_32)
    bitmap.add(33)
    assert bitmap.contains(33)
    bitmap.remove(33)
    assert not bitmap.contains(33)

    path = tmp_path / "words.txt"
    path.write_text("alpha\nbeta\n", encoding="utf-8")
    opened: list[str] = []

    def open_file(p: str):
        opened.append(p)
        return open(p, encoding="utf-8")  # noqa: SIM115 - opener contract returns a handle

    bloom = vblf.new_bit_set_bloom_filter(100, 10, 3)
    vblf.init_from_file_with_options(bloom, str(path), [blfx.with_open_file(open_file)])
    assert opened == [str(path)]
    assert bloom.contains("alpha")
    assert bloom.contains("beta")

    cfg = blfx._apply_file_options([None])
    assert cfg.open_file is None
