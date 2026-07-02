from __future__ import annotations

from kniferpy import vdfa


def test_add_word_and_is_match() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("bad", "worse")
    assert tree.is_match("this is bad") is True
    assert tree.is_match("all fine") is False


def test_stop_chars_are_ignored_between_runes() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("bad")
    # Punctuation between characters must not defeat the match.
    found = tree.match_word("b-a-d word")
    assert found is not None
    assert found.word == "bad"
    assert found.found_word == "b-a-d"
    assert found.start == 0
    assert found.end == 4


def test_match_returns_first_text() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("cat", "dog")
    assert tree.match("a dog and a cat") == "dog"
    assert tree.match("nothing here") is None


def test_match_word_none_when_absent() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("secret")
    assert tree.match_word("no match") is None


def test_match_all_non_dense_skips_past_match() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("ab", "abc")
    # Non-dense: after matching "ab" the scan resumes past it.
    assert tree.match_all("abc") == ["ab"]


def test_match_all_mode_dense_non_greedy() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("ab", "abc")
    # Dense + non-greedy stops at the shortest match per start position.
    assert tree.match_all_mode("abc", -1, True, False) == ["ab"]


def test_match_all_mode_dense_greedy() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("ab", "abc")
    # Dense + greedy reports every prefix match starting at a position.
    assert tree.match_all_mode("abc", -1, True, True) == ["ab", "abc"]


def test_match_all_limit() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("a")
    assert tree.match_all_limit("aaaa", 2) == ["a", "a"]


def test_match_all_words_metadata() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("cat", "dog")
    words = tree.match_all_words("cat dog")
    assert [w.word for w in words] == ["cat", "dog"]
    assert words[0].start == 0
    assert words[0].end == 2
    assert words[1].start == 4
    assert words[1].end == 6


def test_found_word_str() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("bad")
    found = tree.match_word("bad")
    assert found is not None
    assert str(found) == "bad"


def test_filter_default_mask() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("bad", "evil")
    assert tree.filter("bad and evil") == "*** and ****"


def test_filter_masks_embedded_stop_chars() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("bad")
    # The matched span includes the interior separators, so all are masked.
    assert tree.filter("b.a.d") == "*****"


def test_filter_custom_processor() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("bad")
    assert tree.filter("a bad word", processor=lambda w: "[X]") == "a [X] word"


def test_filter_no_match_returns_original() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("bad")
    assert tree.filter("all clear") == "all clear"


def test_filter_empty_text() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word("bad")
    assert tree.filter("") == ""


def test_clear_and_is_empty() -> None:
    tree = vdfa.new_word_tree()
    assert tree.is_empty() is True
    tree.add_word("bad")
    assert tree.is_empty() is False
    tree.clear()
    assert tree.is_empty() is True


def test_add_words_dedup() -> None:
    tree = vdfa.new_word_tree()
    tree.add_words("bad", "bad", "bad")
    assert tree.match_all("bad bad") == ["bad", "bad"]


def test_custom_char_filter_disables_stop_skipping() -> None:
    # A filter that accepts everything makes separators significant again.
    tree = vdfa.new_word_tree(char_filter=lambda _c: True)
    tree.add_word("bad")
    assert tree.is_match("b-a-d") is False
    assert tree.is_match("bad") is True


def test_set_char_filter_returns_self() -> None:
    tree = vdfa.new_word_tree()
    assert tree.set_char_filter(lambda _c: True) is tree


def test_is_stop_char_helpers() -> None:
    assert vdfa.is_stop_char(" ") is True
    assert vdfa.is_stop_char("-") is True
    assert vdfa.is_stop_char("a") is False
    assert vdfa.is_not_stop_char("a") is True
    assert vdfa.is_not_stop_char("-") is False


def test_default_processor() -> None:
    word = vdfa.FoundWord(word="bad", found_word="b-a-d", start=0, end=4)
    assert vdfa.default_processor(word) == "*****"


def test_package_matcher_init_and_contains() -> None:
    vdfa.init(["bad", "worse"])
    assert vdfa.is_inited() is True
    assert vdfa.contains("that is bad") is True
    assert vdfa.contains("all good") is False


def test_package_matcher_init_string() -> None:
    vdfa.init_string("bad, worse , evil")
    assert vdfa.contains("evil") is True
    assert vdfa.contains("worse") is True


def test_package_matcher_init_string_custom_separator() -> None:
    vdfa.init_string("bad|evil", "|")
    assert vdfa.contains("bad") is True
    assert vdfa.contains("evil") is True


def test_package_matcher_get_found_first_and_all() -> None:
    vdfa.init(["cat", "dog"])
    first = vdfa.get_found_first("a dog and a cat")
    assert first is not None
    assert first.word == "dog"
    assert [w.word for w in vdfa.get_found_all("cat dog")] == ["cat", "dog"]


def test_package_matcher_get_found_all_mode() -> None:
    vdfa.init(["ab", "abc"])
    words = vdfa.get_found_all_mode("abc", True, True)
    assert [w.word for w in words] == ["ab", "abc"]


def test_package_matcher_filter() -> None:
    vdfa.init(["bad"])
    assert vdfa.filter("a bad word") == "a *** word"


def test_package_matcher_set_char_filter() -> None:
    vdfa.init(["bad"])
    vdfa.set_char_filter(lambda _c: True)
    assert vdfa.contains("b-a-d") is False
    # Restore the default so later tests keep the standard behaviour.
    vdfa.set_char_filter(vdfa.is_not_stop_char)
