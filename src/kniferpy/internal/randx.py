from __future__ import annotations

import os
import random
import sys
import threading
from typing import Any, Callable, Sequence, TypeVar

T = TypeVar('T')

BaseNumber = "0123456789"
BaseChar = "abcdefghijklmnopqrstuvwxyz"
BaseCharNumber = BaseChar + BaseNumber
BaseCharNumberUC = BaseChar + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + BaseNumber


class RandomOption:
    pass


class _RandomOptions:
    """Per-call random configuration."""

    def __init__(self) -> None:
        self.source: random.Random | None = None
        self.reader: Callable[[int], bytes] | None = None
        self.strict_crypto: bool = False


def _apply_options(opts: Sequence[Callable[[_RandomOptions], None]]) -> _RandomOptions:
    cfg = _RandomOptions()
    cfg.reader = os.urandom
    for opt in opts:
        if opt:
            opt(cfg)
    if cfg.reader is None:
        cfg.reader = os.urandom
    return cfg


def with_random_source(source: random.Random) -> Callable[[_RandomOptions], None]:
    """Set the pseudo-random source for numeric, string, and element helpers."""
    def _opt(cfg: _RandomOptions) -> None:
        cfg.source = source
    return _opt


def with_random_reader(reader: Callable[[int], bytes]) -> Callable[[_RandomOptions], None]:
    """Set the byte source for RandomBytesWithOptions and SecureRandomBytesWithOptions."""
    def _opt(cfg: _RandomOptions) -> None:
        cfg.reader = reader
    return _opt


def with_strict_crypto_random() -> Callable[[_RandomOptions], None]:
    """Make RandomBytesWithOptions return reader errors instead of falling back."""
    def _opt(cfg: _RandomOptions) -> None:
        cfg.strict_crypto = True
    return _opt


_default_rand_lock = threading.Lock()
_default_rand: random.Random | None = None
def _default_rand_provider() -> random.Random:
    return random.Random()


def set_seed(seed: int) -> None:
    """Reset the package-level pseudo-random source seed."""
    global _default_rand
    with _default_rand_lock:
        _default_rand = random.Random(seed)


def configure_default_random_source_provider(provider: Callable[[], random.Random] | None) -> None:
    """Set the provider used to lazily create the package-level pseudo-random source."""
    global _default_rand, _default_rand_provider
    with _default_rand_lock:
        _default_rand = None
        _default_rand_provider = (lambda: random.Random()) if provider is None else provider


def reset_default_random_source() -> None:
    """Restore the time-seeded default source provider."""
    configure_default_random_source_provider(None)


def _default_rand_locked() -> random.Random:
    global _default_rand
    if _default_rand is None:
        _default_rand = _default_rand_provider()
        if _default_rand is None:
            _default_rand = random.Random()
    return _default_rand


def _random_intn(cfg: _RandomOptions, n: int) -> int:
    if cfg.source is not None:
        return cfg.source.randrange(n)
    with _default_rand_lock:
        return _default_rand_locked().randrange(n)


def random_int(max_val: int) -> int:
    """Return a random integer in [0, max). Non-positive max returns 0."""
    return random_int_with_options(max_val)


def random_int_with_options(max_val: int, *opts: Callable[[_RandomOptions], None]) -> int:
    """Return a random integer in [0, max) with per-call options."""
    if max_val <= 0:
        return 0
    cfg = _apply_options(opts)
    return _random_intn(cfg, max_val)


def random_int_range(min_val: int, max_val: int) -> int:
    """Return a random integer in [min, max). If max <= min, return min."""
    return random_int_range_with_options(min_val, max_val)


def random_int_range_with_options(min_val: int, max_val: int, *opts: Callable[[_RandomOptions], None]) -> int:
    """Return a random integer in [min, max) with per-call options."""
    if max_val <= min_val:
        return min_val
    cfg = _apply_options(opts)
    return min_val + _random_intn(cfg, max_val - min_val)


def random_long() -> int:
    """Return a non-negative random int64."""
    return random_long_with_options()


def random_long_with_options(*opts: Callable[[_RandomOptions], None]) -> int:
    """Return a non-negative random int64 with per-call options."""
    cfg = _apply_options(opts)
    if cfg.source is not None:
        return cfg.source.getrandbits(63)
    with _default_rand_lock:
        return _default_rand_locked().getrandbits(63)


def random_float() -> float:
    """Return a random float64 in [0.0, 1.0)."""
    return random_float_with_options()


