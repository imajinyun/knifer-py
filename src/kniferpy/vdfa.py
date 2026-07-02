"""DFA/trie-based sensitive-word matching and text filtering.

Build a :class:`WordTree` from a dictionary of words and scan text for matches,
or use the package-level matcher via :func:`init` / :func:`contains` /
:func:`filter`. Punctuation and whitespace between characters are ignored by
default, so ``bad`` still matches ``b-a-d``.
"""

from __future__ import annotations

from kniferpy.internal import dfax
from kniferpy.internal.dfax import (
    DEFAULT_SEPARATOR,
    CharFilter,
    FoundWord,
    Processor,
    WordTree,
    default_processor,
    is_not_stop_char,
    is_stop_char,
)

__all__ = [
    "DEFAULT_SEPARATOR",
    "CharFilter",
    "FoundWord",
    "Processor",
    "WordTree",
    "contains",
    "default_processor",
    "filter",
    "get_found_all",
    "get_found_all_mode",
    "get_found_first",
    "init",
    "init_string",
    "is_inited",
    "is_not_stop_char",
    "is_stop_char",
    "new_word_tree",
    "set_char_filter",
]


def new_word_tree(*, char_filter: CharFilter | None = None) -> WordTree:
    """Create an empty word tree using the default stop-rune filter."""
    return dfax.new_word_tree(char_filter=char_filter)


def is_inited() -> bool:
    """Report whether the package-level matcher contains words."""
    return dfax.is_inited()


def init(words: list[str], *, char_filter: CharFilter | None = None) -> None:
    """Replace the package-level matcher with ``words``."""
    dfax.init(words, char_filter=char_filter)


def init_string(
    words: str,
    separator: str = DEFAULT_SEPARATOR,
    *,
    char_filter: CharFilter | None = None,
) -> None:
    """Initialize the package-level matcher from a separated string."""
    dfax.init_string(words, separator, char_filter=char_filter)


def set_char_filter(char_filter: CharFilter | None) -> None:
    """Set the filter used by the package-level matcher."""
    dfax.set_char_filter(char_filter)


def contains(text: str) -> bool:
    """Report whether ``text`` contains a word from the package-level matcher."""
    return dfax.contains(text)


def get_found_first(text: str) -> FoundWord | None:
    """Return the first found word from the package-level matcher."""
    return dfax.get_found_first(text)


def get_found_all(text: str) -> list[FoundWord]:
    """Return all found words from the package-level matcher."""
    return dfax.get_found_all(text)


def get_found_all_mode(text: str, density_match: bool, greed_match: bool) -> list[FoundWord]:
    """Return all found words with dense and greedy matching controls."""
    return dfax.get_found_all_mode(text, density_match, greed_match)


def filter(text: str, greed_match: bool = True, processor: Processor | None = None) -> str:
    """Replace words found by the package-level matcher (masked with ``*`` by default)."""
    return dfax.filter(text, greed_match, processor)
