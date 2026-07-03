from __future__ import annotations

from collections.abc import Callable

from kniferpy.internal import strx

# ── BOM ──────────────────────────────────────────────────────────────────────

BOM_NONE = ""
BOM_UTF8 = "UTF-8"
BOM_UTF16_LE = "UTF-16LE"
BOM_UTF16_BE = "UTF-16BE"
BOM_UTF32_LE = "UTF-32LE"
BOM_UTF32_BE = "UTF-32BE"


def has_bom(data: bytes) -> str:
    return strx.has_bom(data)


def strip_bom(data: bytes) -> bytes:
    return strx.strip_bom(data)


# ── Charset ──────────────────────────────────────────────────────────────────


def to_utf8(data: bytes, from_charset: str) -> bytes:
    return strx.to_utf8(data, from_charset)


def from_utf8(data: bytes, to_charset: str) -> bytes:
    return strx.from_utf8(data, to_charset)


# ── Empty / Blank ────────────────────────────────────────────────────────────


def is_empty(value: str | None) -> bool:
    return strx.is_empty(value)


def is_not_empty(value: str | None) -> bool:
    return strx.is_not_empty(value)


def is_blank(value: str | None) -> bool:
    return strx.is_blank(value)


def is_not_blank(value: str | None) -> bool:
    return strx.is_not_blank(value)


def has_empty(*strs: str) -> bool:
    return strx.has_empty(*strs)


def has_blank(*strs: str) -> bool:
    return strx.has_blank(*strs)


def is_all_empty(*strs: str) -> bool:
    return strx.is_all_empty(*strs)


def is_all_blank(*strs: str) -> bool:
    return strx.is_all_blank(*strs)


# ── Trim ─────────────────────────────────────────────────────────────────────


def trim(value: str | None) -> str:
    return strx.trim(value)


def trim_to_empty(value: str | None) -> str:
    return strx.trim_to_empty(value)


def trim_start(value: str) -> str:
    return strx.trim_start(value)


def trim_end(value: str) -> str:
    return strx.trim_end(value)


# ── Substring ────────────────────────────────────────────────────────────────


def sub(value: str, from_index: int, to_index: int) -> str:
    return strx.sub(value, from_index, to_index)


def sub_before(value: str, separator: str, *, last: bool = False) -> str:
    return strx.sub_before(value, separator, last=last)


def sub_after(value: str, separator: str, *, last: bool = False) -> str:
    return strx.sub_after(value, separator, last=last)


# ── Split / Repeat / Pad ─────────────────────────────────────────────────────


def split(value: str, separator: str) -> list[str]:
    return strx.split(value, separator)


def split_trim(value: str, separator: str) -> list[str]:
    return strx.split_trim(value, separator)


def repeat(value: str, n: int) -> str:
    return strx.repeat(value, n)


def pad_left(value: str, length: int, pad: str) -> str:
    return strx.pad_left(value, length, pad)


def pad_right(value: str, length: int, pad: str) -> str:
    return strx.pad_right(value, length, pad)


# ── Contains / StartsWith / EndsWith ─────────────────────────────────────────


def contains(value: str, sub: str) -> bool:
    return strx.contains(value, sub)


def contains_emoji(value: str) -> bool:
    return strx.contains_emoji(value)


def contains_emoji_with_options(
    value: str,
    matcher: Callable[[str], bool] | None = None,
    replacer: Callable[[str], str] | None = None,
) -> bool:
    return strx.contains_emoji_with_options(value, matcher=matcher, replacer=replacer)


def remove_emoji(value: str) -> str:
    return strx.remove_emoji(value)


def remove_emoji_with_options(
    value: str,
    matcher: Callable[[str], bool] | None = None,
    replacer: Callable[[str], str] | None = None,
) -> str:
    return strx.remove_emoji_with_options(value, matcher=matcher, replacer=replacer)


def contains_any(value: str, *items: str) -> bool:
    return strx.contains_any(value, *items)


