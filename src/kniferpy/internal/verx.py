from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

DEFAULT_VERSIONS_DELIMITER = ";"


@dataclass(slots=True, frozen=True)
class Token:
    number: bool
    num: str
    text: str


@dataclass(slots=True)
class ParsedVersion:
    sequence: list[Token] = field(default_factory=list)
    pre: list[Token] = field(default_factory=list)
    build: list[Token] = field(default_factory=list)


def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def _strcmp(a: str, b: str) -> int:
    return (a > b) - (a < b)


def _normalize_number(text: str) -> str:
    neg = text.startswith("-")
    if neg:
        text = text[1:]
    text = text.lstrip("0")
    if text == "":
        text = "0"
    if neg and text != "0":
        return "-" + text
    return text


def _take_number(s: str, i: int, acc: list[Token]) -> int:
    start = i
    while i < len(s) and _is_digit(s[i]):
        i += 1
    raw = _normalize_number(s[start:i])
    acc.append(Token(number=True, num=raw, text=raw))
    return i


def _take_string(s: str, i: int, acc: list[Token]) -> int:
    start = i
    while i < len(s):
        ch = s[i]
        if ch in ".-+" or _is_digit(ch):
            break
        i += 1
    acc.append(Token(number=False, num="", text=s[start:i]))
    return i


def _take_initial_token(s: str, i: int, acc: list[Token]) -> int:
    if _is_digit(s[i]):
        return _take_number(s, i, acc)
    # Preserve the original rule for leading non-digit tokens: the first
    # character is treated as its code point offset by '0'.
    value = str(ord(s[i]) - ord("0"))
    acc.append(Token(number=True, num=_normalize_number(value), text=value))
    return i + 1


def parse_version(v: str) -> ParsedVersion:
    parsed = ParsedVersion()
    n = len(v)
    if n == 0:
        return parsed
    i = 0
    c = v[i]
    i = _take_initial_token(v, i, parsed.sequence)
    while i < n:
        c = v[i]
        if c == ".":
            i += 1
            continue
        if c in "-+":
            i += 1
            break
        if _is_digit(c):
            i = _take_number(v, i, parsed.sequence)
        else:
            i = _take_string(v, i, parsed.sequence)
    if c == "-" and i >= n:
        return parsed
    while i < n:
        c = v[i]
        i = _take_number(v, i, parsed.pre) if _is_digit(c) else _take_string(v, i, parsed.pre)
        if i >= n:
            break
        c = v[i]
        if c in ".-":
            i += 1
            continue
        if c == "+":
            i += 1
            break
    if c == "+" and i >= n:
        return parsed
    while i < n:
        c = v[i]
        i = _take_number(v, i, parsed.build) if _is_digit(c) else _take_string(v, i, parsed.build)
        if i >= n:
            break
        c = v[i]
        if c in ".-+":
            i += 1
    return parsed


def _compare_number_string(a: str, b: str) -> int:
    a_neg = a.startswith("-")
    b_neg = b.startswith("-")
    if a_neg != b_neg:
        return -1 if a_neg else 1
    aa = a[1:] if a_neg else a
    bb = b[1:] if b_neg else b
    if len(aa) < len(bb):
        result = -1
    elif len(aa) > len(bb):
        result = 1
    else:
        result = _strcmp(aa, bb)
    return -result if a_neg else result


def _compare_tokens(ts1: list[Token], ts2: list[Token]) -> int:
    shared = min(len(ts1), len(ts2))
    for index in range(shared):
        o1, o2 = ts1[index], ts2[index]
        if o1.number and o2.number:
            cmp = _compare_number_string(o1.num, o2.num)
        else:
            cmp = _strcmp(o1.text, o2.text)
        if cmp != 0:
            return cmp
    rest = ts2 if len(ts2) > len(ts1) else ts1
    for index in range(shared, len(rest)):
        if rest[index].number and rest[index].num == "0":
            continue
        return len(ts1) - len(ts2)
    return 0


