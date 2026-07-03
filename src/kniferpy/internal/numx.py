from __future__ import annotations

import math
import os
import struct
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from decimal import (
    Decimal,
    InvalidOperation,
)
from enum import IntEnum
from fractions import Fraction
from typing import Any, TypeVar

from kniferpy.verr import ValidationError

# ---------------------------------------------------------------------------
# rounding mode
# ---------------------------------------------------------------------------


class RoundingMode(IntEnum):
    HALF_UP = 0
    HALF_EVEN = 1
    DOWN = 2


# ---------------------------------------------------------------------------
# option configs
# ---------------------------------------------------------------------------

T = TypeVar("T", int, float)
_Number = int | float


@dataclass
class _RandomNumberConfig:
    random_reader: Callable[[int], int] = field(default_factory=lambda: (lambda n: int.from_bytes(os.urandom(8), "big") % n))


@dataclass
class _ParseConfig:
    parse_int: Callable[[str], int] = field(default_factory=lambda: int)
    parse_float: Callable[[str], float] = field(default_factory=lambda: float)


@dataclass
class _FormatConfig:
    format_float: Callable[..., str] = field(default_factory=lambda: str)
    format_int: Callable[..., str] = field(default_factory=lambda: str)


@dataclass
class _DoubleConfig:
    parse_float: Callable[[str], float] = field(default_factory=lambda: float)
    format_float: Callable[..., str] = field(default_factory=lambda: str)


RandomNumberOption = Callable[[_RandomNumberConfig], None]
ParseOption = Callable[[_ParseConfig], None]
FormatOption = Callable[[_FormatConfig], None]
DoubleOption = Callable[[_DoubleConfig], None]


def _with_random_reader(reader: Callable[[int], int]) -> RandomNumberOption:
    def apply(cfg: _RandomNumberConfig) -> None:
        cfg.random_reader = reader

    return apply


def _with_parse_int(parser: Callable[[str], int]) -> ParseOption:
    def apply(cfg: _ParseConfig) -> None:
        cfg.parse_int = parser

    return apply


def _with_parse_float(parser: Callable[[str], float]) -> ParseOption:
    def apply(cfg: _ParseConfig) -> None:
        cfg.parse_float = parser

    return apply


def _with_format_float(formatter: Callable[..., str]) -> FormatOption:
    def apply(cfg: _FormatConfig) -> None:
        cfg.format_float = formatter

    return apply


def _with_format_int(formatter: Callable[..., str]) -> FormatOption:
    def apply(cfg: _FormatConfig) -> None:
        cfg.format_int = formatter

    return apply


def _with_double_parse_float(parser: Callable[[str], float]) -> DoubleOption:
    def apply(cfg: _DoubleConfig) -> None:
        cfg.parse_float = parser

    return apply


def _with_double_format_float(formatter: Callable[..., str]) -> DoubleOption:
    def apply(cfg: _DoubleConfig) -> None:
        cfg.format_float = formatter

    return apply


def _apply_random_number_options(opts: Sequence[RandomNumberOption]) -> _RandomNumberConfig:
    cfg = _RandomNumberConfig()
    for opt in opts:
        opt(cfg)
    return cfg


def _apply_parse_options(opts: Sequence[ParseOption]) -> _ParseConfig:
    cfg = _ParseConfig()
    for opt in opts:
        opt(cfg)
    return cfg


def _apply_format_options(opts: Sequence[FormatOption]) -> _FormatConfig:
    cfg = _FormatConfig()
    for opt in opts:
        opt(cfg)
    return cfg


def _apply_double_options(opts: Sequence[DoubleOption]) -> _DoubleConfig:
    cfg = _DoubleConfig()
    for opt in opts:
        opt(cfg)
    return cfg


# ---------------------------------------------------------------------------
# factorial table
# ---------------------------------------------------------------------------

_FACTORIALS: tuple[int, ...] = (
    1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800,
    39916800, 479001600, 6227020800, 87178291200, 1307674368000,
    20922789888000, 355687428096000, 6402373705728000,
    121645100408832000, 2432902008176640000,
)

_DEFAULT_DIV_SCALE = 10


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _abs_int(v: int) -> int:
    return -v if v < 0 else v


