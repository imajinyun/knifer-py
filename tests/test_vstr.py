from __future__ import annotations

import pytest

from kniferpy import vstr

# ── BOM ──────────────────────────────────────────────────────────────────────


class TestBOM:
    def test_bom_constants(self) -> None:
        assert vstr.BOM_NONE == ""
        assert vstr.BOM_UTF8 == "UTF-8"

    def test_has_bom_utf8(self) -> None:
        assert vstr.has_bom(b"\xef\xbb\xbfhello") == vstr.BOM_UTF8

    def test_has_bom_none(self) -> None:
        assert vstr.has_bom(b"hello") == vstr.BOM_NONE

    def test_has_bom_utf16le(self) -> None:
        assert vstr.has_bom(b"\xff\xfehello") == vstr.BOM_UTF16_LE

    def test_strip_bom_utf8(self) -> None:
        assert vstr.strip_bom(b"\xef\xbb\xbfhello") == b"hello"

    def test_strip_bom_none(self) -> None:
        assert vstr.strip_bom(b"hello") == b"hello"


# ── Empty / Blank ────────────────────────────────────────────────────────────


class TestEmptyBlank:
    def test_is_empty(self) -> None:
        assert vstr.is_empty("")
        assert vstr.is_empty(None)
        assert not vstr.is_empty("a")

    def test_is_not_empty(self) -> None:
        assert vstr.is_not_empty("a")
        assert not vstr.is_not_empty("")
        assert not vstr.is_not_empty(None)

    def test_is_blank(self) -> None:
        assert vstr.is_blank("")
        assert vstr.is_blank("  \t\n")
        assert vstr.is_blank(None)
        assert not vstr.is_blank("a")

    def test_is_not_blank(self) -> None:
        assert vstr.is_not_blank("a")
        assert not vstr.is_not_blank("  ")
        assert not vstr.is_not_blank(None)

    def test_has_empty(self) -> None:
        assert vstr.has_empty("", "a")
        assert not vstr.has_empty("a", "b")

    def test_has_blank(self) -> None:
        assert vstr.has_blank("  ", "a")
        assert not vstr.has_blank("a", "b")

    def test_is_all_empty(self) -> None:
        assert vstr.is_all_empty("", "")
        assert not vstr.is_all_empty("a", "")

    def test_is_all_blank(self) -> None:
        assert vstr.is_all_blank("  ", "")
        assert not vstr.is_all_blank("a", "  ")


# ── Trim ─────────────────────────────────────────────────────────────────────


class TestTrim:
    def test_trim(self) -> None:
        assert vstr.trim("  hello  ") == "hello"
        assert vstr.trim(None) == ""

    def test_trim_to_empty(self) -> None:
        assert vstr.trim_to_empty("  hello  ") == "hello"
        assert vstr.trim_to_empty(None) == ""

    def test_trim_start(self) -> None:
        assert vstr.trim_start("  hello") == "hello"
        assert vstr.trim_start("hello") == "hello"

    def test_trim_end(self) -> None:
        assert vstr.trim_end("hello  ") == "hello"
        assert vstr.trim_end("hello") == "hello"


# ── Substring ────────────────────────────────────────────────────────────────


class TestSubstring:
    def test_sub(self) -> None:
        assert vstr.sub("hello", 0, 2) == "he"
        assert vstr.sub("hello", -2, 20) == "lo"
        assert vstr.sub("hello", 0, -1) == "hell"
        assert vstr.sub("", 0, 5) == ""
        assert vstr.sub("hello", 2, 2) == ""
        assert vstr.sub("hello", 3, 1) == "el"

    def test_sub_before(self) -> None:
        assert vstr.sub_before("a/b/c", "/") == "a"
        assert vstr.sub_before("a/b/c", "/", last=True) == "a/b"
        assert vstr.sub_before("hello", "") == "hello"
        assert vstr.sub_before("hello", "x") == "hello"

    def test_sub_after(self) -> None:
        assert vstr.sub_after("a/b/c", "/") == "b/c"
        assert vstr.sub_after("a/b/c", "/", last=True) == "c"
        assert vstr.sub_after("hello", "") == ""
        assert vstr.sub_after("hello", "x") == ""


# ── Split / Repeat / Pad ─────────────────────────────────────────────────────


class TestSplitRepeatPad:
    def test_split(self) -> None:
        assert vstr.split("a,b,c", ",") == ["a", "b", "c"]
        assert vstr.split("", ",") == []

    def test_split_trim(self) -> None:
        assert vstr.split_trim(" a, ,b ", ",") == ["a", "b"]

    def test_repeat(self) -> None:
        assert vstr.repeat("ab", 3) == "ababab"
        assert vstr.repeat("ab", 0) == ""
        assert vstr.repeat("ab", -1) == ""

    def test_pad_left(self) -> None:
        assert vstr.pad_left("ab", 5, "0") == "000ab"
        assert vstr.pad_left("abcde", 3, "0") == "abcde"

    def test_pad_right(self) -> None:
        assert vstr.pad_right("ab", 5, "0") == "ab000"
        assert vstr.pad_right("abcde", 3, "0") == "abcde"