def random_float_with_options(*opts: Callable[[_RandomOptions], None]) -> float:
    """Return a random float64 in [0.0, 1.0) with per-call options."""
    cfg = _apply_options(opts)
    if cfg.source is not None:
        return cfg.source.random()
    with _default_rand_lock:
        return _default_rand_locked().random()


def random_bool() -> bool:
    """Return a random boolean."""
    return random_bool_with_options()


def random_bool_with_options(*opts: Callable[[_RandomOptions], None]) -> bool:
    """Return a random boolean with per-call options."""
    cfg = _apply_options(opts)
    return _random_intn(cfg, 2) == 0


def random_bytes(n: int) -> bytes:
    """Return n random bytes. Use SecureRandomBytes for secrets."""
    return random_bytes_with_options(n)


def random_bytes_with_options(n: int, *opts: Callable[[_RandomOptions], None]) -> bytes:
    """Return n random bytes with per-call options."""
    if n <= 0:
        return b""
    cfg = _apply_options(opts)
    return _fill_random_bytes(n, cfg)


def secure_random_bytes(n: int) -> bytes:
    """Return n cryptographically secure random bytes."""
    return secure_random_bytes_with_options(n)


def secure_random_bytes_with_options(n: int, *opts: Callable[[_RandomOptions], None]) -> bytes:
    """Return n cryptographically secure random bytes with per-call options."""
    strict_opts = list(opts)
    strict_opts.append(with_strict_crypto_random())
    return random_bytes_with_options(n, *strict_opts)


def _fill_random_bytes(n: int, cfg: _RandomOptions) -> bytes:
    try:
        if cfg.reader:
            return cfg.reader(n)
    except Exception:
        if cfg.strict_crypto:
            raise
    # Compatibility fallback: pseudo-random
    buf = bytearray(n)
    for i in range(n):
        buf[i] = _random_intn(cfg, 256)
    return bytes(buf)


def random_string(n: int) -> str:
    """Return a random lowercase alphanumeric string of length n."""
    return random_string_with_options(n)


def random_string_with_options(n: int, *opts: Callable[[_RandomOptions], None]) -> str:
    """Return a random lowercase alphanumeric string with per-call options."""
    return random_string_from_with_options(BaseCharNumber, n, *opts)


def random_numbers(n: int) -> str:
    """Return a random numeric string of length n."""
    return random_numbers_with_options(n)


def random_numbers_with_options(n: int, *opts: Callable[[_RandomOptions], None]) -> str:
    """Return a random numeric string with per-call options."""
    return random_string_from_with_options(BaseNumber, n, *opts)


def random_string_upper(n: int) -> str:
    """Return a random mixed-case alphanumeric string of length n."""
    return random_string_upper_with_options(n)


def random_string_upper_with_options(n: int, *opts: Callable[[_RandomOptions], None]) -> str:
    """Return a random mixed-case alphanumeric string with per-call options."""
    return random_string_from_with_options(BaseCharNumberUC, n, *opts)


def random_string_from(charset: str, n: int) -> str:
    """Build a random string by sampling runes from charset."""
    return random_string_from_with_options(charset, n)


def random_string_from_with_options(charset: str, n: int, *opts: Callable[[_RandomOptions], None]) -> str:
    """Build a random string by sampling runes from charset with per-call options."""
    if n <= 0 or not charset:
        return ""
    cfg = _apply_options(opts)
    chars = list(charset)
    out = [_random_intn(cfg, len(chars)) for _ in range(n)]
    return "".join(chars[i] for i in out)


def random_ele(a: list[T]) -> T:
    """Return a random element from a, or a zero value when a is empty."""
    return random_ele_with_options(a)


def random_ele_with_options(a: list[T], *opts: Callable[[_RandomOptions], None]) -> T:
    """Return a random element with per-call options, or a zero value when a is empty."""
    if not a:
        if sys.version_info >= (3, 11):
            return list.__new__(list)  # type: ignore[return-value]
        return a[0:0]  # type: ignore[return-value]
    cfg = _apply_options(opts)
    return a[_random_intn(cfg, len(a))]


class WeightedOption:
    pass


class _WeightedConfig:
    def __init__(self) -> None:
        self.source: random.Random | None = None
        self.precision: float = 1e-12


def _apply_weighted_options(opts: Sequence[Callable[[_WeightedConfig], None]]) -> _WeightedConfig:
    cfg = _WeightedConfig()
    for opt in opts:
        if opt:
            opt(cfg)
    return cfg