def contains_all(value: str, *items: str) -> bool:
    return strx.contains_all(value, *items)


def contains_ignore_case(value: str, item: str) -> bool:
    return strx.contains_ignore_case(value, item)


def starts_with(value: str, prefix: str) -> bool:
    return strx.starts_with(value, prefix)


def ends_with(value: str, suffix: str) -> bool:
    return strx.ends_with(value, suffix)


def equals_ignore_case(left: str, right: str) -> bool:
    return strx.equals_ignore_case(left, right)


# ── Transform ────────────────────────────────────────────────────────────────


def reverse(value: str) -> str:
    return strx.reverse(value)


def format(template: str, *args: object) -> str:
    return strx.format(template, *args)


def remove_prefix(value: str, prefix: str) -> str:
    return strx.remove_prefix(value, prefix)


def remove_suffix(value: str, suffix: str) -> str:
    return strx.remove_suffix(value, suffix)


def add_prefix_if_not(value: str, prefix: str) -> str:
    return strx.add_prefix_if_not(value, prefix)


def add_suffix_if_not(value: str, suffix: str) -> str:
    return strx.add_suffix_if_not(value, suffix)


# ── Length ───────────────────────────────────────────────────────────────────


def length(value: str) -> int:
    return strx.length(value)


def rune_len(value: str) -> int:
    return strx.rune_len(value)


# ── Default ──────────────────────────────────────────────────────────────────


def default_if_empty(value: str | None, default: str) -> str:
    return strx.default_if_empty(value, default)


def default_if_blank(value: str | None, default: str) -> str:
    return strx.default_if_blank(value, default)


# ── HTML ─────────────────────────────────────────────────────────────────────


def escape_html(value: str) -> str:
    return strx.escape_html(value)


def unescape_html(value: str) -> str:
    return strx.unescape_html(value)


# ── Unicode Escape ───────────────────────────────────────────────────────────


def escape_unicode(value: str) -> str:
    return strx.escape_unicode(value)


def unescape_unicode(value: str) -> str:
    return strx.unescape_unicode(value)


# ── Case Conversion ──────────────────────────────────────────────────────────


def to_camel_case(value: str) -> str:
    return strx.to_camel_case(value)


def to_pascal_case(value: str) -> str:
    return strx.to_pascal_case(value)


def to_snake_case(value: str) -> str:
    return strx.to_snake_case(value)


def to_kebab_case(value: str) -> str:
    return strx.to_kebab_case(value)


# ── Ant Path Matching ────────────────────────────────────────────────────────


def ant_path_match(pattern: str, path: str) -> bool:
    return strx.ant_path_match(pattern, path)


def ant_path_match_with_separator(pattern: str, path: str, separator: str) -> bool:
    return strx.ant_path_match_with_separator(pattern, path, separator)


# ── Text Similarity ──────────────────────────────────────────────────────────


def jaccard_similarity(a: str, b: str) -> float:
    return strx.jaccard_similarity(a, b)


def ngram_similarity(a: str, b: str, n: int) -> float:
    return strx.ngram_similarity(a, b, n)


def levenshtein_distance(a: str, b: str) -> int:
    return strx.levenshtein_distance(a, b)


def levenshtein_similarity(a: str, b: str) -> float:
    return strx.levenshtein_similarity(a, b)


def sim_hash(text: str) -> int:
    return strx.sim_hash(text)


def hamming_distance64(a: int, b: int) -> int:
    return strx.hamming_distance64(a, b)


# ── Character Predicates ─────────────────────────────────────────────────────


def is_blank_char(ch: str) -> bool:
    return strx.is_blank_char(ch)


def is_letter(ch: str) -> bool:
    return strx.is_letter(ch)


def is_digit(ch: str) -> bool:
    return strx.is_digit(ch)


def is_ascii(ch: str) -> bool:
    return strx.is_ascii(ch)


def is_letter_or_digit(ch: str) -> bool:
    return strx.is_letter_or_digit(ch)