# ── Contains / StartsWith / EndsWith ─────────────────────────────────────────


class TestContains:
    def test_contains(self) -> None:
        assert vstr.contains("hello", "el")
        assert not vstr.contains("hello", "xx")

    def test_contains_any(self) -> None:
        assert vstr.contains_any("hello", "el", "xx")
        assert not vstr.contains_any("hello", "xx", "yy")

    def test_contains_all(self) -> None:
        assert vstr.contains_all("hello", "he", "lo")
        assert not vstr.contains_all("hello", "he", "xx")

    def test_contains_ignore_case(self) -> None:
        assert vstr.contains_ignore_case("HELLO", "el")
        assert not vstr.contains_ignore_case("HELLO", "xx")

    def test_starts_with(self) -> None:
        assert vstr.starts_with("hello", "he")
        assert not vstr.starts_with("hello", "lo")

    def test_ends_with(self) -> None:
        assert vstr.ends_with("hello", "lo")
        assert not vstr.ends_with("hello", "he")

    def test_equals_ignore_case(self) -> None:
        assert vstr.equals_ignore_case("Hello", "HELLO")
        assert not vstr.equals_ignore_case("Hello", "World")


# ── Emoji ────────────────────────────────────────────────────────────────────


class TestEmoji:
    def test_contains_emoji(self) -> None:
        assert vstr.contains_emoji("hello 😀 world")
        assert not vstr.contains_emoji("hello world")

    def test_remove_emoji(self) -> None:
        assert vstr.remove_emoji("hello 😀 world") == "hello  world"

    def test_contains_emoji_with_options_matcher(self) -> None:
        assert vstr.contains_emoji_with_options("hello world", matcher=lambda s: True)
        assert not vstr.contains_emoji_with_options("hello", matcher=lambda s: False)

    def test_remove_emoji_with_options_replacer(self) -> None:
        result = vstr.remove_emoji_with_options(
            "hello 😀 world", replacer=lambda s: s.replace("😀", ":)")
        )
        assert result == "hello :) world"

    def test_emoji_helpers_default_option_paths(self) -> None:
        assert vstr.contains_emoji_with_options("hello 😀")
        assert vstr.remove_emoji_with_options("hello 😀") == "hello "


# ── Transform ────────────────────────────────────────────────────────────────


class TestTransform:
    def test_reverse(self) -> None:
        assert vstr.reverse("hello") == "olleh"
        assert vstr.reverse("") == ""

    def test_format(self) -> None:
        assert vstr.format("name={}, age={}", "tom", 12) == "name=tom, age=12"
        assert vstr.format("{}", "kniferpy") == "kniferpy"
        assert vstr.format("no placeholder") == "no placeholder"
        assert vstr.format("") == ""
        assert vstr.format(r"\{} {}", "x") == "{} x"
        assert vstr.format("{} {} {}", "a") == "a {} {}"

    def test_remove_prefix(self) -> None:
        assert vstr.remove_prefix("hello", "he") == "llo"
        assert vstr.remove_prefix("hello", "xx") == "hello"

    def test_remove_suffix(self) -> None:
        assert vstr.remove_suffix("hello", "lo") == "hel"
        assert vstr.remove_suffix("hello", "xx") == "hello"

    def test_add_prefix_if_not(self) -> None:
        assert vstr.add_prefix_if_not("hello", "he") == "hello"
        assert vstr.add_prefix_if_not("llo", "he") == "hello"

    def test_add_suffix_if_not(self) -> None:
        assert vstr.add_suffix_if_not("hello", "lo") == "hello"
        assert vstr.add_suffix_if_not("hel", "lo") == "hello"


# ── Length ───────────────────────────────────────────────────────────────────


class TestLength:
    def test_length(self) -> None:
        assert vstr.length("hello") == 5
        assert vstr.length("") == 0

    def test_rune_len(self) -> None:
        assert vstr.rune_len("hello") == 5
        assert vstr.rune_len("你好") == 2


# ── Default ──────────────────────────────────────────────────────────────────


class TestDefault:
    def test_default_if_empty(self) -> None:
        assert vstr.default_if_empty("", "fallback") == "fallback"
        assert vstr.default_if_empty(None, "fallback") == "fallback"
        assert vstr.default_if_empty("hello", "fallback") == "hello"

    def test_default_if_blank(self) -> None:
        assert vstr.default_if_blank("  ", "fallback") == "fallback"
        assert vstr.default_if_blank(None, "fallback") == "fallback"
        assert vstr.default_if_blank("hello", "fallback") == "hello"


