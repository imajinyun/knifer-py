"""Provider-neutral text tokenization and keyword extraction.

Thin facade over kniferpy.internal.tokenizex, porting knifer-go's vtok surface.

Python-idiomatic mappings:
- Go context.Context -> omitted (synchronous)
- Go Provider interface -> Protocol
- Go functional With* options -> keyword args on Client constructor
- Go error sentinels -> KniferError with codes knifer.tok.*

Omitted (Go-specific):
- context.Context cancellation (not needed in sync Python)
- WithProvider functional option (provider is a constructor arg)
"""

from __future__ import annotations

from kniferpy.internal.tokenizex import (
    Client,
    Keyword,
    KeywordsRequest,
    KeywordsResponse,
    Mode,
    Provider,
    Token,
    TokenizeRequest,
    TokenizeResponse,
)

__all__ = [
    "Client",
    "Keyword",
    "KeywordsRequest",
    "KeywordsResponse",
    "Mode",
    "Provider",
    "Token",
    "TokenizeRequest",
    "TokenizeResponse",
]
