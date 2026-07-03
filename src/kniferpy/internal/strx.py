from __future__ import annotations

import codecs
import hashlib
import html
import re
from collections.abc import Callable

_EMOJI_PATTERN = re.compile(
    r"(?:[\U0001F1E6-\U0001F1FF]{2}"
    r"|[#*0-9]\uFE0F?\u20E3"
    r"|[\U0001F300-\U0001FAFF\u2600-\u27BF])"
    r"(?:\uFE0F|\u200D[\U0001F300-\U0001FAFF\u2600-\u27BF]\uFE0F?)*"
)

# ── BOM ──────────────────────────────────────────────────────────────────────

_BOM_PREFIXES: list[tuple[str, bytes]] = [
    ("UTF-32LE", codecs.BOM_UTF32_LE),
    ("UTF-32BE", codecs.BOM_UTF32_BE),
    ("UTF-8", codecs.BOM_UTF8),
    ("UTF-16LE", codecs.BOM_UTF16_LE),
    ("UTF-16BE", codecs.BOM_UTF16_BE),
]


def has_bom(data: bytes) -> str:
    for typ, prefix in _BOM_PREFIXES:
        if data.startswith(prefix):
            return typ
    return ""


def strip_bom(data: bytes) -> bytes:
    for _typ, prefix in _BOM_PREFIXES:
        if data.startswith(prefix):
            return data[len(prefix):]
    return data


# ── Charset ──────────────────────────────────────────────────────────────────

_CHARSET_MAP: dict[str, str | None] = {
    "": None,
    "utf8": None,
    "utf-8": None,
    "gbk": "gbk",
    "cp936": "gbk",
    "gb18030": "gb18030",
    "big5": "big5",
    "big-5": "big5",
    "shift-jis": "shift_jis",
    "shiftjis": "shift_jis",
    "sjis": "shift_jis",
    "cp932": "cp932",
    "euc-kr": "euc_kr",
    "euckr": "euc_kr",
    "iso-8859-1": "iso-8859-1",
    "latin1": "iso-8859-1",
    "latin-1": "iso-8859-1",
}


def _lookup_encoding(name: str) -> str | None:
    normalized = name.strip().lower().replace("_", "-").replace(" ", "")
    if normalized not in _CHARSET_MAP:
        raise ValueError(f"charset {name!r} is unsupported")
    return _CHARSET_MAP[normalized]


def to_utf8(data: bytes, from_charset: str) -> bytes:
    encoding = _lookup_encoding(from_charset)
    data = strip_bom(data)
    if encoding is None:
        return data
    try:
        return data.decode(encoding).encode("utf-8")
    except (UnicodeDecodeError, LookupError) as e:
        raise ValueError(f"charset decode failed: {e}") from e


def from_utf8(data: bytes, to_charset: str) -> bytes:
    encoding = _lookup_encoding(to_charset)
    if encoding is None:
        return data
    try:
        return data.decode("utf-8").encode(encoding)
    except (UnicodeEncodeError, LookupError) as e:
        raise ValueError(f"charset encode failed: {e}") from e


# ── Empty / Blank ────────────────────────────────────────────────────────────


def is_empty(value: str | None) -> bool:
    return value is None or value == ""


def is_not_empty(value: str | None) -> bool:
    return not is_empty(value)


def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def is_not_blank(value: str | None) -> bool:
    return not is_blank(value)


def has_empty(*strs: str) -> bool:
    return any(is_empty(s) for s in strs)


def has_blank(*strs: str) -> bool:
    return any(is_blank(s) for s in strs)


def is_all_empty(*strs: str) -> bool:
    return all(is_empty(s) for s in strs)


def is_all_blank(*strs: str) -> bool:
    return all(is_blank(s) for s in strs)


# ── Trim ─────────────────────────────────────────────────────────────────────


def trim(value: str | None) -> str:
    return "" if value is None else value.strip()


def trim_to_empty(value: str | None) -> str:
    return "" if value is None else value.strip()


def trim_start(value: str) -> str:
    return value.lstrip()


def trim_end(value: str) -> str:
    return value.rstrip()


# ── Substring ────────────────────────────────────────────────────────────────


