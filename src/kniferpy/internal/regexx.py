from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

# Chinese character constants
RE_CHINESE = r"\p{Han}"
RE_CHINESES = r"^\p{Han}+$"

_numbers_regex = re.compile(r"\d+")
_group_var_regexp = re.compile(r"\$(\d+)")


@dataclass
class MatchResult:
    """Describes a single regular-expression match."""

    text: str = ""
    start: int = 0
    end: int = 0
    groups: list[str] = field(default_factory=list)
    group_names: dict[str, str] = field(default_factory=dict)


def _try_compile(pattern: str) -> re.Pattern[str] | None:
    try:
        return re.compile(pattern)
    except re.error:
        return None


def _build_match_result(
    regex: re.Pattern[str], content: str, loc: tuple[int, int]
) -> MatchResult:
    """Build a MatchResult from a compiled regex and a (start, end) span."""
    # Find the full match with subgroups
    m = regex.search(content, loc[0], loc[1])
    if m is None:
        return MatchResult(text=content[loc[0] : loc[1]], start=loc[0], end=loc[1])
    groups = [m.group(i) or "" for i in range(len(m.groups()) + 1)]
    group_names: dict[str, str] = {}
    for name, value in m.groupdict().items():
        group_names[name] = value or ""
    return MatchResult(
        text=m.group(0) or "",
        start=m.start(0),
        end=m.end(0),
        groups=groups,
        group_names=group_names,
    )


# ========== Match / Find ==========


def match(pattern: str, text: str) -> bool:
    compiled = _try_compile(pattern)
    return compiled is not None and compiled.search(text) is not None


def is_match(pattern: str, text: str) -> bool:
    if pattern == "":
        return text != ""
    compiled = _try_compile(pattern)
    if compiled is None:
        return False
    m = compiled.search(text)
    return m is not None and m.start() == 0 and m.end() == len(text)


