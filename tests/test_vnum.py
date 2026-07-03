from __future__ import annotations

import pytest
from fractions import Fraction

from kniferpy import vnum
from kniferpy.internal.numx import RoundingMode
from kniferpy.verr import ValidationError


# ---------------------------------------------------------------------------
# arithmetic
# ---------------------------------------------------------------------------


class TestArithmetic:
    def test_add_floats(self) -> None:
        assert vnum.Add(1, 2, 3) == pytest.approx(6.0)
        assert vnum.Add() == pytest.approx(0.0)
        assert vnum.Add(0.1, 0.2) == pytest.approx(0.3)

    def test_add_str(self) -> None:
        result = vnum.AddStr("0.1", "0.2")
        assert isinstance(result, Fraction)
        assert float(result) == pytest.approx(0.3)

    def test_add_str_empty(self) -> None:
        result = vnum.AddStr()
        assert float(result) == 0.0

    def test_sub_floats(self) -> None:
        assert vnum.Sub(10, 3, 2) == pytest.approx(5.0)
        assert vnum.Sub() == pytest.approx(0.0)

    def test_sub_str(self) -> None:
        result = vnum.SubStr("10", "3", "2")
        assert float(result) == pytest.approx(5.0)

    def test_mul_floats(self) -> None:
        assert vnum.Mul(2, 3, 4) == pytest.approx(24.0)
        assert vnum.Mul() == pytest.approx(0.0)

    def test_mul_str(self) -> None:
        result = vnum.MulStr("2", "3", "4")
        assert float(result) == pytest.approx(24.0)

    def test_div(self) -> None:
        assert vnum.Div(10, 3) == pytest.approx(3.3333333333, abs=1e-6)
        assert vnum.Div(10, 0) == pytest.approx(0.0)
        assert vnum.Div(10, 3, 2) == pytest.approx(3.33)

    def test_div_with_mode(self) -> None:
        assert vnum.DivWithMode(10, 3, 2, RoundingMode.HALF_UP) == pytest.approx(3.33)
        assert vnum.DivWithMode(10, 3, 2, RoundingMode.DOWN) == pytest.approx(3.33)
        assert vnum.DivWithMode(10, 0, 2, RoundingMode.HALF_UP) == pytest.approx(0.0)

    def test_ceil_div(self) -> None:
        assert vnum.CeilDiv(7, 2) == 4
        assert vnum.CeilDiv(6, 2) == 3
        assert vnum.CeilDiv(0, 5) == 0

    def test_pow(self) -> None:
        assert vnum.Pow(2, 3) == pytest.approx(8.0)
        assert vnum.Pow(2, -1) == pytest.approx(0.50)

    def test_pow_with_mode(self) -> None:
        assert vnum.PowWithMode(2, -1, 2, RoundingMode.HALF_UP) == pytest.approx(0.50)

    def test_abs_integer(self) -> None:
        assert vnum.AbsInteger(-5) == 5
        assert vnum.AbsInteger(5) == 5
        assert vnum.AbsInteger(0) == 0

    def test_abs_integer_e(self) -> None:
        val, err = vnum.AbsIntegerE(-5)
        assert val == 5
        assert err is None

    def test_abs_float32(self) -> None:
        assert vnum.AbsFloat32(-3.14) == pytest.approx(3.14)

    def test_abs_float64(self) -> None:
        assert vnum.AbsFloat64(-3.14) == pytest.approx(3.14)

    def test_sum_number(self) -> None:
        assert vnum.SumNumber(1, 2, 3) == pytest.approx(6.0)
        assert vnum.SumNumber(1.5, 2.5) == pytest.approx(4.0)

    def test_avg_number(self) -> None:
        assert vnum.AvgNumber(2, 4, 6) == pytest.approx(4.0)
        assert vnum.AvgNumber() == pytest.approx(0.0)

    def test_min_integer(self) -> None:
        assert vnum.MinInteger(3, 1) == 1
        assert vnum.MinInteger(1, 3) == 1

    def test_min_integers(self) -> None:
        assert vnum.MinIntegers(3, 1, 2) == 1
        assert vnum.MinIntegers() == 0

    def test_min_float64(self) -> None:
        assert vnum.MinFloat64(3.0, 1.0) == pytest.approx(1.0)

    def test_min_float64s(self) -> None:
        assert vnum.MinFloat64s(3.0, 1.0, 2.0) == pytest.approx(1.0)
        assert vnum.MinFloat64s() == pytest.approx(0.0)

    def test_max_integer(self) -> None:
        assert vnum.MaxInteger(3, 1) == 3

    def test_max_integers(self) -> None:
        assert vnum.MaxIntegers(3, 1, 2) == 3
        assert vnum.MaxIntegers() == 0

    def test_max_float64(self) -> None:
        assert vnum.MaxFloat64(3.0, 1.0) == pytest.approx(3.0)

    def test_max_float64s(self) -> None:
        assert vnum.MaxFloat64s(3.0, 1.0, 2.0) == pytest.approx(3.0)
        assert vnum.MaxFloat64s() == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# rounding