def _strip_trailing_zeros(s: str) -> str:
    if "." in s and "e" not in s.lower():
        s = s.rstrip("0").rstrip(".")
    return s


def _add_thousands(s: str) -> str:
    parts = s.split(".", 1)
    int_part = parts[0]
    sign = ""
    if int_part.startswith("-"):
        sign, int_part = "-", int_part[1:]
    result = ""
    for i, ch in enumerate(reversed(int_part)):
        if i > 0 and i % 3 == 0:
            result = "," + result
        result = ch + result
    if len(parts) == 2:
        return sign + result + "." + parts[1]
    return sign + result


def _secure_intn(max_val: int, reader: Callable[[int], int] | None = None) -> int:
    if max_val <= 0:
        return 0
    if reader is None:
        def reader(n):
            return int.from_bytes(os.urandom(8), "big") % n
    return reader(max_val)


# ---------------------------------------------------------------------------
# arithmetic
# ---------------------------------------------------------------------------


def _add(values: Sequence[float]) -> float:
    result = Decimal(0)
    for v in values:
        result += Decimal(str(v))
    return float(result)


def _add_str(values: Sequence[str]) -> Fraction:
    r = Fraction(0, 1)
    for v in values:
        stripped = v.strip()
        if stripped:
            r += Fraction(stripped)
    return r


