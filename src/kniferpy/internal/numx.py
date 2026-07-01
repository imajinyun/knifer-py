from __future__ import annotations

import math
from collections.abc import Sequence

from kniferpy.verr import ValidationError

_FACTORIALS: tuple[int, ...] = (
    1,
    1,
    2,
    6,
    24,
    120,
    720,
    5040,
    40320,
    362880,
    3628800,
    39916800,
    479001600,
    6227020800,
    87178291200,
    1307674368000,
    20922789888000,
    355687428096000,
    6402373705728000,
    121645100408832000,
    2432902008176640000,
)


def _strip_sign(text: str) -> str:
    if text and text[0] in "+-":
        return text[1:]
    return text


def is_number(value: str) -> bool:
    text = value.strip()
    if text == "":
        return False
    body = _strip_sign(text)
    lowered = body.lower()
    if lowered.startswith("0x"):
        try:
            int(body[2:], 16)
            return True
        except ValueError:
            return False
    if body and body[-1] in "dDfFlL":
        body = body[:-1]
    try:
        float(body)
        return True
    except ValueError:
        return False


def is_integer(value: str) -> bool:
    text = value.strip()
    if text == "":
        return False
    try:
        int(text, 10)
        return True
    except ValueError:
        return False


def is_double(value: str) -> bool:
    text = value.strip()
    if text == "" or "." not in value:
        return False
    try:
        float(text)
        return True
    except ValueError:
        return False


def is_digits(value: str) -> bool:
    return value != "" and all("0" <= ch <= "9" for ch in value)


def is_prime(n: int) -> bool:
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


def is_odd(n: int) -> bool:
    return n % 2 != 0


def is_even(n: int) -> bool:
    return n % 2 == 0


def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip(), 10)
    except ValueError:
        try:
            return int(float(value.strip()))
        except ValueError:
            return default


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value.strip())
    except ValueError:
        return default


def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        low, high = high, low
    return max(low, min(value, high))


def is_in(value: float, low: float, high: float) -> bool:
    if low > high:
        low, high = high, low
    return low <= value <= high


def compare(a: float, b: float) -> int:
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def sum_values(values: Sequence[float]) -> float:
    return math.fsum(values)


def avg_values(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return math.fsum(values) / len(values)


def min_value(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return min(values)


def max_value(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return max(values)


def ceil_div(a: int, b: int) -> int:
    if b == 0:
        raise ValidationError(
            message="division by zero", code="knifer.num.div_zero"
        )
    return -(-a // b)


def gcd(m: int, n: int) -> int:
    return math.gcd(m, n)


def lcm(m: int, n: int) -> int:
    return math.lcm(m, n)


def round_half_up(value: float, scale: int = 0) -> float:
    factor = float(10**scale)
    scaled = value * factor
    shifted = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    return shifted / factor


def factorial(n: int) -> int:
    if n < 0:
        raise ValidationError(
            message=f"factorial is undefined for negative input: {n}",
            code="knifer.num.factorial_negative",
            context={"n": n},
        )
    if n < len(_FACTORIALS):
        return _FACTORIALS[n]
    return math.factorial(n)


def num_range(start: int, stop: int, step: int = 1) -> list[int]:
    if step == 0:
        raise ValidationError(message="step must not be zero", code="knifer.num.step_zero")
    return list(range(start, stop, step))


def range_closed(start: int, stop: int, step: int = 1) -> list[int]:
    if step == 0:
        raise ValidationError(message="step must not be zero", code="knifer.num.step_zero")
    if step > 0:
        return list(range(start, stop + 1, step))
    return list(range(start, stop - 1, step))