# ---------------------------------------------------------------------------


class TestRounding:
    def test_round(self) -> None:
        assert vnum.Round(3.14159, 2) == pytest.approx(3.14)
        assert vnum.Round(3.14159, 0) == pytest.approx(3.0)
        assert vnum.Round(3.5, 0) == pytest.approx(4.0)

    def test_round_mode(self) -> None:
        assert vnum.RoundMode(3.14159, 2, RoundingMode.HALF_UP) == pytest.approx(3.14)
        assert vnum.RoundMode(3.14159, 2, RoundingMode.DOWN) == pytest.approx(3.14)
        assert vnum.RoundMode(2.5, 0, RoundingMode.HALF_EVEN) == pytest.approx(2.0)
        assert vnum.RoundMode(3.5, 0, RoundingMode.HALF_EVEN) == pytest.approx(4.0)

    def test_round_str(self) -> None:
        result = vnum.RoundStr(3.14159, 2)
        assert result == "3.14"

    def test_round_half_even_float(self) -> None:
        result = vnum.RoundHalfEvenFloat(2.5, 0)
        assert result == pytest.approx(2.0)

    def test_round_down_float(self) -> None:
        result = vnum.RoundDownFloat(3.99, 0)
        assert result == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------


class TestFormatting:
    def test_decimal_format(self) -> None:
        assert vnum.DecimalFormat("0.00", 3.14159) == "3.14"
        assert vnum.DecimalFormat("0", 3.7) == "4"
        assert vnum.DecimalFormat("", 3.7) == "4"

    def test_decimal_format_money(self) -> None:
        result = vnum.DecimalFormatMoney(12345.6)
        assert "12,345.60" in result or "12,346" in result or result == "12,346"

    def test_format_percent(self) -> None:
        result = vnum.FormatPercent(0.1234, 2)
        assert "12.34%" in result or "12%" in result

    def test_to_str(self) -> None:
        result = vnum.ToStr(12.34)
        assert result == "12.34"

    def test_to_str_default(self) -> None:
        assert vnum.ToStrDefault(12.34, "n/a") == "12.34"
        assert vnum.ToStrDefault(None, "n/a") == "n/a"

    def test_to_str_strip(self) -> None:
        result = vnum.ToStrStrip(12.3400, True)
        assert result == "12.34"


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_is_number(self) -> None:
        assert vnum.IsNumber("  -3.14 ")
        assert vnum.IsNumber("0xFF")
        assert vnum.IsNumber("1e5")
        assert not vnum.IsNumber("abc")
        assert not vnum.IsNumber("")

    def test_is_integer(self) -> None:
        assert vnum.IsInteger("42")
        assert vnum.IsInteger("-10")
        assert not vnum.IsInteger("3.14")
        assert not vnum.IsInteger("")

    def test_is_long(self) -> None:
        assert vnum.IsLong("42")
        assert not vnum.IsLong("3.14")

    def test_is_double(self) -> None:
        assert vnum.IsDouble("3.14")
        assert not vnum.IsDouble("3")
        assert not vnum.IsDouble("")

    def test_is_digits(self) -> None:
        assert vnum.IsDigits("12345")
        assert not vnum.IsDigits("-1")
        assert not vnum.IsDigits("")

    def test_is_primes(self) -> None:
        assert vnum.IsPrimes(2)
        assert vnum.IsPrimes(3)
        assert vnum.IsPrimes(7)
        assert vnum.IsPrimes(11)
        assert not vnum.IsPrimes(1)
        assert not vnum.IsPrimes(4)
        assert not vnum.IsPrimes(9)

    def test_is_valid_number(self) -> None:
        assert vnum.IsValidNumber(42.0)
        assert vnum.IsValidNumber(42)
        assert not vnum.IsValidNumber(None)
        assert not vnum.IsValidNumber(float("nan"))

    def test_is_valid(self) -> None:
        assert vnum.IsValid(1.0)
        assert not vnum.IsValid(float("nan"))
        assert not vnum.IsValid(float("inf"))

    def test_is_odd_even(self) -> None:
        assert vnum.IsOdd(3)
        assert not vnum.IsOdd(4)
        assert vnum.IsEven(4)
        assert not vnum.IsEven(3)

    def test_is_power_of_two(self) -> None:
        assert vnum.IsPowerOfTwo(1)
        assert vnum.IsPowerOfTwo(2)
        assert vnum.IsPowerOfTwo(4)
        assert vnum.IsPowerOfTwo(8)
        assert not vnum.IsPowerOfTwo(0)
        assert not vnum.IsPowerOfTwo(6)
        assert not vnum.IsPowerOfTwo(-2)


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------