def _sub(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    result = Decimal(str(values[0]))
    for v in values[1:]:
        result -= Decimal(str(v))
    return float(result)


def _sub_str(values: Sequence[str]) -> Fraction:
    if not values:
        return Fraction(0, 1)
    r = Fraction(values[0].strip() or "0")
    for v in values[1:]:
        stripped = v.strip()
        if stripped:
            r -= Fraction(stripped)
    return r


def _mul(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    result = Decimal(1)
    for v in values:
        result *= Decimal(str(v))
    return float(result)


def _mul_str(values: Sequence[str]) -> Fraction:
    if not values:
        return Fraction(0, 1)
    r = Fraction(1, 1)
    for v in values:
        stripped = v.strip()
        if not stripped:
            return Fraction(0, 1)
        r *= Fraction(stripped)
    return r


def _div(a: float, b: float, scale: int = _DEFAULT_DIV_SCALE) -> float:
    return _number_div(a, b, scale)


def _number_div(a: float, b: float, scale: int = _DEFAULT_DIV_SCALE) -> float:
    if b == 0:
        return 0.0
    if scale < 0:
        return a / b
    return _round(a / b, scale)


def _div_with_mode(a: float, b: float, scale: int, mode: RoundingMode) -> float:
    if b == 0:
        return 0.0
    return _round_mode(a / b, scale, mode)


def _ceil_div(v1: int, v2: int) -> int:
    return -(-v1 // v2)


def _pow(number: float, n: int) -> float:
    return _pow_with_mode(number, n, 2, RoundingMode.HALF_UP)


def _pow_with_mode(number: float, n: int, scale: int, mode: RoundingMode) -> float:
    if n < 0:
        return _round_mode(1.0 / math.pow(number, -n), scale, mode)
    return math.pow(number, n)


# ---------------------------------------------------------------------------
# rounding
# ---------------------------------------------------------------------------


def _round(value: float, scale: int = 0) -> float:
    return _round_mode(value, scale, RoundingMode.HALF_UP)


def _round_mode(value: float, scale: int, mode: RoundingMode) -> float:
    if scale < 0:
        scale = 0
    pow10 = float(10**scale)
    scaled = value * pow10
    if mode == RoundingMode.DOWN:
        rounded = math.trunc(scaled)
    elif mode == RoundingMode.HALF_EVEN:
        rounded = round(scaled)
    else:
        rounded = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    return rounded / pow10


def _round_str(value: float, scale: int, opts: Sequence[FormatOption] | None = None) -> str:
    if opts is None:
        opts = []
    cfg = _apply_format_options(opts)
    return cfg.format_float(_round(value, scale))


def _round_half_even_float(value: float, scale: int) -> float:
    return _round_mode(value, scale, RoundingMode.HALF_EVEN)


def _round_down_float(value: float, scale: int) -> float:
    return _round_mode(value, scale, RoundingMode.DOWN)


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------


def _decimal_format(format_str: str, value: float, opts: Sequence[FormatOption] | None = None) -> str:
    if opts is None:
        opts = []
    _apply_format_options(opts)
    if not format_str:
        return f"{_round(value, 0):.0f}"
    percent = "%" in format_str
    if percent:
        value *= 100
    decimals = 0
    if "." in format_str:
        for ch in format_str.split(".", 1)[1]:
            if ch in "0#":
                decimals += 1
    out = f"{_round(value, decimals):.{decimals}f}"
    if "," in format_str:
        out = _add_thousands(out)
    if percent:
        out += "%"
    return out


def _decimal_format_money(value: float, opts: Sequence[FormatOption] | None = None) -> str:
    return _decimal_format(",##0.00", value, opts)


def _format_percent(number: float, scale: int, opts: Sequence[FormatOption] | None = None) -> str:
    return _decimal_format("0." + "0" * max(scale, 0) + "%", number, opts)


def _to_str(number: float, opts: Sequence[FormatOption] | None = None) -> str:
    return _to_str_strip(number, True, opts)


def _to_str_default(number: float | None, default_value: str, opts: Sequence[FormatOption] | None = None) -> str:
    if number is None:
        return default_value
    return _to_str(number, opts)


def _to_str_strip(number: float, strip: bool, opts: Sequence[FormatOption] | None = None) -> str:
    if not _is_valid(number):
        return ""
    if opts is None:
        opts = []
    cfg = _apply_format_options(opts)
    s = cfg.format_float(number)
    if strip:
        s = _strip_trailing_zeros(s)
    return s


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def _is_number(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    s = s.strip()
    if not s:
        return False
    if s.startswith("+") or s.startswith("-"):
        s = s[1:]
    lowered = s.lower()
    if lowered.startswith("0x"):
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    if s and s[-1] in "dDfFlL":
        s = s[:-1]
    try:
        cfg.parse_float(s)
        return True
    except (ValueError, InvalidOperation):
        return False


def _is_integer(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    if not s.strip():
        return False
    try:
        cfg.parse_int(s.strip())
        return True
    except (ValueError, InvalidOperation):
        return False


def _is_long(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    return _is_integer(s, opts)


def _is_double(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    s = s.strip()
    if not s or "." not in s:
        return False
    try:
        cfg.parse_float(s)
        return True
    except (ValueError, InvalidOperation):
        return False


def _is_digits(s: str) -> bool:
    return bool(s) and all("0" <= ch <= "9" for ch in s)


def _is_primes(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _is_valid_number(number: Any) -> bool:
    if number is None:
        return False
    if isinstance(number, float):
        return _is_valid(number)
    if isinstance(number, int):
        return True
    return True


def _is_valid(number: float) -> bool:
    return not math.isnan(number) and not math.isinf(number)


def _is_valid_float32(number: float) -> bool:
    return not math.isnan(float(number)) and not math.isinf(float(number))


def _is_odd(num: int) -> bool:
    return num % 2 != 0


def _is_even(num: int) -> bool:
    return num % 2 == 0


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------


def _parse_int(number: str, opts: Sequence[ParseOption] | None = None) -> int:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    s = number.strip()
    if not s or s.startswith("."):
        return 0
    lowered = s.lower()
    if lowered.startswith("0x"):
        return int(s[2:], 16)
    if any(ch in s for ch in "eE"):
        return 0
    try:
        return cfg.parse_int(s)
    except (ValueError, InvalidOperation):
        pass
    try:
        return int(cfg.parse_float(s.replace(",", "")))
    except (ValueError, InvalidOperation):
        return 0


def _parse_int_impl(s: str) -> int:
    return int(s, 10)


def _parse_float_impl(s: str) -> float:
    return float(s)


def _parse_int_with_opts(number: str, opts: Sequence[ParseOption] | None = None) -> int:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    s = number.strip()
    if not s or s.startswith("."):
        return 0
    lowered = s.lower()
    if lowered.startswith("0x"):
        return int(s[2:], 16)
    if any(ch in s for ch in "eE"):
        return 0
    try:
        return cfg.parse_int(s)
    except (ValueError, InvalidOperation):
        pass
    try:
        return int(cfg.parse_float(s.replace(",", "")))
    except (ValueError, InvalidOperation):
        return 0


def _parse_long(number: str, opts: Sequence[ParseOption] | None = None) -> int:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    s = number.strip()
    if not s or s.startswith("."):
        return 0
    lowered = s.lower()
    if lowered.startswith("0x"):
        return int(s[2:], 16)
    if any(ch in s for ch in "eE"):
        return 0
    try:
        return cfg.parse_int(s)
    except (ValueError, InvalidOperation):
        pass
    try:
        return int(cfg.parse_float(s.replace(",", "")))
    except (ValueError, InvalidOperation):
        return 0


def _parse_float(number: str, opts: Sequence[ParseOption] | None = None) -> float:
    return float(_parse_double(number, opts))


def _parse_double(number: str, opts: Sequence[ParseOption] | None = None) -> float:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    s = number.strip().replace(",", "")
    if not s:
        return 0.0
    try:
        return cfg.parse_float(s)
    except (ValueError, InvalidOperation):
        return 0.0


def _parse_number(number_str: str, opts: Sequence[ParseOption] | None = None) -> float | None:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    s = number_str.strip().replace(",", "")
    s = s.removeprefix("+")
    lowered = s.lower()
    if lowered.startswith("0x"):
        try:
            return float(int(s[2:], 16))
        except (ValueError, InvalidOperation):
            return None
    try:
        return cfg.parse_float(s)
    except (ValueError, InvalidOperation):
        return None


def _parse_int_default(number_str: str, default_value: int, opts: Sequence[ParseOption] | None = None) -> int:
    if opts is None:
        opts = []
    if not number_str.strip():
        return default_value
    if not _is_number(number_str, opts) and "," not in number_str:
        return default_value
    return _parse_int_with_opts(number_str, opts)


def _parse_long_default(number_str: str, default_value: int, opts: Sequence[ParseOption] | None = None) -> int:
    if opts is None:
        opts = []
    if not number_str.strip():
        return default_value
    if not _is_number(number_str, opts) and "," not in number_str:
        return default_value
    return _parse_long(number_str, opts)


def _parse_float_default(number_str: str, default_value: float, opts: Sequence[ParseOption] | None = None) -> float:
    if opts is None:
        opts = []
    if not number_str.strip():
        return default_value
    cfg = _apply_parse_options(opts)
    try:
        return cfg.parse_float(number_str.strip().replace(",", ""))
    except (ValueError, InvalidOperation):
        return default_value


def _parse_double_default(number_str: str, default_value: float, opts: Sequence[ParseOption] | None = None) -> float:
    if opts is None:
        opts = []
    if not number_str.strip():
        return default_value
    cfg = _apply_parse_options(opts)
    try:
        return cfg.parse_float(number_str.strip().replace(",", ""))
    except (ValueError, InvalidOperation):
        return default_value


# ---------------------------------------------------------------------------
# random number generation
# ---------------------------------------------------------------------------


def _gen_random_number(begin: int, end: int, size: int, opts: Sequence[RandomNumberOption] | None = None) -> list[int]:
    if begin > end:
        begin, end = end, begin
    return _gen_random_number_with_seed(begin, end, size, _num_range(begin, end, 1), opts)


def _gen_random_number_with_seed(
    begin: int, end: int, size: int, seed: list[int], opts: Sequence[RandomNumberOption] | None = None
) -> list[int]:
    if opts is None:
        opts = []
    if begin > end:
        begin, end = end, begin
    if size < 0 or end - begin < size or len(seed) < size:
        return []
    cfg = _apply_random_number_options(opts)
    pool = seed[:]
    out: list[int] = []
    for i in range(size):
        j = _secure_intn(len(pool) - i, cfg.random_reader)
        out.append(pool[j])
        pool[j] = pool[len(pool) - 1 - i]
    return out


def _gen_by_set(begin: int, end: int, size: int, opts: Sequence[RandomNumberOption] | None = None) -> list[int]:
    if opts is None:
        opts = []
    if begin > end:
        begin, end = end, begin
    if size < 0 or end - begin < size:
        return []
    cfg = _apply_random_number_options(opts)
    seen: set[int] = set()
    while len(seen) < size:
        seen.add(begin + _secure_intn(end - begin, cfg.random_reader))
    return list(seen)


# ---------------------------------------------------------------------------
# range
# ---------------------------------------------------------------------------


def _num_range(start: int, end: int, step: int = 1) -> list[int]:
    if step == 0:
        step = 1 if end >= start else -1
    return list(range(start, end, step))


def _range_closed(start: int, stop: int, step: int = 1) -> list[int]:
    if start == stop:
        return [start]
    if step == 0:
        step = 1
    step = _abs_int(step) if start < stop else -_abs_int(step)
    out = []
    i = start
    while True:
        out.append(i)
        if (step > 0 and i + step > stop) or (step < 0 and i + step < stop):
            break
        i += step
    return out


def _append_range(start: int, stop: int, step: int, values: list[int]) -> list[int]:
    return values + _range_closed(start, stop, step)


# ---------------------------------------------------------------------------
# expression calculator
# ---------------------------------------------------------------------------


class _ExprParser:
    def __init__(self, expr: str, cfg: _ParseConfig) -> None:
        self.s = expr
        self.pos = 0
        self.cfg = cfg

    def _skip_spaces(self) -> None:
        while self.pos < len(self.s) and self.s[self.pos] in " \t\n\r":
            self.pos += 1

    def _match(self, ch: str) -> bool:
        self._skip_spaces()
        if self.pos < len(self.s) and self.s[self.pos] == ch:
            self.pos += 1
            return True
        return False

    def _parse_expression(self) -> float:
        v = self._parse_term()
        while True:
            self._skip_spaces()
            if self._match("+"):
                v += self._parse_term()
            elif self._match("-"):
                v -= self._parse_term()
            else:
                return v

    def _parse_term(self) -> float:
        v = self._parse_factor()
        while True:
            self._skip_spaces()
            if self._match("*"):
                v *= self._parse_factor()
            elif self._match("/"):
                v /= self._parse_factor()
            elif self._match("%"):
                v = math.fmod(v, self._parse_factor())
            else:
                return v

    def _parse_factor(self) -> float:
        self._skip_spaces()
        if self._match("+"):
            return self._parse_factor()
        if self._match("-"):
            return -self._parse_factor()
        if self._match("("):
            v = self._parse_expression()
            if not self._match(")"):
                raise ValidationError(message="missing closing parenthesis", code="knifer.num.calc_paren")
            return v
        start = self.pos
        while self.pos < len(self.s) and (self.s[self.pos].isdigit() or self.s[self.pos] == "."):
            self.pos += 1
        if start == self.pos:
            raise ValidationError(message=f"expected number at {self.pos}", code="knifer.num.calc_expected")
        return self.cfg.parse_float(self.s[start : self.pos])


def _calculate(expression: str, opts: Sequence[ParseOption] | None = None) -> float:
    if opts is None:
        opts = []
    cfg = _apply_parse_options(opts)
    parser = _ExprParser(expression, cfg)
    result = parser._parse_expression()
    parser._skip_spaces()
    if parser.pos != len(parser.s):
        raise ValidationError(message=f"unexpected token at {parser.pos}", code="knifer.num.calc_trailing")
    return result


# ---------------------------------------------------------------------------
# binary conversion
# ---------------------------------------------------------------------------


def _get_binary_str(number: Any, opts: Sequence[FormatOption] | None = None) -> str:
    if isinstance(number, int):
        return bin(number)[2:]
    if isinstance(number, float):
        raw = struct.pack(">d", number)
        return "".join(f"{b:08b}" for b in raw)
    return ""


def _binary_to_int(binary_str: str, opts: Sequence[ParseOption] | None = None) -> int:
    try:
        return int(binary_str, 2)
    except (ValueError, InvalidOperation):
        return 0


def _binary_to_long(binary_str: str, opts: Sequence[ParseOption] | None = None) -> int:
    return _binary_to_int(binary_str, opts)


def _to_bytes(value: int) -> bytes:
    return struct.pack(">i", value)


def _to_int(data: bytes) -> int:
    if len(data) < 4:
        return 0
    return struct.unpack(">i", data[:4])[0]


def _to_unsigned_byte_array(value: int) -> bytes:
    if value == 0:
        return b""
    result = []
    while value > 0:
        result.append(value & 0xFF)
        value >>= 8
    return bytes(reversed(result))


def _to_unsigned_byte_array_len(length: int, value: int) -> bytes:
    raw = _to_unsigned_byte_array(value)
    if len(raw) > length:
        raise ValidationError(message="standard length exceeded for value", code="knifer.num.byte_len_exceeded")
    return b"\x00" * (length - len(raw)) + raw


def _from_unsigned_byte_array(buf: bytes) -> int:
    return int.from_bytes(buf, "big")


def _from_unsigned_byte_array_range(buf: bytes, off: int, length: int) -> int:
    if off < 0 or length < 0 or off + length > len(buf):
        return 0
    return int.from_bytes(buf[off : off + length], "big")


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------


def _compare(x: _Number, y: _Number) -> int:
    if x < y:
        return -1
    if x > y:
        return 1
    return 0


def _is_greater(a: _Number, b: _Number) -> bool:
    return a > b


def _is_greater_or_equal(a: _Number, b: _Number) -> bool:
    return a >= b


def _is_less(a: _Number, b: _Number) -> bool:
    return a < b


def _is_less_or_equal(a: _Number, b: _Number) -> bool:
    return a <= b


def _is_in(value: _Number, min_include: _Number, max_include: _Number) -> bool:
    return min_include <= value <= max_include


def _equals(a: float, b: float) -> bool:
    return math.isclose(a, b, abs_tol=1e-9)


def _equals_exact(a: float, b: float) -> bool:
    return struct.pack(">d", a) == struct.pack(">d", b)


def _equals_float32_exact(a: float, b: float) -> bool:
    return struct.pack(">f", a) == struct.pack(">f", b)


def _equals_int64(a: int, b: int) -> bool:
    return a == b


def _equals_big_decimal(a: Fraction | None, b: Fraction | None) -> bool:
    if a is b:
        return True
    if a is None or b is None:
        return False
    return a == b


def _equals_char(c1: str, c2: str, ignore_case: bool) -> bool:
    if ignore_case:
        return c1.lower() == c2.lower()
    return c1 == c2


def _min(*nums: _Number) -> _Number:
    if not nums:
        return 0
    return min(nums)


def _max(*nums: _Number) -> _Number:
    if not nums:
        return 0
    return max(nums)


def _sum(*nums: _Number) -> _Number:
    total: _Number = type(nums[0])(0) if nums else 0
    for v in nums:
        total += v
    return total


def _avg(*nums: _Number) -> float:
    if not nums:
        return 0.0
    return float(_sum(*nums)) / len(nums)


def _is_beside(number1: int, number2: int) -> bool:
    return abs(number1 - number2) == 1


# ---------------------------------------------------------------------------
# factorial and combinatorics
# ---------------------------------------------------------------------------


def _factorial(n: int) -> int:
    if n < 0:
        raise ValidationError(message=f"factorial is undefined for negative input: {n}", code="knifer.num.factorial_negative")
    if n < len(_FACTORIALS):
        return _FACTORIALS[n]
    return math.factorial(n)


def _factorial_range(start: int, end: int) -> int:
    if start == 0 or start == end:
        return 1
    if start < end:
        return 0
    result = 1
    for i in range(start, end, -1):
        result *= i
    return result


def _factorial_big(n: int) -> int:
    if n <= 0:
        return 1
    return _factorial_big_range(n, 0)


def _factorial_big_range(start: int, end: int) -> int:
    if start < 0 or end < 0 or start <= end:
        return 1
    result = 1
    for i in range(start, end, -1):
        result *= i
    return result


def _sqrt(x: int) -> int:
    return int(math.isqrt(x))


def _process_multiple(select_num: int, min_num: int) -> int:
    if min_num < 0 or select_num < min_num:
        return 0
    return _math_sub_node(select_num, min_num) // math.factorial(select_num - min_num)


def _math_sub_node(select_num: int, min_num: int) -> int:
    if select_num == min_num:
        return 1
    return select_num * _math_sub_node(select_num - 1, min_num)


def _divisor(m: int, n: int) -> int:
    return math.gcd(m, n)


def _multiple(m: int, n: int) -> int:
    if m == 0 or n == 0:
        return 0
    return _abs_int(m // math.gcd(m, n) * n)


# ---------------------------------------------------------------------------
# conversion
# ---------------------------------------------------------------------------


def _to_big_decimal(number_str: str, opts: Sequence[ParseOption] | None = None) -> Fraction:
    s = number_str.strip().replace(",", "")
    if not s:
        return Fraction(0, 1)
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        if opts is None:
            opts = []
        cfg = _apply_parse_options(opts)
        try:
            return Fraction(cfg.parse_float(s))
        except (ValueError, InvalidOperation, ZeroDivisionError):
            return Fraction(0, 1)


def _to_big_integer(number: str) -> int:
    s = number.strip()
    if not s:
        return 0
    try:
        return int(s)
    except ValueError:
        return _parse_long(s)


def _count(total: int, part: int) -> int:
    if total == 0 or part == 0:
        return 0
    return (total - 1) // part + 1


def _null_to_zero(decimal: Fraction | None) -> Fraction:
    return _null_big_decimal_to_zero(decimal)


def _zero_to_one(value: int) -> int:
    return 1 if value == 0 else value


def _null_int_to_zero(number: int | None) -> int:
    return 0 if number is None else number


def _null_float_to_zero(number: float | None) -> float:
    return 0.0 if number is None else number


def _null_big_int_to_zero(number: int | None) -> int:
    return 0 if number is None else number


def _null_big_decimal_to_zero(number: Fraction | None) -> Fraction:
    return Fraction(0, 1) if number is None else number


def _new_big_integer(s: str) -> tuple[int | None, bool]:
    s = s.strip()
    if not s:
        return None, False
    negate = False
    if s.startswith("-"):
        negate = True
        s = s[1:]
    radix = 10
    lowered = s.lower()
    if lowered.startswith("0x"):
        radix, s = 16, s[2:]
    elif s.startswith("#"):
        radix, s = 16, s[1:]
    elif s.startswith("0") and len(s) > 1:
        radix, s = 8, s[1:]
    try:
        val = int(s, radix)
        return (-val if negate else val), True
    except ValueError:
        return None, False


def _part_value(total: int, part_count: int) -> int:
    return _part_value_with_mode(total, part_count, True)


def _part_value_with_mode(total: int, part_count: int, plus_one_when_has_rem: bool) -> int:
    if part_count == 0:
        return 0
    part = total // part_count
    if plus_one_when_has_rem and total % part_count > 0:
        part += 1
    return part


def _to_double(value: Any, opts: Sequence[DoubleOption] | None = None) -> float:
    if opts is None:
        opts = []
    _apply_double_options(opts)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, int):
        return float(value)
    return 0.0


# ---------------------------------------------------------------------------
# absolute value helpers
# ---------------------------------------------------------------------------


def _abs_integer(v: int) -> int:
    if v < 0:
        return -v
    return v


def _abs_integer_e(v: int) -> tuple[int, str | None]:
    if v < 0 and -v < 0:
        return 0, f"overflow: abs({v})"
    if v < 0:
        return -v, None
    return v, None


def _abs_float32(x: float) -> float:
    return abs(x)


def _abs_float64(x: float) -> float:
    return abs(x)


# ---------------------------------------------------------------------------
# sum / avg for generic numbers
# ---------------------------------------------------------------------------


def _sum_number(values: Sequence[_Number]) -> float:
    return float(sum(values))


def _avg_number(values: Sequence[_Number]) -> float:
    if not values:
        return 0.0
    return _sum_number(values) / len(values)


def _min_integer(a: int, b: int) -> int:
    return a if a <= b else b


def _min_integers(*values: int) -> int:
    if not values:
        return 0
    return min(values)


def _min_float64(a: float, b: float) -> float:
    return a if a <= b else b


def _min_float64s(*values: float) -> float:
    if not values:
        return 0.0
    return min(values)


def _max_integer(a: int, b: int) -> int:
    return a if a >= b else b


def _max_integers(*values: int) -> int:
    if not values:
        return 0
    return max(values)


def _max_float64(a: float, b: float) -> float:
    return a if a >= b else b


def _max_float64s(*values: float) -> float:
    if not values:
        return 0.0
    return max(values)