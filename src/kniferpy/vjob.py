"""Parallel job execution with slice, batch, and map adapters.

Thin facade over kniferpy.internal.jobx, porting knifer-go's vjob surface.

Provides concurrent job execution over index ranges, typed slices, and
map keys with configurable batch size and concurrency.
"""

from __future__ import annotations

from kniferpy.internal.jobx import (
    Batch,
    ErrInvalidMapJob,
    ErrInvalidRange,
    ErrNilJob,
    Merge,
    OptionCarrier,
    Options,
    Slice,
    Sliceable,
    new_batch,
    new_batch_single,
    new_map,
    new_map_keys,
    new_slice,
    new_slice_single,
    run,
    run_with,
)

# ── Go-compat NewMapE alias ───────────────────────────────────────────────────

new_map_e = new_map
"""Error-returning variant (Go compat). In Python, new_map raises exceptions."""

__all__ = [
    "Batch",
    "ErrInvalidMapJob",
    "ErrInvalidRange",
    "ErrNilJob",
    "Merge",
    "OptionCarrier",
    "Options",
    "Slice",
    "Sliceable",
    "new_batch",
    "new_batch_single",
    "new_map",
    "new_map_e",
    "new_map_keys",
    "new_slice",
    "new_slice_single",
    "run",
    "run_with",
]