class TestParsing:
    def test_parse_int(self) -> None:
        assert vnum.ParseInt("42") == 42
        assert vnum.ParseInt("-10") == -10
        assert vnum.ParseInt("") == 0
        assert vnum.ParseInt("  123  ") == 123

    def test_parse_long(self) -> None:
        assert vnum.ParseLong("42") == 42
        assert vnum.ParseLong("") == 0

    def test_parse_float(self) -> None:
        assert vnum.ParseFloat("3.14") == pytest.approx(3.14, rel=0.01)

    def test_parse_double(self) -> None:
        assert vnum.ParseDouble("3.14") == pytest.approx(3.14)
        assert vnum.ParseDouble("") == pytest.approx(0.0)

    def test_parse_number(self) -> None:
        result = vnum.ParseNumber("3.14")
        assert result is not None
        assert result == pytest.approx(3.14)

    def test_parse_int_default(self) -> None:
        assert vnum.ParseIntDefault("42", -1) == 42
        assert vnum.ParseIntDefault("bad", -1) == -1
        assert vnum.ParseIntDefault("", -1) == -1

    def test_parse_long_default(self) -> None:
        assert vnum.ParseLongDefault("42", -1) == 42
        assert vnum.ParseLongDefault("bad", -1) == -1

    def test_parse_float_default(self) -> None:
        assert vnum.ParseFloatDefault("3.5", 1.0) == pytest.approx(3.5, rel=0.01)
        assert vnum.ParseFloatDefault("bad", 1.0) == pytest.approx(1.0)

    def test_parse_double_default(self) -> None:
        assert vnum.ParseDoubleDefault("3.5", 1.0) == pytest.approx(3.5)
        assert vnum.ParseDoubleDefault("bad", 1.0) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# random generation
# ---------------------------------------------------------------------------


