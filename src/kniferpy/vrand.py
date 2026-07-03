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

import os
import random

from kniferpy.internal.randx import (
    BaseNumber,
    BaseChar,
    BaseCharNumber,
    BaseCharNumberUC,
    RandomOption,
    random_int,
    random_int_with_options,
    random_int_range,
    random_int_range_with_options,
    random_long,
    random_long_with_options,
    random_float,
    random_float_with_options,
    random_bool,
    random_bool_with_options,
    random_bytes,
    random_bytes_with_options,
    secure_random_bytes,
    secure_random_bytes_with_options,
    random_string,
    random_string_with_options,
    random_numbers,
    random_numbers_with_options,
    random_string_upper,
    random_string_upper_with_options,
    random_string_from,
    random_string_from_with_options,
    random_ele,
    random_ele_with_options,
    with_random_source,
    with_random_reader,
    with_strict_crypto_random,
    set_seed,
    configure_default_random_source_provider,
    reset_default_random_source,
    weighted_pick,
    weighted_pick_n,
    weighted_pick_unique_n,
    with_weighted_rand_source,
    with_weighted_precision,
)

__all__ = [
    # Character sets
    "BaseNumber",
    "BaseChar",
    "BaseCharNumber",
    "BaseCharNumberUC",
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