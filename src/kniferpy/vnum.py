from __future__ import annotations

from collections.abc import Callable, Sequence
from fractions import Fraction
from typing import Any

from kniferpy.internal import numx
from kniferpy.internal.numx import (
    DoubleOption,
    FormatOption,
    ParseOption,
    RandomNumberOption,
    RoundingMode,
    _with_double_format_float,
    _with_double_parse_float,
    _with_format_float,
    _with_format_int,
    _with_parse_float,
    _with_parse_int,
    _with_random_reader,
)

# ── Go-compat type aliases ────────────────────────────────────────────────────

# Number constraint: all numeric types (Go compat: ~int | ~float | ...)
Number = int | float
"""Union of all built-in numeric types (Go compat: constraint.Number)."""

# Ordered constraint: all ordered types (Go compat: cmp.Ordered)
Ordered = int | float | str
"""Union of all ordered types (Go compat: cmp.Ordered)."""

__all__ = [
    # Types
    "DoubleOption",
    "FormatOption",
    "Number",
    "Ordered",
    "ParseOption",
    "RandomNumberOption",
    "RoundingMode",
    # Constants
    "RoundDown",
    "RoundHalfEven",
    "RoundHalfUp",
    # Option builders
    "WithDoubleFormatFloatFunc",
    "WithDoubleParseFloatFunc",
    "WithFormatFloatFunc",
    "WithFormatIntFunc",
    "WithParseFloatFunc",
    "WithParseIntFunc",
    "WithRandomReader",
    # Arithmetic
    "AbsFloat32",
    "AbsFloat64",
    "AbsInteger",
    "AbsIntegerE",
    "Add",
    "AddStr",
    "AvgNumber",
    "CeilDiv",
    "Div",
    "DivWithMode",
    "MaxFloat64",
    "MaxFloat64s",
    "MaxInteger",
    "MaxIntegers",
    "MinFloat64",
    "MinFloat64s",
    "MinInteger",
    "MinIntegers",
    "Mul",
    "MulStr",
    "Pow",
    "PowWithMode",
    "Sub",
    "SubStr",
    "SumNumber",
    # Rounding
    "Round",
    "RoundDownFloat",
    "RoundHalfEvenFloat",
    "RoundMode",
    "RoundStr",
    "RoundStrWithOptions",
    # Formatting
    "DecimalFormat",
    "DecimalFormatMoney",
    "DecimalFormatMoneyWithOptions",
    "DecimalFormatWithOptions",
    "FormatPercent",
    "FormatPercentWithOptions",
    "ToStr",
    "ToStrDefault",
    "ToStrDefaultWithOptions",
    "ToStrStrip",
    "ToStrStripWithOptions",
    "ToStrWithOptions",
    # Validation
    "IsDigits",
    "IsDouble",
    "IsDoubleWithOptions",
    "IsEven",
    "IsInteger",
    "IsIntegerWithOptions",
    "IsLong",
    "IsLongWithOptions",
    "IsNumber",
    "IsNumberWithOptions",
    "IsOdd",
    "IsPowerOfTwo",
    "IsPrimes",
    "IsValid",
    "IsValidFloat32",
    "IsValidNumber",
    # Parsing
    "ParseDouble",
    "ParseDoubleDefault",
    "ParseDoubleDefaultWithOptions",
    "ParseDoubleWithOptions",
    "ParseFloat",
    "ParseFloatDefault",
    "ParseFloatDefaultWithOptions",
    "ParseFloatWithOptions",
    "ParseInt",
    "ParseIntDefault",
    "ParseIntDefaultWithOptions",
    "ParseIntWithOptions",
    "ParseLong",
    "ParseLongDefault",
    "ParseLongDefaultWithOptions",
    "ParseLongWithOptions",
    "ParseNumber",
    "ParseNumberWithOptions",
    # Random
    "GenBySet",
    "GenBySetWithOptions",
    "GenRandomNumber",
    "GenRandomNumberWithOptions",
    "GenRandomNumberWithSeed",
    "GenRandomNumberWithSeedWithOptions",
    # Range
    "AppendRange",
    "Range",
    "RangeClosed",
    # Calculator
    "Calculate",
    "CalculateWithOptions",
    # Binary
    "BinaryToInt",
    "BinaryToIntWithOptions",
    "BinaryToLong",
    "BinaryToLongWithOptions",
    "FromUnsignedByteArray",
    "FromUnsignedByteArrayRange",
    "GetBinaryStr",
    "GetBinaryStrWithOptions",
    "ToBytes",
    "ToInt",
    "ToUnsignedByteArray",
    "ToUnsignedByteArrayLen",
    # Comparison
    "Avg",
    "Compare",
    "Equals",
    "EqualsBigDecimal",
    "EqualsChar",
    "EqualsExact",
    "EqualsFloat32Exact",
    "EqualsInt64",
    "IsBeside",
    "IsGreater",
    "IsGreaterOrEqual",
    "IsIn",
    "IsLess",
    "IsLessOrEqual",
    "Max",
    "Min",
    "Sum",
    # Factorial / Math
    "Divisor",
    "Factorial",
    "FactorialBig",
    "FactorialBigRange",
    "FactorialRange",
    "Multiple",
    "ProcessMultiple",
    "Sqrt",
    # Conversion
    "Count",
    "NewBigInteger",
    "Null2Zero",
    "NullBigDecimalToZero",
    "NullBigIntToZero",
    "NullToZero",
    "PartValue",
    "PartValueWithMode",
    "ToBigDecimal",
    "ToBigDecimalWithOptions",
    "ToBigInteger",
    "ToDouble",
    "ToDoubleWithOptions",
    "Zero2One",
]


