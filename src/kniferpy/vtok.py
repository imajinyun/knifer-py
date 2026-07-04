"""Provider-neutral text tokenization and keyword extraction.

Thin facade over kniferpy.internal.tokenizex, porting knifer-go's vtok surface.

Python-idiomatic mappings:
- Go context.Context -> omitted (synchronous)
- Go Provider interface -> Protocol
- Go functional With* options -> keyword args on Client constructor
"""

from __future__ import annotations

from kniferpy.internal.tokenizex import (
    Client,
    Keyword,
    KeywordsRequest,
    KeywordsResponse,
    Mode,
    Provider,
    SimpleProvider,
    Token,
    TokenizeRequest,
    TokenizeResponse,
    bigram,
    filter_words,
    is_stop_word,
    new_simple_provider,
    ngram,
    remove_stop_words,
    trigram,
)

__all__ = [
    "Client",
    "Keyword",
    "KeywordsRequest",
    "KeywordsResponse",
    "Mode",
    "Provider",
    "SimpleProvider",
    "Token",
    "TokenizeRequest",
    "TokenizeResponse",
    "bigram",
    "filter_words",
    "is_stop_word",
    "new_simple_provider",
    "ngram",
    "remove_stop_words",
    "trigram",
]