# ── HTML ─────────────────────────────────────────────────────────────────────


class TestHTML:
    def test_escape_html(self) -> None:
        assert vstr.escape_html("<a>") == "&lt;a&gt;"
        assert vstr.escape_html('"hello"') == "&quot;hello&quot;"

    def test_unescape_html(self) -> None:
        assert vstr.unescape_html("&lt;a&gt;") == "<a>"


# ── Unicode Escape ───────────────────────────────────────────────────────────


class TestUnicodeEscape:
    def test_escape_unicode(self) -> None:
        assert vstr.escape_unicode("hello") == "hello"
        result = vstr.escape_unicode("你好")
        assert "\\u" in result
        assert vstr.escape_unicode("😀") == r"\uD83D\uDE00"

    def test_unescape_unicode(self) -> None:
        escaped = vstr.escape_unicode("你好")
        assert vstr.unescape_unicode(escaped) == "你好"
        assert vstr.unescape_unicode(r"\uD83D\uDE00") == "😀"
        assert vstr.unescape_unicode(r"\uZZZZ") == r"\uZZZZ"
        assert vstr.unescape_unicode(r"\uD83D\uZZZZ") == "\ud83d" + r"\uZZZZ"
        assert vstr.unescape_unicode(r"\uD83D\u0041") == "\ud83d" + "A"


# ── Case Conversion ──────────────────────────────────────────────────────────


class TestCaseConversion:
    def test_to_camel_case(self) -> None:
        assert vstr.to_camel_case("hello_world") == "helloWorld"
        assert vstr.to_camel_case("HelloWorld") == "helloWorld"
        assert vstr.to_camel_case("") == ""

    def test_to_pascal_case(self) -> None:
        assert vstr.to_pascal_case("hello_world") == "HelloWorld"
        assert vstr.to_pascal_case("helloWorld") == "HelloWorld"
        assert vstr.to_pascal_case("") == ""

    def test_to_snake_case(self) -> None:
        assert vstr.to_snake_case("HelloWorld") == "hello_world"
        assert vstr.to_snake_case("helloWorld") == "hello_world"
        assert vstr.to_snake_case("hello-world") == "hello_world"
        assert vstr.to_snake_case("") == ""

    def test_to_kebab_case(self) -> None:
        assert vstr.to_kebab_case("HelloWorld") == "hello-world"
        assert vstr.to_kebab_case("hello_world") == "hello-world"
        assert vstr.to_kebab_case("") == ""
        assert vstr.to_snake_case("HTTPServer2XX") == "http_server2_xx"


# ── Ant Path Matching ────────────────────────────────────────────────────────


class TestAntPath:
    def test_exact_match(self) -> None:
        assert vstr.ant_path_match("a/b/c", "a/b/c")

    def test_star_match(self) -> None:
        assert vstr.ant_path_match("a/*/c", "a/b/c")
        assert not vstr.ant_path_match("a/*/c", "a/b/d")

    def test_double_star(self) -> None:
        assert vstr.ant_path_match("a/**/c", "a/b/c")
        assert vstr.ant_path_match("a/**/c", "a/b/d/e/c")

    def test_question_mark(self) -> None:
        assert vstr.ant_path_match("a/?/c", "a/b/c")
        assert not vstr.ant_path_match("a/?/c", "a/bb/c")

    def test_custom_separator(self) -> None:
        assert vstr.ant_path_match_with_separator("a.*.c", "a.b.c", ".")

    def test_empty_separator_and_empty_segments(self) -> None:
        assert vstr.ant_path_match_with_separator("a/*", "a/b", "")
        assert vstr.ant_path_match("/", "/")
        assert vstr.ant_path_match("///", "/")
        assert not vstr.ant_path_match("", "a")
        assert not vstr.ant_path_match("a/**/c", "a/b/d")


# ── Text Similarity ──────────────────────────────────────────────────────────


class TestSimilarity:
    def test_jaccard_identical(self) -> None:
        assert vstr.jaccard_similarity("abc", "abc") == 1.0

    def test_jaccard_different(self) -> None:
        assert vstr.jaccard_similarity("abc", "def") == 0.0
        assert vstr.jaccard_similarity("", "") == 1.0
        assert vstr.jaccard_similarity("", "abc") == 0.0

    def test_ngram_similarity(self) -> None:
        assert vstr.ngram_similarity("abc", "abc", 2) == 1.0
        assert vstr.ngram_similarity("a", "a", 2) == 1.0
        assert vstr.ngram_similarity("", "", 2) == 1.0

    def test_ngram_invalid_n(self) -> None:
        assert vstr.ngram_similarity("abc", "abc", 0) == 0.0

    def test_levenshtein_distance(self) -> None:
        assert vstr.levenshtein_distance("kitten", "sitting") == 3
        assert vstr.levenshtein_distance("", "abc") == 3
        assert vstr.levenshtein_distance("abc", "") == 3
        assert vstr.levenshtein_distance("abc", "abc") == 0

    def test_levenshtein_similarity(self) -> None:
        assert vstr.levenshtein_similarity("abc", "abc") == 1.0
        assert vstr.levenshtein_similarity("", "") == 1.0

    def test_sim_hash(self) -> None:
        assert vstr.sim_hash("hello world") != 0
        assert vstr.sim_hash("") == 0

    def test_hamming_distance64(self) -> None:
        assert vstr.hamming_distance64(0, 0) == 0
        assert vstr.hamming_distance64(0xF, 0x0) == 4