def find(pattern: str, text: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    found = compiled.search(text)
    return found.group(0) if found else ""


def find_all(pattern: str, text: str) -> list[str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return []
    return [m.group(0) for m in compiled.finditer(text)]


def count(pattern: str, text: str) -> int:
    compiled = _try_compile(pattern)
    if compiled is None:
        return 0
    return sum(1 for _ in compiled.finditer(text))


def replace(pattern: str, text: str, replacement: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return compiled.sub(lambda _: replacement, text)


def replace_first(pattern: str, text: str, replacement: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return compiled.sub(lambda _: replacement, text, count=1)


def replace_func(
    pattern: str, text: str, repl: Callable[[re.Match[str]], str]
) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return compiled.sub(repl, text)


def delete_all(pattern: str, text: str) -> str:
    return replace(pattern, text, "")


def delete_first(pattern: str, text: str) -> str:
    return replace_first(pattern, text, "")


# ========== Capture Groups ==========


def get_group(pattern: str, text: str, group: int = 0) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    found = compiled.search(text)
    if found is None:
        return ""
    try:
        value = found.group(group)
    except IndexError:
        return ""
    return value or ""


def get_group_by_name(pattern: str, text: str, name: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    found = compiled.search(text)
    if found is None:
        return ""
    try:
        value = found.group(name)
    except IndexError:
        return ""
    return value or ""


def find_all_group(pattern: str, text: str, group: int = 1) -> list[str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return []
    result: list[str] = []
    for match_obj in compiled.finditer(text):
        try:
            value = match_obj.group(group)
        except IndexError:
            continue
        if value is not None:
            result.append(value)
    return result


def named_groups(pattern: str, text: str) -> dict[str, str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return {}
    found = compiled.search(text)
    if found is None:
        return {}
    return {key: value or "" for key, value in found.groupdict().items()}


def get_first_number(text: str) -> int | None:
    found = _numbers_regex.search(text)
    if found is None:
        return None
    return int(found.group(0))


def escape(text: str) -> str:
    return re.escape(text)


# ========== New: GetGroup0 / GetGroup1 ==========


def get_group0(pattern: str, text: str) -> str:
    return get_group(pattern, text, 0)


def get_group1(pattern: str, text: str) -> str:
    return get_group(pattern, text, 1)


# ========== New: GetOK / GetReOK ==========


def get_ok(pattern: str, text: str, group: int = 0) -> tuple[str, bool]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return "", False
    found = compiled.search(text)
    if found is None:
        return "", False
    try:
        return found.group(group) or "", True
    except IndexError:
        return "", False


def get_re_ok(
    regex: re.Pattern[str], content: str, group_index: int
) -> tuple[str, bool]:
    if regex is None or group_index < 0:
        return "", False
    groups = regex.search(content)
    if groups is None:
        return "", False
    g = groups.groups()
    if group_index > len(g):
        return "", False
    if group_index == 0:
        return groups.group(0) or "", True
    return g[group_index - 1] or "", True


# ========== New: FindAllGroup0 / FindAllGroup1 ==========


def find_all_group0(pattern: str, text: str) -> list[str]:
    return find_all_group(pattern, text, 0)


def find_all_group1(pattern: str, text: str) -> list[str]:
    return find_all_group(pattern, text, 1)


# ========== New: DelLast ==========


def del_last(pattern: str, text: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return _del_last_re(compiled, text)


def _del_last_re(regex: re.Pattern[str], content: str) -> str:
    mr = _last_index_of_re(regex, content)
    if mr is None:
        return content
    return content[: mr.start] + content[mr.end :]


# ========== New: DelPre ==========


def del_pre(pattern: str, text: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return _del_pre_re(compiled, text)


def _del_pre_re(regex: re.Pattern[str], content: str) -> str:
    mr = _index_of_re(regex, content)
    if mr is None:
        return content
    return content[mr.end :]


# ========== New: Contains ==========


def contains(pattern: str, text: str) -> bool:
    return match(pattern, text)


def contains_re(regex: re.Pattern[str], content: str) -> bool:
    return regex is not None and regex.search(content) is not None


# ========== New: IndexOf / LastIndexOf ==========


def index_of(pattern: str, text: str) -> MatchResult | None:
    compiled = _try_compile(pattern)
    if compiled is None:
        return None
    return _index_of_re(compiled, text)


def _index_of_re(regex: re.Pattern[str], content: str) -> MatchResult | None:
    if regex is None:
        return None
    m = regex.search(content)
    if m is None:
        return None
    return _build_match_result(regex, content, (m.start(), m.end()))


def last_index_of(pattern: str, text: str) -> MatchResult | None:
    compiled = _try_compile(pattern)
    if compiled is None:
        return None
    return _last_index_of_re(compiled, text)


def _last_index_of_re(regex: re.Pattern[str], content: str) -> MatchResult | None:
    if regex is None:
        return None
    matches = list(regex.finditer(content))
    if not matches:
        return None
    m = matches[-1]
    return _build_match_result(regex, content, (m.start(), m.end()))


# ========== New: GetAllGroups / GetAllGroupNames ==========


def get_all_groups(
    pattern: str, text: str, with_group0: bool = False, find_all: bool = False
) -> list[str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return []
    return _get_all_groups_re(compiled, text, with_group0, find_all)


def _get_all_groups_re(
    regex: re.Pattern[str], content: str, with_group0: bool, find_all: bool
) -> list[str]:
    if regex is None:
        return []
    limit = -1 if find_all else 1
    all_matches = list(regex.finditer(content))[:limit] if limit > 0 else list(regex.finditer(content))
    result: list[str] = []
    start = 0 if with_group0 else 1
    for m in all_matches:
        groups = [m.group(i) or "" for i in range(len(m.groups()) + 1)]
        for i in range(start, len(groups)):
            result.append(groups[i])
    return result


def get_all_group_names(pattern: str, text: str) -> dict[str, str]:
    compiled = _try_compile(pattern)
    if compiled is None:
        return {}
    return _get_all_group_names_re(compiled, text)


def _get_all_group_names_re(
    regex: re.Pattern[str], content: str
) -> dict[str, str]:
    if regex is None:
        return {}
    result: dict[str, str] = {}
    m = regex.search(content)
    if m is None:
        return result
    for name, value in m.groupdict().items():
        result[name] = value or ""
    return result


# ========== New: ExtractMulti / ExtractMultiAndDelPre ==========


def _go_to_py_template(template: str) -> str:
    """Convert Go-style $1, $2 template to Python-style \\1, \\2."""
    # Handle $0 -> \g<0> (whole match), $1 -> \1, etc.
    return _group_var_regexp.sub(lambda m: r"\g<" + m.group(1) + ">", template)


def extract_multi(pattern: str, text: str, template: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    return _extract_multi_re(compiled, text, template)


def _extract_multi_re(
    regex: re.Pattern[str], content: str, template: str
) -> str:
    if regex is None:
        return ""
    m = regex.search(content)
    if m is None:
        return ""
    return m.expand(_go_to_py_template(template))


def extract_multi_and_del_pre(
    pattern: str, text: list[str], template: str
) -> str:
    """Extract with template and remove the consumed prefix from text (in-place via list wrapper)."""
    compiled = _try_compile(pattern)
    if compiled is None:
        return ""
    return _extract_multi_and_del_pre_re(compiled, text, template)


def _extract_multi_and_del_pre_re(
    regex: re.Pattern[str], content_holder: list[str], template: str
) -> str:
    if regex is None or content_holder is None:
        return ""
    content = content_holder[0]
    m = regex.search(content)
    if m is None:
        return ""
    result = m.expand(_go_to_py_template(template))
    content_holder[0] = content[m.end() :]
    return result


# ========== New: TemplateVars ==========


def template_vars(template: str) -> list[int]:
    """Return numeric placeholders ($1, $2, ...) referenced by a template, longest first."""
    matches = _group_var_regexp.findall(template)
    seen: set[int] = set()
    result: list[int] = []
    for v_str in matches:
        v = int(v_str)
        if v not in seen:
            seen.add(v)
            result.append(v)
    result.sort(reverse=True)
    return result


# ========== New: Each / First ==========


def each(
    regex: re.Pattern[str], content: str, consumer: Callable[[MatchResult], None]
) -> None:
    if regex is None or consumer is None:
        return
    for m in regex.finditer(content):
        consumer(_build_match_result(regex, content, (m.start(), m.end())))


def first(
    regex: re.Pattern[str], content: str, consumer: Callable[[MatchResult], None]
) -> None:
    if regex is None or consumer is None:
        return
    m = regex.search(content)
    if m is not None:
        consumer(_build_match_result(regex, content, (m.start(), m.end())))


# ========== New: EscapeChar ==========

_re_keys = {
    "$", "(", ")", "*", "+", ".", "[", "]", "?", "\\", "^", "{", "}", "|",
}


def escape_char(c: str) -> str:
    if len(c) != 1:
        return c
    if c in _re_keys:
        return "\\" + c
    return c


# ========== New: ReplaceAll / ReplaceAllFunc ==========


def replace_all(text: str, pattern: str, replacement_template: str) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return _replace_all_re(text, compiled, replacement_template)


def _replace_all_re(
    content: str, regex: re.Pattern[str], replacement_template: str
) -> str:
    if regex is None or content == "":
        return content
    return regex.sub(_go_to_py_template(replacement_template), content)


def replace_all_func(
    text: str, pattern: str, replace_fn: Callable[[MatchResult], str]
) -> str:
    compiled = _try_compile(pattern)
    if compiled is None:
        return text
    return _replace_all_func_re(text, compiled, replace_fn)


def _replace_all_func_re(
    content: str, regex: re.Pattern[str], replace_fn: Callable[[MatchResult], str]
) -> str:
    if regex is None or replace_fn is None or content == "":
        return content
    matches = list(regex.finditer(content))
    if not matches:
        return content
    parts: list[str] = []
    last = 0
    for m in matches:
        parts.append(content[last : m.start()])
        mr = _build_match_result(regex, content, (m.start(), m.end()))
        parts.append(replace_fn(mr))
        last = m.end()
    parts.append(content[last:])
    return "".join(parts)


# ========== New: GetFirstNumber with bool return ==========


def get_first_number_ok(text: str) -> tuple[int, bool]:
    found = _numbers_regex.search(text)
    if found is None:
        return 0, False
    try:
        return int(found.group(0)), True
    except ValueError:
        return 0, False


# ========== New: CountRe, IsMatchRe ==========


def count_re(regex: re.Pattern[str], content: str) -> int:
    if regex is None:
        return 0
    return len(list(regex.finditer(content)))


def is_match_re(regex: re.Pattern[str], content: str) -> bool:
    if regex is None:
        return False
    m = regex.search(content)
    return m is not None and m.start() == 0 and m.end() == len(content)


# ========== New: GetRe, GetByNameRe ==========


def get_re(regex: re.Pattern[str], content: str, group_index: int) -> str:
    value, _ = get_re_ok(regex, content, group_index)
    return value


def get_by_name_re(regex: re.Pattern[str], content: str, group_name: str) -> str:
    if regex is None or group_name == "":
        return ""
    m = regex.search(content)
    if m is None:
        return ""
    try:
        return m.group(group_name) or ""
    except IndexError:
        return ""


# ========== New: DelAllRe, DelFirstRe, ReplaceFirstRe ==========


def del_all_re(regex: re.Pattern[str], content: str) -> str:
    if regex is None or content == "":
        return content
    return regex.sub("", content)


def del_first_re(regex: re.Pattern[str], content: str) -> str:
    return replace_first_re(regex, content, "")


def replace_first_re(
    regex: re.Pattern[str], content: str, replacement: str
) -> str:
    if regex is None or content == "":
        return content
    m = regex.search(content)
    if m is None:
        return content
    repl = m.expand(replacement)
    return content[: m.start()] + repl + content[m.end() :]