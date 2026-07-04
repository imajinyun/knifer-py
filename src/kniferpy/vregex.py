from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from kniferpy.internal import regexx
from kniferpy.internal.regexx import MatchResult, RE_CHINESE, RE_CHINESES

# ── Go-compat type alias ───────────────────────────────────────────────────────

Option = Callable[[Any], None]

# Pattern-string matchers
match = regexx.match
is_match = regexx.is_match
find = regexx.find
find_all = regexx.find_all
count = regexx.count
contains = regexx.contains

# Replacement
replace = regexx.replace
replace_first = regexx.replace_first
replace_func = regexx.replace_func
replace_all = regexx.replace_all
replace_all_func = regexx.replace_all_func

# Deletion
delete_all = regexx.delete_all
delete_first = regexx.delete_first
del_last = regexx.del_last
del_pre = regexx.del_pre

# Group extraction
get_group = regexx.get_group
get_group0 = regexx.get_group0
get_group1 = regexx.get_group1
get_ok = regexx.get_ok
get_group_by_name = regexx.get_group_by_name
find_all_group = regexx.find_all_group
find_all_group0 = regexx.find_all_group0
find_all_group1 = regexx.find_all_group1
named_groups = regexx.named_groups
get_all_groups = regexx.get_all_groups
get_all_group_names = regexx.get_all_group_names

# Index / position
index_of = regexx.index_of
last_index_of = regexx.last_index_of

# Template extraction
extract_multi = regexx.extract_multi
extract_multi_and_del_pre = regexx.extract_multi_and_del_pre
template_vars = regexx.template_vars

# Iteration
each = regexx.each
first = regexx.first

# Escape
escape = regexx.escape
escape_char = regexx.escape_char

# Number extraction
get_first_number = regexx.get_first_number
get_first_number_ok = regexx.get_first_number_ok

# Pre-compiled regex helpers
contains_re = regexx.contains_re
count_re = regexx.count_re
is_match_re = regexx.is_match_re
get_re = regexx.get_re
get_re_ok = regexx.get_re_ok
get_by_name_re = regexx.get_by_name_re
del_all_re = regexx.del_all_re
del_first_re = regexx.del_first_re
replace_first_re = regexx.replace_first_re

# Pre-compiled regex helpers (continued)
get_all_group_names_re = regexx.get_all_group_names_re
find_all_group_re = regexx.find_all_group_re
del_last_re = regexx.del_last_re
del_pre_re = regexx.del_pre_re
extract_multi_re = regexx.extract_multi_re
extract_multi_and_del_pre_re = regexx.extract_multi_and_del_pre_re
replace_all_re = regexx.replace_all_re
replace_all_func_re = regexx.replace_all_func_re

__all__ = [
    "MatchResult",
    "RE_CHINESE",
    "RE_CHINESES",
    "match",
    "is_match",
    "find",
    "find_all",
    "count",
    "contains",
    "replace",
    "replace_first",
    "replace_func",
    "replace_all",
    "replace_all_func",
    "delete_all",
    "delete_first",
    "del_last",
    "del_pre",
    "get_group",
    "get_group0",
    "get_group1",
    "get_ok",
    "get_group_by_name",
    "find_all_group",
    "find_all_group0",
    "find_all_group1",
    "named_groups",
    "get_all_groups",
    "get_all_group_names",
    "index_of",
    "last_index_of",
    "extract_multi",
    "extract_multi_and_del_pre",
    "template_vars",
    "each",
    "first",
    "escape",
    "escape_char",
    "get_first_number",
    "get_first_number_ok",
    "contains_re",
    "count_re",
    "is_match_re",
    "get_re",
    "get_re_ok",
    "get_by_name_re",
    "del_all_re",
    "del_first_re",
    "replace_first_re",
    "get_all_group_names_re",
    "find_all_group_re",
    "del_last_re",
    "del_pre_re",
    "extract_multi_re",
    "extract_multi_and_del_pre_re",
    "replace_all_re",
    "replace_all_func_re",
]