class TestRandom:
    def test_gen_random_number(self) -> None:
        result = vnum.GenRandomNumber(1, 10, 3)
        assert len(result) == 3
        assert all(1 <= x < 10 for x in result)
        assert len(set(result)) == 3  # unique

    def test_gen_random_number_swapped_range(self) -> None:
        result = vnum.GenRandomNumber(10, 1, 3)
        assert len(result) == 3
        assert all(1 <= x < 10 for x in result)

    def test_gen_random_number_invalid(self) -> None:
        assert vnum.GenRandomNumber(1, 5, 10) == []
        assert vnum.GenRandomNumber(1, 5, -1) == []

    def test_gen_random_number_with_seed(self) -> None:
        result = vnum.GenRandomNumberWithSeed(1, 10, 3, [1, 3, 5, 7, 9])
        assert len(result) == 3
        assert all(x in [1, 3, 5, 7, 9] for x in result)

    def test_gen_by_set(self) -> None:
        result = vnum.GenBySet(1, 10, 5)
        assert len(result) == 5
        assert len(set(result)) == 5
        assert all(1 <= x < 10 for x in result)


# ---------------------------------------------------------------------------
# range
# ---------------------------------------------------------------------------


class TestRange:
    def test_range(self) -> None:
        assert vnum.Range(0, 5, 2) == [0, 2, 4]
        assert vnum.Range(5, 0, -1) == [5, 4, 3, 2, 1]
        assert vnum.Range(0, 5) == [0, 1, 2, 3, 4]

    def test_range_closed(self) -> None:
        assert vnum.RangeClosed(1, 3) == [1, 2, 3]
        assert vnum.RangeClosed(5, 5) == [5]
        assert vnum.RangeClosed(0, 5, 2) == [0, 2, 4]

    def test_append_range(self) -> None:
        result = vnum.AppendRange(4, 6, 1, [1, 2, 3])
        assert result == [1, 2, 3, 4, 5, 6]


# ---------------------------------------------------------------------------
# expression calculator
# ---------------------------------------------------------------------------


class TestCalculator:
    def test_calculate_basic(self) -> None:
        assert vnum.Calculate("1 + 2 * 3") == pytest.approx(7.0)
        assert vnum.Calculate("(1 + 2) * 3") == pytest.approx(9.0)
        assert vnum.Calculate("10 / 3") == pytest.approx(3.333333, abs=1e-4)

    def test_calculate_mod(self) -> None:
        assert vnum.Calculate("10 % 3") == pytest.approx(1.0)

    def test_calculate_unary(self) -> None:
        assert vnum.Calculate("-5") == pytest.approx(-5.0)
        assert vnum.Calculate("+5") == pytest.approx(5.0)

    def test_calculate_error(self) -> None:
        with pytest.raises(ValidationError):
            vnum.Calculate("(1 + 2")


# ---------------------------------------------------------------------------
# binary conversion
# ---------------------------------------------------------------------------


class TestBinary:
    def test_to_bytes_and_to_int(self) -> None:
        b = vnum.ToBytes(42)
        assert vnum.ToInt(b) == 42

    def test_to_int_short(self) -> None:
        assert vnum.ToInt(b"\x00") == 0

    def test_binary_str(self) -> None:
        result = vnum.GetBinaryStr(42)
        assert isinstance(result, str)

    def test_binary_to_int(self) -> None:
        assert vnum.BinaryToInt("1010") == 10

    def test_binary_to_long(self) -> None:
        assert vnum.BinaryToLong("1010") == 10

    def test_unsigned_byte_array(self) -> None:
        assert vnum.ToUnsignedByteArray(0) == b""
        b = vnum.ToUnsignedByteArray(255)
        assert b == b"\xff"

    def test_unsigned_byte_array_len(self) -> None:
        result = vnum.ToUnsignedByteArrayLen(4, 255)
        assert result == b"\x00\x00\x00\xff"

    def test_from_unsigned_byte_array(self) -> None:
        assert vnum.FromUnsignedByteArray(b"\x00\xff") == 255

    def test_from_unsigned_byte_array_range(self) -> None:
        assert vnum.FromUnsignedByteArrayRange(b"\x00\x01\x02\x03", 0, 2) == 1


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------


