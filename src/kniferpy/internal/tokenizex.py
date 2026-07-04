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


# ========== N-Gram ==========


def ngram(text: str, n: int) -> list[str]:
    if n <= 0:
        return []
    if n > len(text):
        return [text] if text else []
    result: list[str] = []
    chars = list(text)
    for i in range(len(chars) - n + 1):
        result.append("".join(chars[i : i + n]))
    return result


def bigram(text: str) -> list[str]:
    return ngram(text, 2)


def trigram(text: str) -> list[str]:
    return ngram(text, 3)


# ========== Word Filter ==========


def filter_words(text: str, min_len: int = 1, allowed_chars: str | None = None) -> list[str]:
    import re as _re
    if allowed_chars:
        pattern = _re.compile(f"[{_re.escape(allowed_chars)}]+")
    else:
        pattern = _re.compile(r"\w+")
    words = pattern.findall(text)
    if min_len > 1:
        words = [w for w in words if len(w) >= min_len]
    return words


# ========== Stop Words ==========

_ENGLISH_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "shall", "not", "no", "nor", "so", "as", "its", "it",
    "this", "that", "these", "those", "he", "she", "they", "we", "you", "me",
    "him", "her", "us", "them", "my", "your", "his", "our", "their", "i",
})


def remove_stop_words(words: list[str], stop_words: set[str] | None = None) -> list[str]:
    sw = stop_words if stop_words is not None else _ENGLISH_STOP_WORDS
    return [w for w in words if w.lower() not in sw]


def is_stop_word(word: str, stop_words: set[str] | None = None) -> bool:
    sw = stop_words if stop_words is not None else _ENGLISH_STOP_WORDS
    return word.lower() in sw


# ========== Simple Built-in Tokenizer ==========


class SimpleProvider:
    """A simple regex-based tokenizer provider."""

    def tokenize(self, request: TokenizeRequest) -> TokenizeResponse:
        import re as _re
        words = _re.findall(r"\w+", request.text)
        tokens: list[Token] = []
        pos = 0
        for i, word in enumerate(words):
            start = request.text.find(word, pos)
            if start < 0:
                start = 0
            end = start + len(word)
            tokens.append(Token(
                text=word,
                start=start,
                end=end,
                position=i,
                weight=1.0,
            ))
            pos = end
        if request.max_tokens > 0 and len(tokens) > request.max_tokens:
            tokens = tokens[:request.max_tokens]
        return TokenizeResponse(text=request.text, tokens=tokens)

    def keywords(self, request: KeywordsRequest) -> KeywordsResponse:
        import re as _re
        from collections import Counter
        words = _re.findall(r"\w+", request.text)
        words = [w for w in words if w.lower() not in _ENGLISH_STOP_WORDS]
        counter = Counter(words)
        total = sum(counter.values()) or 1
        keywords = [
            Keyword(text=word, score=count / total)
            for word, count in counter.most_common(request.limit if request.limit > 0 else None)
        ]
        return KeywordsResponse(text=request.text, keywords=keywords)


def new_simple_provider() -> SimpleProvider:
    return SimpleProvider()
