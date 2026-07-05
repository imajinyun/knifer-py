from __future__ import annotations

from typing import Any, Callable

from kniferpy.internal import idx
from kniferpy.internal.idx import (
    DEFAULT_NANO_ID_LENGTH,
    NANO_ID_ALPHABET,
    Snowflake,
    UUID,
    configure_default_fallback_random_source_provider,
    configure_default_snowflake,
    create_snowflake,
    fast_simple_uuid,
    fast_uuid,
    get_datacenter_id,
    get_snowflake,
    get_snowflake_with_worker,
    get_snowflake_with_worker_datacenter,
    get_worker_id,
    nano_id,
    nano_id_n,
    new_isolated_snowflake,
    object_id,
    random_uuid,
    reset_default_fallback_random_source,
    set_fallback_random_seed,
    simple_uuid,
    snowflake_next_id,
    snowflake_next_id_str,
)

# ── Go-compat type aliases ────────────────────────────────────────────────────

RandomOption = Callable[[Any], None]
ObjectIDOption = Callable[[Any], None]
NanoIDOption = Callable[[Any], None]
SnowflakeOption = Callable[[Any], None]

# ── Go-compat UUID alias ──────────────────────────────────────────────────────

# UUID is already imported from idx as a simple_uuid alias.

# ── Go-compat *WithOptions aliases ────────────────────────────────────────────

random_uuid_with_options = random_uuid
simple_uuid_with_options = simple_uuid
fast_uuid_with_options = fast_uuid
fast_simple_uuid_with_options = fast_simple_uuid
object_id_with_options = object_id
create_snowflake_with_options = create_snowflake
get_snowflake_with_options = get_snowflake
get_snowflake_with_worker_with_options = get_snowflake_with_worker
get_snowflake_with_worker_datacenter_with_options = get_snowflake_with_worker_datacenter
get_datacenter_id_with_options = get_datacenter_id
get_worker_id_with_options = get_worker_id
nano_id_with_options = nano_id
nano_id_n_with_options = nano_id_n
snowflake_next_id_with_options = snowflake_next_id
snowflake_next_id_str_with_options = snowflake_next_id_str

__all__ = [
    "DEFAULT_NANO_ID_LENGTH",
    "NANO_ID_ALPHABET",
    "Snowflake",
    "UUID",
    "random_uuid",
    "fast_uuid",
    "simple_uuid",
    "fast_simple_uuid",
    "nano_id",
    "nano_id_n",
    "object_id",
    "create_snowflake",
    "new_isolated_snowflake",
    "get_snowflake",
    "configure_default_snowflake",
    "get_snowflake_with_worker",
    "get_snowflake_with_worker_datacenter",
    "get_datacenter_id",
    "get_worker_id",
    "snowflake_next_id",
    "snowflake_next_id_str",
    "configure_default_fallback_random_source_provider",
    "reset_default_fallback_random_source",
    "set_fallback_random_seed",
    # Go-compat type aliases
    "RandomOption",
    "ObjectIDOption",
    "NanoIDOption",
    "SnowflakeOption",
    # Go-compat *WithOptions aliases
    "random_uuid_with_options",
    "simple_uuid_with_options",
    "fast_uuid_with_options",
    "fast_simple_uuid_with_options",
    "object_id_with_options",
    "create_snowflake_with_options",
    "get_snowflake_with_options",
    "get_snowflake_with_worker_with_options",
    "get_snowflake_with_worker_datacenter_with_options",
    "get_datacenter_id_with_options",
    "get_worker_id_with_options",
    "nano_id_with_options",
    "nano_id_n_with_options",
    "snowflake_next_id_with_options",
    "snowflake_next_id_str_with_options",
]