def sub(value: str, from_index: int, to_index: int) -> str:
    chars = list(value)
    n = len(chars)
    if n == 0:
        return ""
    if from_index < 0:
        from_index += n
    if to_index < 0:
        to_index += n
    from_index = max(0, from_index)
    to_index = min(n, to_index)
    if from_index > to_index:
        from_index, to_index = to_index, from_index
    if from_index == to_index:
        return ""
    return "".join(chars[from_index:to_index])


def sub_before(value: str, separator: str, *, last: bool = False) -> str:
    if separator == "":
        return value
    index = value.rfind(separator) if last else value.find(separator)
    return value if index < 0 else value[:index]


def sub_after(value: str, separator: str, *, last: bool = False) -> str:
    if separator == "":
        return ""
    index = value.rfind(separator) if last else value.find(separator)
    return "" if index < 0 else value[index + len(separator):]


# ── Split / Repeat / Pad ─────────────────────────────────────────────────────


def split(value: str, separator: str) -> list[str]:
    if value == "":
        return []
    return value.split(separator)


def split_trim(value: str, separator: str) -> list[str]:
    return [part.strip() for part in value.split(separator) if part.strip()]


def repeat(value: str, n: int) -> str:
    return "" if n <= 0 else value * n


def pad_left(value: str, length: int, pad: str) -> str:
    if len(value) >= length:
        return value
    return pad * (length - len(value)) + value


def pad_right(value: str, length: int, pad: str) -> str:
    if len(value) >= length:
        return value
    return value + pad * (length - len(value))


# ── Contains / StartsWith / EndsWith ─────────────────────────────────────────


def contains(value: str, sub: str) -> bool:
    return sub in value


def contains_emoji(value: str) -> bool:
    return bool(_EMOJI_PATTERN.search(value))


def contains_emoji_with_options(
    value: str,
    matcher: Callable[[str], bool] | None = None,
    replacer: Callable[[str], str] | None = None,
) -> bool:
    if matcher is not None:
        return matcher(value)
    return bool(_EMOJI_PATTERN.search(value))


def remove_emoji(value: str) -> str:
    return _EMOJI_PATTERN.sub("", value)


def remove_emoji_with_options(
    value: str,
    matcher: Callable[[str], bool] | None = None,
    replacer: Callable[[str], str] | None = None,
) -> str:
    if replacer is not None:
        return replacer(value)
    return _EMOJI_PATTERN.sub("", value)


def contains_any(value: str, *items: str) -> bool:
    return any(item in value for item in items)


def contains_all(value: str, *items: str) -> bool:
    return all(item in value for item in items)


def contains_ignore_case(value: str, item: str) -> bool:
    return item.casefold() in value.casefold()


def starts_with(value: str, prefix: str) -> bool:
    return value.startswith(prefix)


def ends_with(value: str, suffix: str) -> bool:
    return value.endswith(suffix)


def equals_ignore_case(left: str, right: str) -> bool:
    return left.casefold() == right.casefold()


# ── Transform ────────────────────────────────────────────────────────────────


def reverse(value: str) -> str:
    return value[::-1]


def format(template: str, *args: object) -> str:  # noqa: A001
    if not template or not args:
        return template
    result: list[str] = []
    i = 0
    while i < len(template):
        c = template[i]
        if c == "\\" and i + 1 < len(template) and template[i + 1] == "{":
            result.append("{")
            i += 2
            continue
        if c == "{" and i + 1 < len(template) and template[i + 1] == "}":
            if args:
                result.append(str(args[0]))
                args = args[1:]
            else:
                result.append("{}")
            i += 2
            continue
        result.append(c)
        i += 1
    return "".join(result)


def remove_prefix(value: str, prefix: str) -> str:
    if value.startswith(prefix):
        return value[len(prefix):]
    return value


def remove_suffix(value: str, suffix: str) -> str:
    if value.endswith(suffix):
        return value[:-len(suffix)]
    return value


def add_prefix_if_not(value: str, prefix: str) -> str:
    return value if value.startswith(prefix) else f"{prefix}{value}"


def add_suffix_if_not(value: str, suffix: str) -> str:
    return value if value.endswith(suffix) else f"{value}{suffix}"


# ── Length ───────────────────────────────────────────────────────────────────


def length(value: str) -> int:
    return len(value)


def rune_len(value: str) -> int:
    return len(value)


# ── Default ──────────────────────────────────────────────────────────────────


