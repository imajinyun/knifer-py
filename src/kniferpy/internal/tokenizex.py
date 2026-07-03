"""Provider-neutral text tokenization and keyword extraction.

Ports knifer-go's internal/tokenize with Python-idiomatic mappings:

- Go context.Context -> omitted (synchronous)
- Go Provider interface -> Protocol
- Go functional options -> keyword args
- Go error sentinels -> KniferError with codes

Errors use kniferpy.verr types with codes knifer.tok.<reason>.
"""

from __future__ import annotations

import copy
import dataclasses
from typing import Protocol, runtime_checkable

from kniferpy.verr import KniferError, ValidationError


class Mode:
    """Provider-specific tokenization mode."""

    DEFAULT = "default"
    PRECISE = "precise"
    SEARCH = "search"
    FULL = "full"

    _VALID = frozenset({DEFAULT, PRECISE, SEARCH, FULL})


@dataclasses.dataclass(slots=True)
class Token:
    """One token emitted by a tokenizer provider."""

    text: str
    start: int = 0
    end: int = 0
    position: int = 0
    weight: float = 0.0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class Keyword:
    """One keyword emitted by a keyword extraction provider."""

    text: str
    score: float = 0.0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class TokenizeRequest:
    """Tokenization request with optional limits."""

    text: str
    mode: str = Mode.DEFAULT
    keep_punct: bool = False
    max_input_runes: int = 0
    max_tokens: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        _validate_text(self.text, self.max_input_runes, "knifer.tok.invalid_tokenize_request")
        if self.max_tokens < 0:
            raise ValidationError(
                message="max tokens must be non-negative",
                code="knifer.tok.invalid_tokenize_request",
            )
        if self.mode not in Mode._VALID:
            raise ValidationError(
                message=f"unsupported mode {self.mode!r}",
                code="knifer.tok.invalid_tokenize_request",
            )

    def clone(self) -> TokenizeRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class TokenizeResponse:
    """Tokenization output with metadata."""

    text: str = ""
    tokens: list[Token] = dataclasses.field(default_factory=list)
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(slots=True)
class KeywordsRequest:
    """Keyword extraction request with optional limits."""

    text: str
    limit: int = 0
    max_input_runes: int = 0
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def validate(self) -> None:
        _validate_text(self.text, self.max_input_runes, "knifer.tok.invalid_keywords_request")
        if self.limit < 0:
            raise ValidationError(
                message="limit must be non-negative",
                code="knifer.tok.invalid_keywords_request",
            )

    def clone(self) -> KeywordsRequest:
        return copy.copy(self)


@dataclasses.dataclass(slots=True)
class KeywordsResponse:
    """Keyword extraction output with metadata."""

    text: str = ""
    keywords: list[Keyword] = dataclasses.field(default_factory=list)
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)


@runtime_checkable
class Provider(Protocol):
    """Performs provider-specific tokenization for validated requests."""

    def tokenize(self, request: TokenizeRequest) -> TokenizeResponse: ...

    def keywords(self, request: KeywordsRequest) -> KeywordsResponse: ...


class Client:
    """Routes validated tokenization requests to an injected provider."""

    def __init__(self, provider: Provider | None = None) -> None:
        self._provider = provider

    def tokenize(self, request: TokenizeRequest) -> TokenizeResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.tok.missing_provider")
        request.validate()
        response = self._provider.tokenize(request.clone())
        if request.max_tokens > 0 and len(response.tokens) > request.max_tokens:
            raise KniferError(
                message=f"provider returned {len(response.tokens)} tokens,"
                f" max {request.max_tokens}",
                code="knifer.tok.token_limit_exceeded",
            )
        return response

    def keywords(self, request: KeywordsRequest) -> KeywordsResponse:
        if self._provider is None:
            raise KniferError(message="missing provider", code="knifer.tok.missing_provider")
        request.validate()
        return self._provider.keywords(request.clone())


def _validate_text(text: str, max_runes: int, code: str) -> None:
    if not text.strip():
        raise ValidationError(message="text is required", code=code)
    if "\x00" in text:
        raise ValidationError(message="text contains nul byte", code=code)
    if max_runes < 0:
        raise ValidationError(message="max input runes must be non-negative", code=code)
    if max_runes > 0:
        runes = len(text)
        if runes > max_runes:
            raise ValidationError(
                message=f"input has {runes} runes, max {max_runes}",
                code="knifer.tok.input_limit_exceeded",
            )