class TestComparison:
    def test_compare(self) -> None:
        assert vnum.Compare(1, 2) == -1
        assert vnum.Compare(3, 3) == 0
        assert vnum.Compare(5, 3) == 1

    def test_is_greater(self) -> None:
        assert vnum.IsGreater(5, 3)
        assert vnum.IsGreater(3.5, 3.0)
        assert not vnum.IsGreater(3, 5)

    def test_is_greater_or_equal(self) -> None:
        assert vnum.IsGreaterOrEqual(5, 5)
        assert vnum.IsGreaterOrEqual(5, 3)

    def test_is_less(self) -> None:
        assert vnum.IsLess(3, 5)
        assert not vnum.IsLess(5, 3)

    def test_is_less_or_equal(self) -> None:
        assert vnum.IsLessOrEqual(3, 3)
        assert vnum.IsLessOrEqual(3, 5)

    def test_is_in(self) -> None:
        assert vnum.IsIn(5, 0, 10)
        assert not vnum.IsIn(15, 0, 10)
        assert vnum.IsIn(0, 0, 10)

    def test_equals(self) -> None:
        assert vnum.Equals(0.1 + 0.2, 0.3)
        assert not vnum.Equals(0.1, 0.2)

    def test_equals_exact(self) -> None:
        assert vnum.EqualsExact(42.0, 42.0)
        assert not vnum.EqualsExact(42.0, 42.1)

    def test_equals_int64(self) -> None:
        assert vnum.EqualsInt64(42, 42)
        assert not vnum.EqualsInt64(42, 43)

    def test_equals_big_decimal(self) -> None:
        a = Fraction(1, 3)
        b = Fraction(2, 6)
        assert vnum.EqualsBigDecimal(a, b)
        assert not vnum.EqualsBigDecimal(a, Fraction(1, 2))
        assert not vnum.EqualsBigDecimal(a, None)
        assert vnum.EqualsBigDecimal(None, None)

    def test_equals_char(self) -> None:
        assert vnum.EqualsChar("a", "A", True)
        assert not vnum.EqualsChar("a", "A", False)
        assert vnum.EqualsChar("a", "a", False)

    def test_min_max(self) -> None:
        assert vnum.Min(3, 1, 2) == 1
        assert vnum.Max(3, 1, 2) == 3
        assert vnum.Min() == 0
        assert vnum.Max() == 0

    def test_sum_avg(self) -> None:
        assert vnum.Sum(1, 2, 3) == 6
        assert vnum.Avg(2, 4, 6) == pytest.approx(4.0)
        assert vnum.Avg() == pytest.approx(0.0)

    def test_is_beside(self) -> None:
        assert vnum.IsBeside(5, 6)
        assert vnum.IsBeside(6, 5)
        assert not vnum.IsBeside(5, 7)


# ---------------------------------------------------------------------------
# factorial and combinatorics
# ---------------------------------------------------------------------------


class TestFactorial:
    def test_factorial(self) -> None:
        assert vnum.Factorial(0) == 1
        assert vnum.Factorial(1) == 1
        assert vnum.Factorial(5) == 120
        assert vnum.Factorial(10) == 3628800

    def test_factorial_negative(self) -> None:
        with pytest.raises(ValidationError):
            vnum.Factorial(-1)

    def test_factorial_range(self) -> None:
        assert vnum.FactorialRange(5, 3) == 20  # 5 * 4
        assert vnum.FactorialRange(5, 5) == 1
        assert vnum.FactorialRange(3, 5) == 0

    def test_factorial_big(self) -> None:
        assert vnum.FactorialBig(5) == 120
        assert vnum.FactorialBig(0) == 1
        assert vnum.FactorialBig(-1) == 1

    def test_factorial_big_range(self) -> None:
        assert vnum.FactorialBigRange(5, 3) == 20
        assert vnum.FactorialBigRange(3, 5) == 1

    def test_sqrt(self) -> None:
        assert vnum.Sqrt(16) == 4
        assert vnum.Sqrt(0) == 0

    def test_process_multiple(self) -> None:
        # C(5, 2) = 10
        assert vnum.ProcessMultiple(5, 2) == 10

    def test_divisor(self) -> None:
        assert vnum.Divisor(12, 8) == 4
        assert vnum.Divisor(7, 3) == 1

    def test_multiple(self) -> None:
        assert vnum.Multiple(4, 6) == 12
        assert vnum.Multiple(0, 5) == 0