def default_if_empty(value: str | None, default: str) -> str:
    return default if value is None or value == "" else value


def default_if_blank(value: str | None, default: str) -> str:
    return default if value is None or value.strip() == "" else value


# ── HTML ─────────────────────────────────────────────────────────────────────


def escape_html(value: str) -> str:
    return html.escape(value, quote=True)


def unescape_html(value: str) -> str:
    return html.unescape(value)


# ── Unicode Escape ───────────────────────────────────────────────────────────


def escape_unicode(value: str) -> str:
    result: list[str] = []
    for ch in value:
        cp = ord(ch)
        if cp < 128:
            result.append(ch)
        elif cp <= 0xFFFF:
            result.append(f"\\u{cp:04X}")
        else:
            # surrogate pair
            high = 0xD800 + ((cp - 0x10000) >> 10)
            low = 0xDC00 + ((cp - 0x10000) & 0x3FF)
            result.append(f"\\u{high:04X}\\u{low:04X}")
    return "".join(result)


def unescape_unicode(value: str) -> str:
    result: list[str] = []
    i = 0
    while i < len(value):
        if i + 6 > len(value) or value[i] != "\\" or value[i + 1] != "u":
            result.append(value[i])
            i += 1
            continue
        try:
            hi = int(value[i + 2 : i + 6], 16)
        except ValueError:
            result.append(value[i])
            i += 1
            continue
        i += 6
        if (
            0xD800 <= hi <= 0xDBFF
            and i + 6 <= len(value)
            and value[i] == "\\"
            and value[i + 1] == "u"
        ):
            try:
                lo = int(value[i + 2 : i + 6], 16)
            except ValueError:
                result.append(chr(hi))
                continue
            if 0xDC00 <= lo <= 0xDFFF:
                cp = 0x10000 + ((hi - 0xD800) << 10) + (lo - 0xDC00)
                result.append(chr(cp))
                i += 6
                continue
        result.append(chr(hi))
    return "".join(result)


# ── Case Conversion ──────────────────────────────────────────────────────────


def to_camel_case(value: str) -> str:
    if value == "":
        return value
    if not any(c in value for c in "_- "):
        return value[0].lower() + value[1:]
    result: list[str] = []
    upper = False
    first = True
    for ch in value:
        if ch in "_- ":
            upper = True
            continue
        if first:
            result.append(ch.lower())
            first = False
            continue
        if upper:
            result.append(ch.upper())
            upper = False
        else:
            result.append(ch.lower())
    return "".join(result)


def to_pascal_case(value: str) -> str:
    if value == "":
        return value
    c = to_camel_case(value)
    return c[0].upper() + c[1:] if c else ""


def to_snake_case(value: str) -> str:
    return _to_separated(value, "_")


def to_kebab_case(value: str) -> str:
    return _to_separated(value, "-")


def _to_separated(value: str, sep: str) -> str:
    if value == "":
        return value
    result: list[str] = []
    chars = list(value)
    for i, ch in enumerate(chars):
        if ch in "_- ":
            result.append(sep)
            continue
        if ch.isupper():
            if i > 0:
                prev = chars[i - 1]
                prev_is_lower = prev.islower() or prev.isdigit()
                next_is_lower = i + 1 < len(chars) and chars[i + 1].islower()
                if prev_is_lower or (prev.isupper() and next_is_lower):
                    result.append(sep)
            result.append(ch.lower())
        else:
            result.append(ch)
    return "".join(result)


# ── Ant Path Matching ────────────────────────────────────────────────────────


def ant_path_match(pattern: str, path: str) -> bool:
    return ant_path_match_with_separator(pattern, path, "/")


def ant_path_match_with_separator(pattern: str, path: str, separator: str) -> bool:
    if separator == "":
        separator = "/"
    if pattern == path:
        return True
    pattern_segments = _split_path_segments(pattern, separator)
    path_segments = _split_path_segments(path, separator)
    return _match_ant_segments(pattern_segments, path_segments, 0, 0)


def _split_path_segments(value: str, separator: str) -> list[str]:
    if value == "":
        return []
    trimmed = value.strip(separator)
    if trimmed == "":
        return []
    return trimmed.split(separator)


