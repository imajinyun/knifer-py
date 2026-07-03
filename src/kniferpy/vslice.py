"""Collection (slice) helpers.

Thin facade over kniferpy.internal.slicex, porting knifer-go's vslice surface.

Python-idiomatic mappings:
- Go generics [T any] -> Python duck typing
- Go iter.Seq[T] -> Python generators via iter_items/iter_indexed
- Go (T, bool) -> T | None

Omitted (Go-specific):
- Pair type alias (Python uses tuple directly)
- Iter/IterIndexed as iterator types (returns plain iterables)
"""

from __future__ import annotations

from kniferpy.internal.slicex import (
    associate,
    chunk,
    compact,
    concat,
    contains,
    count_by,
    distinct,
    filter_err,
    filter_map,
    filter_values,
    find,
    find_index,
    flat_map,
    flatten,
    for_each,
    group_by,
    index_of,
    intersection,
    is_empty,
    is_not_empty,
    iter_indexed,
    iter_items,
    join,
    key_by,
    last_index_of,
    map_err,
    map_values,
    page,
    partition_by,
    reduce,
    reduce_err,
    reject,
    reverse,
    slice_to_map,
    sliding,
    sub,
    subtract,
    union,
    uniq,
    uniq_by,
    unzip2,
    window,
    zip2,
)

__all__ = [
    "associate",
    "chunk",
    "compact",
    "concat",
    "contains",
    "count_by",
    "distinct",
    "filter_err",
    "filter_map",
    "filter_values",
    "find",
    "find_index",
    "flat_map",
    "flatten",
    "for_each",
    "group_by",
    "index_of",
    "intersection",
    "is_empty",
    "is_not_empty",
    "iter_indexed",
    "iter_items",
    "join",
    "key_by",
    "last_index_of",
    "map_err",
    "map_values",
    "page",
    "partition_by",
    "reduce",
    "reduce_err",
    "reject",
    "reverse",
    "slice_to_map",
    "sliding",
    "sub",
    "subtract",
    "uniq",
    "uniq_by",
    "union",
    "unzip2",
    "window",
    "zip2",
]
