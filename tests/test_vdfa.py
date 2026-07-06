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


def test_word_tree_empty_word_and_empty_text_edges() -> None:
    tree = vdfa.new_word_tree()
    tree.add_word(" - ")
    assert tree.is_empty()
    assert tree.match_all_words("") == []


def test_set_char_filter_none_keeps_existing_filter() -> None:
    tree = vdfa.new_word_tree(char_filter=lambda _c: True)
    assert tree.set_char_filter(None) is tree
    tree.add_word("bad")
    assert not tree.is_match("b-a-d")


def test_package_aliases_and_filter_mode() -> None:
    vdfa.init(["ab", "abc"])

    assert vdfa.contains_any("abc")
    assert vdfa.contains_any_with_options("abc")
    assert vdfa.get_found_first_any("abc").word == "ab"
    assert vdfa.get_found_first_any_with_options("abc").word == "ab"
    assert [w.word for w in vdfa.get_found_all_any("abc")] == ["ab"]
    assert [w.word for w in vdfa.get_found_all_any_with_options("abc")] == ["ab"]
    assert [w.word for w in vdfa.get_found_all_with_options("abc")] == ["ab"]
    assert [w.word for w in vdfa.get_found_all_mode_with_options("abc", True, True)] == [
        "ab",
        "abc",
    ]
    assert vdfa.filter_any("abc") == "***"
    assert vdfa.filter_any_with_options("abc") == "***"
    assert vdfa.filter_with_options("abc") == "***"
    assert vdfa.filter_mode("", True, True) == ""
    assert vdfa.filter_mode("none", True, True) == "none"
    assert vdfa.filter_mode("abc", True, True, lambda word: f"[{word.word}]") == "[abc]"
    assert vdfa.filter_mode_with_options("abc", True, False) == "**c"
    assert vdfa.new_word_tree_with_options().is_empty()
    vdfa.init_with_options(["bad"])
    assert vdfa.contains("bad")
    vdfa.init_string_with_options("bad|evil", "|")
    assert vdfa.contains("evil")


def test_async_runner_init_and_reset() -> None:
    calls: list[str] = []

    def runner(fn):
        calls.append("run")
        fn()

    vdfa.configure_async_runner(runner)
    vdfa.init_async(["async"])
    assert calls == ["run"]
    assert vdfa.contains("async")
    vdfa.init_string_async("later|soon", "|")
    assert calls == ["run", "run"]
    assert vdfa.contains("soon")
    vdfa.init_string_async_with_options("x,y")
    assert calls == ["run", "run", "run"]
    assert vdfa.contains("x")
    vdfa.reset_async_runner()
    vdfa.configure_async_runner(None)