def _match_ant_segments(
    pattern: list[str], path: list[str], pi: int, si: int
) -> bool:
    if pi == len(pattern):
        return si == len(path)
    if pattern[pi] == "**":
        for next_idx in range(si, len(path) + 1):
            if _match_ant_segments(pattern, path, pi + 1, next_idx):
                return True
        return False
    if si == len(path):
        return False
    return _match_ant_segment(pattern[pi], path[si]) and _match_ant_segments(
        pattern, path, pi + 1, si + 1
    )


def _match_ant_segment(pattern: str, text: str) -> bool:
    pr = list(pattern)
    tr = list(text)
    dp = [[False] * (len(tr) + 1) for _ in range(len(pr) + 1)]
    dp[0][0] = True
    for i in range(1, len(pr) + 1):
        if pr[i - 1] == "*":
            dp[i][0] = dp[i - 1][0]
    for i in range(1, len(pr) + 1):
        for j in range(1, len(tr) + 1):
            if pr[i - 1] == "*":
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif pr[i - 1] == "?":
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = pr[i - 1] == tr[j - 1] and dp[i - 1][j - 1]
    return dp[len(pr)][len(tr)]


# ── Text Similarity ──────────────────────────────────────────────────────────


def _rune_set(value: str) -> set[str]:
    return {ch for ch in value if not ch.isspace()}


def _effective_runes(value: str) -> list[str]:
    return [ch for ch in value if not ch.isspace()]


def _ngram_set(value: str, n: int) -> set[str]:
    runes = _effective_runes(value)
    if not runes:
        return set()
    if len(runes) < n:
        return {"".join(runes)}
    return {"".join(runes[i : i + n]) for i in range(len(runes) - n + 1)}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    union = len(left | right)
    return intersection / union


def jaccard_similarity(a: str, b: str) -> float:
    return _jaccard(_rune_set(a), _rune_set(b))


def ngram_similarity(a: str, b: str, n: int) -> float:
    if n <= 0:
        return 0.0
    return _jaccard(_ngram_set(a, n), _ngram_set(b, n))


def levenshtein_distance(a: str, b: str) -> int:
    left = list(a)
    right = list(b)
    if not left:
        return len(right)
    if not right:
        return len(left)
    prev = list(range(len(right) + 1))
    curr = [0] * (len(right) + 1)
    for i, lr in enumerate(left):
        curr[0] = i + 1
        for j, rr in enumerate(right):
            cost = 0 if lr == rr else 1
            curr[j + 1] = min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost)
        prev, curr = curr, prev
    return prev[len(right)]


def levenshtein_similarity(a: str, b: str) -> float:
    left_len = len(a)
    right_len = len(b)
    max_len = max(left_len, right_len)
    if max_len == 0:
        return 1.0
    distance = levenshtein_distance(a, b)
    return 1.0 - distance / max_len


def sim_hash(text: str) -> int:
    tokens = _sim_hash_tokens(text)
    if not tokens:
        return 0
    vector = [0] * 64
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest()[:16], 16)
        for i in range(64):
            if h & (1 << i):
                vector[i] += 1
            else:
                vector[i] -= 1
    result = 0
    for i, weight in enumerate(vector):
        if weight > 0:
            result |= 1 << i
    return result & 0xFFFFFFFFFFFFFFFF


def _sim_hash_tokens(text: str) -> list[str]:
    fields = text.lower().split()
    if fields:
        return fields
    return [ch for ch in text.lower() if not ch.isspace()]


def hamming_distance64(a: int, b: int) -> int:
    return (a ^ b).bit_count()


# ── Character Predicates ─────────────────────────────────────────────────────


def is_blank_char(ch: str) -> bool:
    if len(ch) != 1:
        return False
    cp = ord(ch)
    return ch.isspace() or cp in (0x00A0, 0x2007, 0x202F, 0xFEFF)


def is_letter(ch: str) -> bool:
    if len(ch) != 1:
        return False
    return ch.isalpha()


def is_digit(ch: str) -> bool:
    if len(ch) != 1:
        return False
    return ch.isdigit()


def is_ascii(ch: str) -> bool:
    if len(ch) != 1:
        return False
    return ord(ch) < 128


def is_letter_or_digit(ch: str) -> bool:
    if len(ch) != 1:
        return False
    return ch.isalpha() or ch.isdigit()