# ---------------------------------------------------------------------------
# rounding mode
# ---------------------------------------------------------------------------

RoundHalfUp = RoundingMode.HALF_UP
RoundHalfEven = RoundingMode.HALF_EVEN
RoundDown = RoundingMode.DOWN


# ---------------------------------------------------------------------------
# option constructors
# ---------------------------------------------------------------------------


def WithRandomReader(reader: Callable[[int], int]) -> RandomNumberOption:
    return _with_random_reader(reader)


def WithParseIntFunc(parser: Callable[[str], int]) -> ParseOption:
    return _with_parse_int(parser)


def WithParseFloatFunc(parser: Callable[[str], float]) -> ParseOption:
    return _with_parse_float(parser)


def WithFormatFloatFunc(formatter: Callable[..., str]) -> FormatOption:
    return _with_format_float(formatter)


def WithFormatIntFunc(formatter: Callable[..., str]) -> FormatOption:
    return _with_format_int(formatter)


def WithDoubleParseFloatFunc(parser: Callable[[str], float]) -> DoubleOption:
    return _with_double_parse_float(parser)


def WithDoubleFormatFloatFunc(formatter: Callable[..., str]) -> DoubleOption:
    return _with_double_format_float(formatter)


# ---------------------------------------------------------------------------
# arithmetic
# ---------------------------------------------------------------------------


def Add(*values: float) -> float:
    return numx._add(values)


def AddStr(*values: str) -> Fraction:
    return numx._add_str(values)


def Sub(*values: float) -> float:
    return numx._sub(values)


def SubStr(*values: str) -> Fraction:
    return numx._sub_str(values)


def Mul(*values: float) -> float:
    return numx._mul(values)


def MulStr(*values: str) -> Fraction:
    return numx._mul_str(values)


def Div(a: float, b: float, scale: int | None = None) -> float:
    if scale is None:
        return numx._div(a, b)
    return numx._number_div(a, b, scale)


def DivWithMode(a: float, b: float, scale: int, mode: RoundingMode) -> float:
    return numx._div_with_mode(a, b, scale, mode)


def CeilDiv(v1: int, v2: int) -> int:
    return numx._ceil_div(v1, v2)


def Pow(number: float, n: int) -> float:
    return numx._pow(number, n)


def PowWithMode(number: float, n: int, scale: int, mode: RoundingMode) -> float:
    return numx._pow_with_mode(number, n, scale, mode)


def AbsInteger(v: int) -> int:
    return numx._abs_integer(v)


def AbsIntegerE(v: int) -> tuple[int, str | None]:
    return numx._abs_integer_e(v)


def AbsFloat32(x: float) -> float:
    return numx._abs_float32(x)


def AbsFloat64(x: float) -> float:
    return numx._abs_float64(x)


