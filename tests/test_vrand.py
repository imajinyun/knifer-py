from __future__ import annotations

import random
import sys

import pytest

from kniferpy import vrand
from kniferpy.internal import randx


class TestRandomInt:
    def test_non_positive_max_returns_zero(self) -> None:
        assert vrand.random_int(0) == 0
        assert vrand.random_int(-1) == 0

    def test_positive_max_returns_in_range(self) -> None:
        for _ in range(50):
            val = vrand.random_int(10)
            assert 0 <= val < 10

    def test_with_options(self) -> None:
        rng = random.Random(42)
        val = vrand.random_int_with_options(100, vrand.with_random_source(rng))
        assert 0 <= val < 100


class TestRandomIntRange:
    def test_max_le_min_returns_min(self) -> None:
        assert vrand.random_int_range(5, 5) == 5
        assert vrand.random_int_range(5, 3) == 5

    def test_returns_in_range(self) -> None:
        for _ in range(50):
            val = vrand.random_int_range(10, 20)
            assert 10 <= val < 20


class TestRandomLong:
    def test_non_negative(self) -> None:
        val = vrand.random_long()
        assert val >= 0
        assert isinstance(val, int)
        assert isinstance(vrand.random_long_with_options(), int)

    def test_reproducible_with_seed(self) -> None:
        vrand.set_seed(42)
        a = vrand.random_long()
        vrand.set_seed(42)
        b = vrand.random_long()
        assert a == b
        vrand.reset_default_random_source()


class TestRandomFloat:
    def test_in_range(self) -> None:
        for _ in range(50):
            val = vrand.random_float()
            assert 0.0 <= val < 1.0

    def test_with_options(self) -> None:
        rng = random.Random(42)
        val = vrand.random_float_with_options(vrand.with_random_source(rng))
        assert 0.0 <= val < 1.0


class TestRandomBool:
    def test_returns_bool(self) -> None:
        val = vrand.random_bool()
        assert isinstance(val, bool)

    def test_with_options(self) -> None:
        rng = random.Random(42)
        val = vrand.random_bool_with_options(vrand.with_random_source(rng))
        assert isinstance(val, bool)


class TestRandomBytes:
    def test_length(self) -> None:
        assert len(vrand.random_bytes(16)) == 16

    def test_non_positive_returns_empty(self) -> None:
        assert vrand.random_bytes(0) == b""
        assert vrand.random_bytes(-1) == b""

    def test_secure_random_bytes(self) -> None:
        assert len(vrand.secure_random_bytes(32)) == 32

    def test_secure_non_positive_returns_empty(self) -> None:
        assert vrand.secure_random_bytes(0) == b""

    def test_reader_option_and_fallback(self) -> None:
        assert vrand.random_bytes_with_options(
            4, vrand.with_random_reader(lambda n: b"x" * n)
        ) == b"xxxx"

        def failing_reader(_n: int) -> bytes:
            raise RuntimeError("reader failed")

        data = vrand.random_bytes_with_options(
            4,
            vrand.with_random_reader(failing_reader),
            vrand.with_random_source(random.Random(1)),
        )
        assert len(data) == 4

        with pytest.raises(RuntimeError, match="reader failed"):
            vrand.secure_random_bytes_with_options(4, vrand.with_random_reader(failing_reader))


class TestRandomString:
    def test_length(self) -> None:
        assert len(vrand.random_string(10)) == 10

    def test_non_positive_returns_empty(self) -> None:
        assert vrand.random_string(0) == ""

    def test_reproducible_with_seed(self) -> None:
        vrand.set_seed(42)
        a = vrand.random_string(20)
        vrand.set_seed(42)
        b = vrand.random_string(20)
        assert a == b
        vrand.reset_default_random_source()


class TestRandomNumbers:
    def test_length(self) -> None:
        assert len(vrand.random_numbers(10)) == 10

    def test_all_digits(self) -> None:
        s = vrand.random_numbers(50)
        assert s.isdigit()


class TestRandomStringUpper:
    def test_length(self) -> None:
        assert len(vrand.random_string_upper(10)) == 10

    def test_alphanumeric(self) -> None:
        s = vrand.random_string_upper(50)
        assert s.isalnum()


class TestRandomStringFrom:
    def test_from_custom_charset(self) -> None:
        s = vrand.random_string_from("ABC", 10)
        assert len(s) == 10
        assert all(c in "ABC" for c in s)

    def test_empty_charset_returns_empty(self) -> None:
        assert vrand.random_string_from("", 10) == ""

    def test_non_positive_n_returns_empty(self) -> None:
        assert vrand.random_string_from("ABC", 0) == ""


class TestRandomEle:
    def test_returns_element(self) -> None:
        items = [1, 2, 3, 4, 5]
        for _ in range(20):
            val = vrand.random_ele(items)
            assert val in items

    def test_empty_list(self) -> None:
        result = vrand.random_ele([])
        assert result == [] or result == []
        assert isinstance(result, list)

    def test_with_options(self) -> None:
        rng = random.Random(42)
        items = [10, 20, 30]
        val = vrand.random_ele_with_options(items, vrand.with_random_source(rng))
        assert val in items