# ── Character Predicates ─────────────────────────────────────────────────────


class TestCharPredicates:
    def test_is_blank_char(self) -> None:
        assert vstr.is_blank_char(" ")
        assert vstr.is_blank_char("\t")
        assert vstr.is_blank_char("\u00a0")
        assert not vstr.is_blank_char("a")
        assert not vstr.is_blank_char("ab")

    def test_is_letter(self) -> None:
        assert vstr.is_letter("a")
        assert vstr.is_letter("Z")
        assert not vstr.is_letter("1")
        assert not vstr.is_letter("ab")

    def test_is_digit(self) -> None:
        assert vstr.is_digit("1")
        assert vstr.is_digit("9")
        assert not vstr.is_digit("a")
        assert not vstr.is_digit("12")

    def test_is_ascii(self) -> None:
        assert vstr.is_ascii("a")
        assert vstr.is_ascii("~")
        assert not vstr.is_ascii("é")
        assert not vstr.is_ascii("你好")

    def test_is_letter_or_digit(self) -> None:
        assert vstr.is_letter_or_digit("a")
        assert vstr.is_letter_or_digit("1")
        assert not vstr.is_letter_or_digit("!")
        assert not vstr.is_letter_or_digit("ab")


# ── Charset ──────────────────────────────────────────────────────────────────


class TestCharset:
    def test_to_utf8_gbk(self) -> None:
        result = vstr.to_utf8("你好".encode("gbk"), "gbk")
        assert result == "你好".encode()

    def test_from_utf8_gbk(self) -> None:
        result = vstr.from_utf8("你好".encode(), "gbk")
        assert result == "你好".encode("gbk")

    def test_to_utf8_utf8_is_noop(self) -> None:
        data = b"hello"
        assert vstr.to_utf8(data, "utf-8") == data

    def test_from_utf8_utf8_is_noop(self) -> None:
        data = b"hello"
        assert vstr.from_utf8(data, "utf-8") == data

    def test_to_utf8_unsupported_raises(self) -> None:
        with pytest.raises(ValueError, match="unsupported"):
            vstr.to_utf8(b"hello", "unknown-charset")

    def test_from_utf8_unsupported_raises(self) -> None:
        with pytest.raises(ValueError, match="unsupported"):
            vstr.from_utf8(b"hello", "unknown-charset")

    def test_charset_aliases_bom_and_errors(self) -> None:
        assert vstr.to_utf8(b"\xef\xbb\xbfhello", "") == b"hello"
        assert vstr.to_utf8("é".encode("latin-1"), "latin 1") == "é".encode()
        with pytest.raises(ValueError):
            vstr.to_utf8(b"\xff", "gbk")
        with pytest.raises(ValueError):
            vstr.from_utf8("你好".encode(), "latin1")


# ── Legacy backward-compat tests ─────────────────────────────────────────────


class TestLegacy:
    def test_blank_and_defaults(self) -> None:
        assert vstr.is_empty("")
        assert vstr.is_blank(" \t\n")
        assert vstr.is_not_blank("kniferpy")
        assert vstr.default_if_empty("", "fallback") == "fallback"
        assert vstr.default_if_blank("  ", "fallback") == "fallback"

    def test_sub_split_and_contains(self) -> None:
        assert vstr.sub_before("a/b/c", "/", last=False) == "a"
        assert vstr.sub_before("a/b/c", "/", last=True) == "a/b"
        assert vstr.sub_after("a/b/c", "/", last=True) == "c"
        assert vstr.split_trim(" a, ,b ", ",") == ["a", "b"]
        assert vstr.contains_any("kniferpy", "py", "go")
        assert vstr.contains_all("kniferpy", "knife", "py")
        assert vstr.contains_ignore_case("KniferPy", "py")

    def test_case_and_html_helpers(self) -> None:
        assert vstr.to_snake_case("HelloWorld") == "hello_world"
        assert vstr.to_kebab_case("hello_world") == "hello-world"
        assert vstr.to_pascal_case("hello world") == "HelloWorld"
        assert vstr.escape_html("<a>") == "&lt;a&gt;"
        assert vstr.unescape_html("&lt;a&gt;") == "<a>"
