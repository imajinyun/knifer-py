from kniferpy import vstr


def test_blank_and_defaults() -> None:
    assert vstr.is_empty("")
    assert vstr.is_blank(" \t\n")
    assert vstr.is_not_blank("kniferpy")
    assert vstr.default_if_empty("", "fallback") == "fallback"
    assert vstr.default_if_blank("  ", "fallback") == "fallback"


def test_sub_split_and_contains() -> None:
    assert vstr.sub_before("a/b/c", "/", last=False) == "a"
    assert vstr.sub_before("a/b/c", "/", last=True) == "a/b"
    assert vstr.sub_after("a/b/c", "/", last=True) == "c"
    assert vstr.split_trim(" a, ,b ", ",") == ["a", "b"]
    assert vstr.contains_any("kniferpy", "py", "go")
    assert vstr.contains_all("kniferpy", "knife", "py")
    assert vstr.contains_ignore_case("KniferPy", "py")


def test_case_and_html_helpers() -> None:
    assert vstr.to_snake_case("HelloWorld") == "hello_world"
    assert vstr.to_kebab_case("hello_world") == "hello-world"
    assert vstr.to_pascal_case("hello world") == "HelloWorld"
    assert vstr.escape_html("<a>") == "&lt;a&gt;"
    assert vstr.unescape_html("&lt;a&gt;") == "<a>"