class TestSetSeed:
    def test_reproducible(self) -> None:
        vrand.set_seed(123)
        int1 = vrand.random_int(100)
        vrand.set_seed(123)
        int2 = vrand.random_int(100)
        assert int1 == int2
        vrand.reset_default_random_source()


class TestDefaultRandomSourceProvider:
    def test_configure_and_reset(self) -> None:
        vrand.configure_default_random_source_provider(lambda: random.Random(77))
        vrand.set_seed(99)
        val = vrand.random_int(1000)
        assert isinstance(val, int)
        vrand.reset_default_random_source()
        val2 = vrand.random_int(1000)
        assert isinstance(val2, int)

    def test_none_provider_falls_back_to_random(self) -> None:
        try:
            vrand.configure_default_random_source_provider(lambda: None)  # type: ignore[return-value]
            assert isinstance(vrand.random_int(1000), int)
        finally:
            vrand.reset_default_random_source()

    def test_apply_options_ignores_none_and_restores_reader(self) -> None:
        def clear_reader(cfg: randx._RandomOptions) -> None:
            cfg.reader = None

        cfg = randx._apply_options([None, clear_reader])  # type: ignore[list-item]
        assert cfg.reader is not None


class TestWeightedPick:
    def test_pick_one(self) -> None:
        items = ["a", "b", "c"]
        weights = [1.0, 2.0, 3.0]
        result = vrand.weighted_pick(items, weights)
        assert result in items

    def test_pick_n(self) -> None:
        items = ["a", "b", "c"]
        weights = [1.0, 2.0, 3.0]
        results = vrand.weighted_pick_n(items, weights, 5)
        assert len(results) == 5
        assert all(r in items for r in results)

    def test_pick_n_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            vrand.weighted_pick_n(["a"], [1.0], -1)

    def test_pick_n_empty_and_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            vrand.weighted_pick_n([], [], 1)
        with pytest.raises(ValueError, match="mismatch"):
            vrand.weighted_pick_n(["a"], [1.0, 2.0], 1)

    def test_pick_unique_n(self) -> None:
        items = ["a", "b", "c", "d"]
        weights = [1.0, 2.0, 3.0, 4.0]
        results = vrand.weighted_pick_unique_n(items, weights, 3)
        assert len(results) == 3
        assert len(set(results)) == 3
        assert all(r in items for r in results)

    def test_pick_unique_n_exceeds_count_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds"):
            vrand.weighted_pick_unique_n(["a"], [1.0], 2)

    def test_pick_unique_n_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            vrand.weighted_pick_unique_n(["a"], [1.0], -1)

    def test_pick_unique_empty_and_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            vrand.weighted_pick_unique_n([], [], 0)
        with pytest.raises(ValueError, match="mismatch"):
            vrand.weighted_pick_unique_n(["a"], [1.0, 2.0], 1)

    def test_with_weighted_source(self) -> None:
        rng = random.Random(42)
        items = ["a", "b", "c"]
        weights = [1.0, 2.0, 3.0]
        result = vrand.weighted_pick(items, weights, vrand.with_weighted_rand_source(rng))
        assert result in items

    def test_reproducible_weighted(self) -> None:
        rng = random.Random(42)
        items = ["a", "b", "c", "d", "e"]
        weights = [1.0, 2.0, 3.0, 4.0, 5.0]
        a = vrand.weighted_pick_n(items, weights, 10, vrand.with_weighted_rand_source(rng))
        rng = random.Random(42)
        b = vrand.weighted_pick_n(items, weights, 10, vrand.with_weighted_rand_source(rng))
        assert a == b

    def test_zero_total_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            vrand.weighted_pick(["a", "b"], [0.0, 0.0])
        with pytest.raises(ValueError, match="positive"):
            vrand.weighted_pick(
                ["a"],
                [1e-13],
                vrand.with_weighted_precision(-1),
            )
        assert vrand.weighted_pick(
            ["a"],
            [1e-13],
            vrand.with_weighted_precision(1e-15),
        ) == "a"

    def test_negative_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            vrand.weighted_pick(["a", "b"], [1.0, -1.0])
        with pytest.raises(ValueError, match="finite"):
            vrand.weighted_pick(["a"], [float("nan")])
        with pytest.raises(ValueError, match="finite"):
            vrand.weighted_pick(["a"], [float("inf")])

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError, match="mismatch"):
            vrand.weighted_pick(["a", "b"], [1.0])

    def test_empty_items_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            vrand.weighted_pick([], [])


class TestCharacterSets:
    def test_base_number(self) -> None:
        assert "0" in vrand.BaseNumber
        assert "9" in vrand.BaseNumber
        assert len(vrand.BaseNumber) == 10

    def test_base_char(self) -> None:
        assert "a" in vrand.BaseChar
        assert "z" in vrand.BaseChar
        assert len(vrand.BaseChar) == 26

    def test_base_char_number(self) -> None:
        assert len(vrand.BaseCharNumber) == 36

    def test_base_char_number_uc(self) -> None:
        assert len(vrand.BaseCharNumberUC) == 62
        assert "A" in vrand.BaseCharNumberUC
        assert "Z" in vrand.BaseCharNumberUC