# ---------------------------------------------------------------------------
# conversion
# ---------------------------------------------------------------------------


class TestConversion:
    def test_to_big_decimal(self) -> None:
        result = vnum.ToBigDecimal("0.5")
        assert result == Fraction(1, 2)

    def test_to_big_decimal_empty(self) -> None:
        result = vnum.ToBigDecimal("")
        assert result == Fraction(0, 1)

    def test_to_big_integer(self) -> None:
        assert vnum.ToBigInteger("42") == 42
        assert vnum.ToBigInteger("") == 0

    def test_count(self) -> None:
        assert vnum.Count(10, 3) == 4
        assert vnum.Count(0, 3) == 0
        assert vnum.Count(10, 0) == 0

    def test_null_to_zero(self) -> None:
        assert vnum.Null2Zero(None) == Fraction(0, 1)
        assert vnum.Null2Zero(Fraction(1, 2)) == Fraction(1, 2)

    def test_zero_to_one(self) -> None:
        assert vnum.Zero2One(0) == 1
        assert vnum.Zero2One(5) == 5

    def test_null_to_zero_int(self) -> None:
        assert vnum.NullToZero(5) == 5
        assert vnum.NullToZero(None) == 0

    def test_null_big_int_to_zero(self) -> None:
        assert vnum.NullBigIntToZero(None) == 0
        assert vnum.NullBigIntToZero(42) == 42

    def test_null_big_decimal_to_zero(self) -> None:
        assert vnum.NullBigDecimalToZero(None) == Fraction(0, 1)

    def test_new_big_integer(self) -> None:
        val, ok = vnum.NewBigInteger("42")
        assert ok and val == 42

        val, ok = vnum.NewBigInteger("0xFF")
        assert ok and val == 255

        val, ok = vnum.NewBigInteger("")
        assert not ok and val is None

    def test_part_value(self) -> None:
        assert vnum.PartValue(10, 3) == 4
        assert vnum.PartValue(9, 3) == 3

    def test_part_value_with_mode(self) -> None:
        assert vnum.PartValueWithMode(10, 3, True) == 4
        assert vnum.PartValueWithMode(10, 3, False) == 3
        assert vnum.PartValueWithMode(10, 0, True) == 0

    def test_to_double(self) -> None:
        assert vnum.ToDouble(42) == pytest.approx(42.0)
        assert vnum.ToDouble(3.14) == pytest.approx(3.14)
        assert vnum.ToDouble("abc") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# option contracts
# ---------------------------------------------------------------------------


class TestOptions:
    def test_with_parse_int_func(self) -> None:
        opt = vnum.WithParseIntFunc(lambda s: int(s) * 2)
        assert vnum.ParseInt("5", [opt]) == 10

    def test_with_parse_float_func(self) -> None:
        opt = vnum.WithParseFloatFunc(lambda s: float(s) * 2)
        assert vnum.ParseDouble("3.0", [opt]) == pytest.approx(6.0)

    def test_with_format_float_func(self) -> None:
        opt = vnum.WithFormatFloatFunc(lambda f: f"[{f}]")
        assert vnum.ToStr(3.14, [opt]) == "[3.14]"

    def test_with_random_reader(self) -> None:
        opt = vnum.WithRandomReader(lambda n: 0)  # always picks first
        result = vnum.GenRandomNumber(1, 10, 3, [opt])
        assert len(result) == 3
        assert all(1 <= x < 10 for x in result)