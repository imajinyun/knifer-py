"""Random generation utilities.

Ports knifer-go's internal/rand with Python-idiomatic mappings.

Supports:
- Random int, float, bool, long
- Random bytes (cryptographic with fallback for compatibility)
- Random strings from custom character sets
- Random element picking from a list
- Weighted random selection with the alias method
- Per-call options for custom sources and readers
"""
from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal.randx import (
    BaseChar,
    BaseCharNumber,
    BaseCharNumberUC,
    BaseNumber,
    configure_default_random_source_provider,
    random_bool,
    random_bool_with_options,
    random_bytes,
    random_bytes_with_options,
    random_ele,
    random_ele_with_options,
    random_float,
    random_float_with_options,
    random_int,
    random_int_range,
    random_int_range_with_options,
    random_int_with_options,
    random_long,
    random_long_with_options,
    random_numbers,
    random_numbers_with_options,
    random_string,
    random_string_from,
    random_string_from_with_options,
    random_string_upper,
    random_string_upper_with_options,
    random_string_with_options,
    reset_default_random_source,
    secure_random_bytes,
    secure_random_bytes_with_options,
    set_seed,
    weighted_pick,
    weighted_pick_n,
    weighted_pick_unique_n,
    with_random_reader,
    with_random_source,
    with_strict_crypto_random,
    with_weighted_precision,
    with_weighted_rand_source,
)

__all__ = [
    # Character sets
    "BaseNumber",
    "BaseChar",
    "BaseCharNumber",
    "BaseCharNumberUC",
    # Go-compat type aliases
    "RandomOption",
    "WeightedOption",
    # Basic random
    "random_int",
    "random_int_with_options",
    "random_int_range",
    "random_int_range_with_options",
    "random_long",
    "random_long_with_options",
    "random_float",
    "random_float_with_options",
    "random_bool",
    "random_bool_with_options",
    # Byte random
    "random_bytes",
    "random_bytes_with_options",
    "secure_random_bytes",
    "secure_random_bytes_with_options",
    # String random
    "random_string",
    "random_string_with_options",
    "random_numbers",
    "random_numbers_with_options",
    "random_string_upper",
    "random_string_upper_with_options",
    "random_string_from",
    "random_string_from_with_options",
    # Element selection
    "random_ele",
    "random_ele_with_options",
    # Global source
    "set_seed",
    "configure_default_random_source_provider",
    "reset_default_random_source",
    # Options
    "with_random_source",
    "with_random_reader",
    "with_strict_crypto_random",
    # Weighted selection
    "weighted_pick",
    "weighted_pick_n",
    "weighted_pick_unique_n",
    "with_weighted_rand_source",
    "with_weighted_precision",
]

# ── Go-compat type aliases ─────────────────────────────────────────────────────

RandomOption = Callable[[Any], None]
"""Functional option for random generation (Go compat)."""

WeightedOption = Callable[[Any], None]
"""Functional option for weighted random selection (Go compat)."""