def _compare_parsed(v1: ParsedVersion, v2: ParsedVersion) -> int:
    cmp = _compare_tokens(v1.sequence, v2.sequence)
    if cmp != 0:
        return cmp
    if not v1.pre and v2.pre:
        return 1
    if v1.pre and not v2.pre:
        return -1
    cmp = _compare_tokens(v1.pre, v2.pre)
    if cmp != 0:
        return cmp
    return _compare_tokens(v1.build, v2.build)


def compare_version(version1: str, version2: str) -> int:
    return _compare_parsed(parse_version(version1), parse_version(version2))


def _compare_op_prefix(s: str) -> str:
    if s == "":
        return ""
    first = s[0]
    if first not in (">", "<", "\u2265", "\u2264"):
        return ""
    if len(s) > 1 and s[1] == "=":
        return s[:2]
    return first


def _valid_delimiter(delimiter: str) -> bool:
    return not (delimiter.strip() == "" or delimiter == "-" or _compare_op_prefix(delimiter) != "")


def _split_expression(expr: str, delimiter: str) -> list[str]:
    return [item.strip() for item in expr.split(delimiter) if item.strip() != ""]


def _compare_nullable(version1: str | None, version2: str | None) -> int:
    if version1 is None and version2 is None:
        return 0
    if version1 is None:
        return -1
    if version2 is None:
        return 1
    return compare_version(version1, version2)


def _match_one(current: str, expression: str) -> bool:
    op = _compare_op_prefix(expression)
    if op != "":
        ver = expression[len(op) :].strip()
        target = None if ver.lower() == "null" else ver
        cmp = _compare_nullable(current, target)
        if op in (">=", "\u2265", "\u2265="):
            return cmp >= 0
        if op in ("<=", "\u2264", "\u2264="):
            return cmp <= 0
        if op == ">":
            return cmp > 0
        if op == "<":
            return cmp < 0
        return False
    if "-" in expression:
        idx = expression.index("-")
        left = expression[:idx].strip()
        right = expression[idx + 1 :].strip()
        left_match = left == "" or compare_version(left, current) <= 0
        right_match = right == "" or compare_version(right, current) >= 0
        return left_match and right_match
    return current == expression


def match_el_with_delimiter(current_version: str, version_el: str, delimiter: str) -> bool:
    if not _valid_delimiter(delimiter):
        return False
    if version_el.strip() == "":
        return False
    trimmed = current_version.strip()
    parts = _split_expression(version_el, delimiter)
    if not parts:
        return False
    return any(_match_one(trimmed, el) for el in parts)


def match_el(current_version: str, version_el: str) -> bool:
    return match_el_with_delimiter(current_version, version_el, DEFAULT_VERSIONS_DELIMITER)


def any_match_slice(current_version: str, compare_versions: Sequence[str]) -> bool:
    joined = DEFAULT_VERSIONS_DELIMITER.join(compare_versions)
    return match_el(current_version, joined)


def any_match(current_version: str, *compare_versions: str) -> bool:
    return any_match_slice(current_version, compare_versions)


def is_greater_than(current_version: str, compare_version_str: str) -> bool:
    return match_el(current_version, ">" + compare_version_str)


def is_greater_than_or_equal(current_version: str, compare_version_str: str) -> bool:
    return match_el(current_version, ">=" + compare_version_str)


def is_less_than(current_version: str, compare_version_str: str) -> bool:
    return match_el(current_version, "<" + compare_version_str)


def is_less_than_or_equal(current_version: str, compare_version_str: str) -> bool:
    return match_el(current_version, "<=" + compare_version_str)


def match_el_with_delimiter_err(
    current_version: str, version_el: str, delimiter: str
) -> tuple[bool, str | None]:
    """Return (matched, error) tuple. Error is None on success."""
    if not _valid_delimiter(delimiter):
        return False, f"invalid delimiter: {delimiter!r}"
    if version_el.strip() == "":
        return False, None
    return match_el_with_delimiter(current_version, version_el, delimiter), None


def match_el_by_delimiter(current_version: str, version_el: str, delimiter: str) -> bool:
    return match_el_with_delimiter(current_version, version_el, delimiter)