def with_weighted_rand_source(source: random.Random) -> Callable[[_WeightedConfig], None]:
    """Set the pseudo-random source for weighted helpers."""
    def _opt(cfg: _WeightedConfig) -> None:
        cfg.source = source
    return _opt


def with_weighted_precision(precision: float) -> Callable[[_WeightedConfig], None]:
    """Set the minimum positive total-weight tolerance."""
    def _opt(cfg: _WeightedConfig) -> None:
        if precision > 0:
            cfg.precision = precision
    return _opt


def _weighted_float64(cfg: _WeightedConfig) -> float:
    if cfg.source is not None:
        return cfg.source.random()
    with _default_rand_lock:
        return _default_rand_locked().random()


def _weighted_intn(cfg: _WeightedConfig, n: int) -> int:
    if cfg.source is not None:
        return cfg.source.randrange(n)
    with _default_rand_lock:
        return _default_rand_locked().randrange(n)


class _AliasPicker:
    def __init__(self, items: list[Any], weights: list[float], cfg: _WeightedConfig):
        self._items = list(items)
        self._prob: list[float] = []
        self._alias: list[int] = []
        self._cfg = cfg
        self._build(weights)

    def _build(self, weights: list[float]) -> None:
        n = len(self._items)
        total = 0.0
        for w in weights:
            if w != w or w == float('inf') or w == float('-inf') or w < 0:
                raise ValueError("weighted pick weights must be finite and non-negative")
            total += w
        if total <= self._cfg.precision:
            raise ValueError("weighted pick total weight must be positive")
        scaled = [w * n / total for w in weights]
        small: list[int] = []
        large: list[int] = []
        for i, s in enumerate(scaled):
            if s < 1:
                small.append(i)
            else:
                large.append(i)

        self._prob = [0.0] * n
        self._alias = [0] * n
        while small and large:
            s = small.pop()
            large_item = large.pop()
            self._prob[s] = scaled[s]
            self._alias[s] = large_item
            scaled[large_item] = scaled[large_item] + scaled[s] - 1
            if scaled[large_item] < 1:
                small.append(large_item)
            else:
                large.append(large_item)
        for i in small + large:
            self._prob[i] = 1.0
            self._alias[i] = i

    def pick(self) -> Any:
        return self._items[self._pick_index()]

    def _pick_index(self) -> int:
        idx = _weighted_intn(self._cfg, len(self._items))
        if _weighted_float64(self._cfg) < self._prob[idx]:
            return idx
        return self._alias[idx]


def weighted_pick(items: list[T], weights: list[float], *opts: Callable[[_WeightedConfig], None]) -> T:
    """Pick one item according to weights using the alias method."""
    if len(items) == 0:
        raise ValueError("weighted pick items are empty")
    if len(items) != len(weights):
        raise ValueError("weighted pick items and weights length mismatch")
    picker = _AliasPicker(items, weights, _apply_weighted_options(opts))
    return picker.pick()


def weighted_pick_n(items: list[T], weights: list[float], n: int, *opts: Callable[[_WeightedConfig], None]) -> list[T]:
    """Pick n items with replacement according to weights."""
    if n < 0:
        raise ValueError("weighted pick count must be non-negative")
    if len(items) == 0:
        raise ValueError("weighted pick items are empty")
    if len(items) != len(weights):
        raise ValueError("weighted pick items and weights length mismatch")
    picker = _AliasPicker(items, weights, _apply_weighted_options(opts))
    return [picker.pick() for _ in range(n)]


def weighted_pick_unique_n(items: list[T], weights: list[float], n: int, *opts: Callable[[_WeightedConfig], None]) -> list[T]:
    """Pick n unique items without replacement according to weights."""
    if n < 0:
        raise ValueError("weighted pick count must be non-negative")
    if n > len(items):
        raise ValueError("weighted unique pick count exceeds item count")
    if len(items) == 0:
        raise ValueError("weighted pick items are empty")
    if len(items) != len(weights):
        raise ValueError("weighted pick items and weights length mismatch")
    cfg = _apply_weighted_options(opts)
    remaining_items = list(items)
    remaining_weights = list(weights)
    out: list[T] = []
    for _ in range(n):
        picker = _AliasPicker(remaining_items, remaining_weights, cfg)
        idx = picker._pick_index()
        out.append(remaining_items[idx])
        del remaining_items[idx]
        del remaining_weights[idx]
    return out