def SumNumber(*values: float) -> float:
    return numx._sum_number(values)


def AvgNumber(*values: float) -> float:
    return numx._avg_number(values)


def MinInteger(a: int, b: int) -> int:
    return numx._min_integer(a, b)


def MinIntegers(*values: int) -> int:
    return numx._min_integers(*values)


def MinFloat64(a: float, b: float) -> float:
    return numx._min_float64(a, b)


def MinFloat64s(*values: float) -> float:
    return numx._min_float64s(*values)


def MaxInteger(a: int, b: int) -> int:
    return numx._max_integer(a, b)


def MaxIntegers(*values: int) -> int:
    return numx._max_integers(*values)


def MaxFloat64(a: float, b: float) -> float:
    return numx._max_float64(a, b)


def MaxFloat64s(*values: float) -> float:
    return numx._max_float64s(*values)


# ---------------------------------------------------------------------------
# rounding
# ---------------------------------------------------------------------------


def Round(v: float, scale: int) -> float:
    return numx._round(v, scale)


def RoundMode(v: float, scale: int, mode: RoundingMode) -> float:
    return numx._round_mode(v, scale, mode)


def RoundStr(v: float, scale: int, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._round_str(v, scale, opts)


def RoundHalfEvenFloat(v: float, scale: int) -> float:
    return numx._round_half_even_float(v, scale)


def RoundDownFloat(v: float, scale: int) -> float:
    return numx._round_down_float(v, scale)


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------


def DecimalFormat(format_str: str, v: float, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._decimal_format(format_str, v, opts)


def DecimalFormatMoney(v: float, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._decimal_format_money(v, opts)


def FormatPercent(number: float, scale: int, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._format_percent(number, scale, opts)


def ToStr(number: float, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._to_str(number, opts)


def ToStrDefault(number: float | None, default_value: str, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._to_str_default(number, default_value, opts)


def ToStrStrip(number: float, strip_trailing_zeros: bool, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._to_str_strip(number, strip_trailing_zeros, opts)


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def IsNumber(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    return numx._is_number(s, opts)


def IsInteger(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    return numx._is_integer(s, opts)


def IsLong(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    return numx._is_long(s, opts)


def IsDouble(s: str, opts: Sequence[ParseOption] | None = None) -> bool:
    return numx._is_double(s, opts)


def IsDigits(s: str) -> bool:
    return numx._is_digits(s)


def IsPrimes(n: int) -> bool:
    return numx._is_primes(n)


def IsValidNumber(number: Any) -> bool:
    return numx._is_valid_number(number)


def IsValid(number: float) -> bool:
    return numx._is_valid(number)


def IsValidFloat32(number: float) -> bool:
    return numx._is_valid_float32(number)


def IsOdd(num: int) -> bool:
    return numx._is_odd(num)


def IsEven(num: int) -> bool:
    return numx._is_even(num)


def IsPowerOfTwo(n: int) -> bool:
    return numx._is_power_of_two(n)


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------


def ParseInt(number: str, opts: Sequence[ParseOption] | None = None) -> int:
    return numx._parse_int_with_opts(number, opts)


def ParseLong(number: str, opts: Sequence[ParseOption] | None = None) -> int:
    return numx._parse_long(number, opts)


def ParseFloat(number: str, opts: Sequence[ParseOption] | None = None) -> float:
    return numx._parse_float(number, opts)


def ParseDouble(number: str, opts: Sequence[ParseOption] | None = None) -> float:
    return numx._parse_double(number, opts)


def ParseNumber(number_str: str, opts: Sequence[ParseOption] | None = None) -> float | None:
    return numx._parse_number(number_str, opts)


def ParseIntDefault(number_str: str, default_value: int, opts: Sequence[ParseOption] | None = None) -> int:
    return numx._parse_int_default(number_str, default_value, opts)


def ParseLongDefault(number_str: str, default_value: int, opts: Sequence[ParseOption] | None = None) -> int:
    return numx._parse_long_default(number_str, default_value, opts)


def ParseFloatDefault(number_str: str, default_value: float, opts: Sequence[ParseOption] | None = None) -> float:
    return numx._parse_float_default(number_str, default_value, opts)


def ParseDoubleDefault(number_str: str, default_value: float, opts: Sequence[ParseOption] | None = None) -> float:
    return numx._parse_double_default(number_str, default_value, opts)


# ---------------------------------------------------------------------------
# random generation
# ---------------------------------------------------------------------------


def GenRandomNumber(begin: int, end: int, size: int, opts: Sequence[RandomNumberOption] | None = None) -> list[int]:
    return numx._gen_random_number(begin, end, size, opts)


def GenRandomNumberWithSeed(
    begin: int, end: int, size: int, seed: list[int], opts: Sequence[RandomNumberOption] | None = None
) -> list[int]:
    return numx._gen_random_number_with_seed(begin, end, size, seed, opts)


def GenBySet(begin: int, end: int, size: int, opts: Sequence[RandomNumberOption] | None = None) -> list[int]:
    return numx._gen_by_set(begin, end, size, opts)


# ---------------------------------------------------------------------------
# range
# ---------------------------------------------------------------------------


def Range(start: int, end: int, step: int = 1) -> list[int]:
    return numx._num_range(start, end, step)


def RangeClosed(start: int, stop: int, step: int = 1) -> list[int]:
    return numx._range_closed(start, stop, step)


def AppendRange(start: int, stop: int, step: int, values: list[int]) -> list[int]:
    return numx._append_range(start, stop, step, values)


# ---------------------------------------------------------------------------
# expression calculator
# ---------------------------------------------------------------------------


def Calculate(expression: str, opts: Sequence[ParseOption] | None = None) -> float:
    return numx._calculate(expression, opts)


# ---------------------------------------------------------------------------
# binary conversion
# ---------------------------------------------------------------------------


def GetBinaryStr(number: Any, opts: Sequence[FormatOption] | None = None) -> str:
    return numx._get_binary_str(number, opts)


def BinaryToInt(binary_str: str, opts: Sequence[ParseOption] | None = None) -> int:
    return numx._binary_to_int(binary_str, opts)


def BinaryToLong(binary_str: str, opts: Sequence[ParseOption] | None = None) -> int:
    return numx._binary_to_long(binary_str, opts)


def ToBytes(value: int) -> bytes:
    return numx._to_bytes(value)


def ToInt(data: bytes) -> int:
    return numx._to_int(data)


def ToUnsignedByteArray(value: int) -> bytes:
    return numx._to_unsigned_byte_array(value)


def ToUnsignedByteArrayLen(length: int, value: int) -> bytes:
    return numx._to_unsigned_byte_array_len(length, value)


def FromUnsignedByteArray(buf: bytes) -> int:
    return numx._from_unsigned_byte_array(buf)


def FromUnsignedByteArrayRange(buf: bytes, off: int, length: int) -> int:
    return numx._from_unsigned_byte_array_range(buf, off, length)


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------


def Compare(x: int | float, y: int | float) -> int:
    return numx._compare(x, y)


def IsGreater(a: int | float, b: int | float) -> bool:
    return numx._is_greater(a, b)


def IsGreaterOrEqual(a: int | float, b: int | float) -> bool:
    return numx._is_greater_or_equal(a, b)


def IsLess(a: int | float, b: int | float) -> bool:
    return numx._is_less(a, b)


def IsLessOrEqual(a: int | float, b: int | float) -> bool:
    return numx._is_less_or_equal(a, b)


def IsIn(value: int | float, min_include: int | float, max_include: int | float) -> bool:
    return numx._is_in(value, min_include, max_include)


def Equals(a: float, b: float) -> bool:
    return numx._equals(a, b)


def EqualsExact(a: float, b: float) -> bool:
    return numx._equals_exact(a, b)


def EqualsFloat32Exact(a: float, b: float) -> bool:
    return numx._equals_float32_exact(a, b)


def EqualsInt64(a: int, b: int) -> bool:
    return numx._equals_int64(a, b)


def EqualsBigDecimal(a: Fraction | None, b: Fraction | None) -> bool:
    return numx._equals_big_decimal(a, b)


def EqualsChar(c1: str, c2: str, ignore_case: bool) -> bool:
    return numx._equals_char(c1, c2, ignore_case)


def Min(*nums: int | float) -> int | float:
    return numx._min(*nums)


def Max(*nums: int | float) -> int | float:
    return numx._max(*nums)


def Sum(*nums: int | float) -> int | float:
    return numx._sum(*nums)


def Avg(*nums: int | float) -> float:
    return numx._avg(*nums)


def IsBeside(number1: int, number2: int) -> bool:
    return numx._is_beside(number1, number2)


# ---------------------------------------------------------------------------
# factorial and combinatorics
# ---------------------------------------------------------------------------


def Factorial(n: int) -> int:
    return numx._factorial(n)


def FactorialRange(start: int, end: int) -> int:
    return numx._factorial_range(start, end)


def FactorialBig(n: int) -> int:
    return numx._factorial_big(n)


def FactorialBigRange(start: int, end: int) -> int:
    return numx._factorial_big_range(start, end)


def Sqrt(x: int) -> int:
    return numx._sqrt(x)


def ProcessMultiple(select_num: int, min_num: int) -> int:
    return numx._process_multiple(select_num, min_num)


def Divisor(m: int, n: int) -> int:
    return numx._divisor(m, n)


def Multiple(m: int, n: int) -> int:
    return numx._multiple(m, n)


# ---------------------------------------------------------------------------
# conversion
# ---------------------------------------------------------------------------


def ToBigDecimal(number_str: str, opts: Sequence[ParseOption] | None = None) -> Fraction:
    return numx._to_big_decimal(number_str, opts)


def ToBigInteger(number: str) -> int:
    return numx._to_big_integer(number)


def Count(total: int, part: int) -> int:
    return numx._count(total, part)


def Null2Zero(decimal: Fraction | None) -> Fraction:
    return numx._null_to_zero(decimal)


def Zero2One(value: int) -> int:
    return numx._zero_to_one(value)


def NullToZero(value: int | float | None) -> int | float:
    if isinstance(value, float) or value is None:
        return numx._null_float_to_zero(value)
    return numx._null_int_to_zero(value)


def NullBigIntToZero(number: int | None) -> int:
    return numx._null_big_int_to_zero(number)


def NullBigDecimalToZero(number: Fraction | None) -> Fraction:
    return numx._null_big_decimal_to_zero(number)


def NewBigInteger(s: str) -> tuple[int | None, bool]:
    return numx._new_big_integer(s)


def PartValue(total: int, part_count: int) -> int:
    return numx._part_value(total, part_count)


def PartValueWithMode(total: int, part_count: int, plus_one_when_has_rem: bool) -> int:
    return numx._part_value_with_mode(total, part_count, plus_one_when_has_rem)


def ToDouble(value: Any, opts: Sequence[DoubleOption] | None = None) -> float:
    return numx._to_double(value, opts)


# ---------------------------------------------------------------------------
# *WithOptions aliases (Go compat)
# ---------------------------------------------------------------------------

ParseIntWithOptions = ParseInt
ParseLongWithOptions = ParseLong
ParseFloatWithOptions = ParseFloat
ParseDoubleWithOptions = ParseDouble
ParseNumberWithOptions = ParseNumber
ParseIntDefaultWithOptions = ParseIntDefault
ParseLongDefaultWithOptions = ParseLongDefault
ParseFloatDefaultWithOptions = ParseFloatDefault
ParseDoubleDefaultWithOptions = ParseDoubleDefault
IsNumberWithOptions = IsNumber
IsIntegerWithOptions = IsInteger
IsLongWithOptions = IsLong
IsDoubleWithOptions = IsDouble
GenRandomNumberWithOptions = GenRandomNumber
GenRandomNumberWithSeedWithOptions = GenRandomNumberWithSeed
GenBySetWithOptions = GenBySet
CalculateWithOptions = Calculate
GetBinaryStrWithOptions = GetBinaryStr
BinaryToIntWithOptions = BinaryToInt
BinaryToLongWithOptions = BinaryToLong
DecimalFormatWithOptions = DecimalFormat
DecimalFormatMoneyWithOptions = DecimalFormatMoney
FormatPercentWithOptions = FormatPercent
ToStrWithOptions = ToStr
ToStrDefaultWithOptions = ToStrDefault
ToStrStripWithOptions = ToStrStrip
RoundStrWithOptions = RoundStr
ToBigDecimalWithOptions = ToBigDecimal
ToDoubleWithOptions = ToDouble