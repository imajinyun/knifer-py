"""AI provider-neutral client.

Thin facade over kniferpy.internal.aix, porting knifer-go's vai surface.

Provides a provider-neutral AI client that routes chat and embedding
requests to injected providers. Supports Chat, Embed, and Redact.
"""

from __future__ import annotations

from kniferpy.internal.aix import (
    ChatProvider,
    ChatRequest,
    ChatResponse,
    Client,
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    ErrInvalidChatRequest,
    ErrInvalidEmbeddingRequest,
    ErrMissingChatProvider,
    ErrMissingEmbeddingProvider,
    Message,
    ProviderMetadata,
    Role,
    RoleAssistant,
    RoleSystem,
    RoleUser,
    Usage,
    chat,
    embed,
    new,
    redact,
)

__all__ = [
    "ChatProvider",
    "ChatRequest",
    "ChatResponse",
    "Client",
    "EmbeddingProvider",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "ErrInvalidChatRequest",
    "ErrInvalidEmbeddingRequest",
    "ErrMissingChatProvider",
    "ErrMissingEmbeddingProvider",
    "Message",
    "ProviderMetadata",
    "Role",
    "RoleAssistant",
    "RoleSystem",
    "RoleUser",
    "Usage",
    "chat",
    "embed",
    "new",
    "redact",
]
