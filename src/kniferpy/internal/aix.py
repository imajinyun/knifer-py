"""Provider-neutral AI client.

Ports knifer-go's internal/ai with Python-idiomatic mappings:

- Go context.Context -> explicit context passing (compatible with any async framework)
- Go interface ChatProvider/EmbeddingProvider -> Python Protocol
- Go functional options -> keyword arguments
- Go error sentinels -> kniferpy.verr KniferError

Errors use kniferpy.verr types with codes knifer.ai.<reason>.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Protocol

from kniferpy.verr import KniferError


# --- errors --------------------------------------------------------------------

class ErrInvalidChatRequest(KniferError):
    pass


class ErrInvalidEmbeddingRequest(KniferError):
    pass


class ErrMissingChatProvider(KniferError):
    pass


class ErrMissingEmbeddingProvider(KniferError):
    pass


# --- types ---------------------------------------------------------------------

class Role(str):
    """Identifies the speaker or source of a chat message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


RoleSystem = Role.SYSTEM
RoleUser = Role.USER
RoleAssistant = Role.ASSISTANT


@dataclass
class Message:
    Role: str = ""
    Content: str = ""


@dataclass
class Usage:
    InputTokens: int = 0
    OutputTokens: int = 0
    TotalTokens: int = 0


@dataclass
class ProviderMetadata:
    Name: str = ""
    Model: str = ""
    TraceID: str = ""


@dataclass
class ChatRequest:
    Model: str = ""
    Messages: list[Message] = field(default_factory=list)
    Temperature: float = 0.0
    Metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.Model.strip():
            raise ErrInvalidChatRequest("model is required")
        if not self.Messages:
            raise ErrInvalidChatRequest("at least one message is required")
        for i, msg in enumerate(self.Messages):
            if not msg.Role.strip():
                raise ErrInvalidChatRequest(f"message {i} role is required")
            if not msg.Content.strip():
                raise ErrInvalidChatRequest(f"message {i} content is required")

    def clone(self) -> ChatRequest:
        return ChatRequest(
            Model=self.Model,
            Messages=[copy.copy(m) for m in self.Messages],
            Temperature=self.Temperature,
            Metadata=dict(self.Metadata),
        )


@dataclass
class ChatResponse:
    Message: Message = field(default_factory=Message)
    Usage: Usage = field(default_factory=Usage)
    Provider: ProviderMetadata = field(default_factory=ProviderMetadata)

    def clone(self) -> ChatResponse:
        return ChatResponse(
            Message=copy.copy(self.Message),
            Usage=copy.copy(self.Usage),
            Provider=copy.copy(self.Provider),
        )


@dataclass
class EmbeddingRequest:
    Model: str = ""
    Input: list[str] = field(default_factory=list)
    Metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.Model.strip():
            raise ErrInvalidEmbeddingRequest("model is required")
        if not self.Input:
            raise ErrInvalidEmbeddingRequest("at least one input is required")
        for i, text in enumerate(self.Input):
            if not text.strip():
                raise ErrInvalidEmbeddingRequest(f"input {i} is empty")

    def clone(self) -> EmbeddingRequest:
        return EmbeddingRequest(
            Model=self.Model,
            Input=list(self.Input),
            Metadata=dict(self.Metadata),
        )


@dataclass
class EmbeddingResponse:
    Vectors: list[list[float]] = field(default_factory=list)
    Usage: Usage = field(default_factory=Usage)
    Provider: ProviderMetadata = field(default_factory=ProviderMetadata)

    def clone(self) -> EmbeddingResponse:
        return EmbeddingResponse(
            Vectors=[list(v) for v in self.Vectors],
            Usage=copy.copy(self.Usage),
            Provider=copy.copy(self.Provider),
        )


# --- provider interfaces -------------------------------------------------------

class ChatProvider(Protocol):
    def chat(self, request: ChatRequest) -> ChatResponse:
        ...


class EmbeddingProvider(Protocol):
    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        ...


# --- client --------------------------------------------------------------------

class Client:
    def __init__(
        self,
        chat_provider: ChatProvider | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ):
        self._chat_provider = chat_provider
        self._embedding_provider = embedding_provider

    def chat(self, request: ChatRequest) -> ChatResponse:
        request.validate()
        if self._chat_provider is None:
            raise ErrMissingChatProvider("no chat provider configured")
        response = self._chat_provider.chat(request.clone())
        return response.clone()

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        request.validate()
        if self._embedding_provider is None:
            raise ErrMissingEmbeddingProvider("no embedding provider configured")
        response = self._embedding_provider.embed(request.clone())
        return response.clone()


def new(
    chat_provider: ChatProvider | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> Client:
    return Client(chat_provider=chat_provider, embedding_provider=embedding_provider)


def chat(provider: ChatProvider, request: ChatRequest) -> ChatResponse:
    return new(chat_provider=provider).chat(request)


def embed(provider: EmbeddingProvider, request: EmbeddingRequest) -> EmbeddingResponse:
    return new(embedding_provider=provider).embed(request)


# --- redact --------------------------------------------------------------------

_SECRET_WORDS = frozenset({"secret", "password"})


def redact(text: str) -> str:
    fields = text.split()
    for i, field in enumerate(fields):
        lower = field.strip("'\"`.,;:()[]{}<>").lower()
        if lower in _SECRET_WORDS or lower.startswith("sk-"):
            fields[i] = "[REDACTED]"
    return " ".join(fields)