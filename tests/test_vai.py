import pytest

from kniferpy.vai import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ErrInvalidChatRequest,
    ErrInvalidEmbeddingRequest,
    ErrMissingChatProvider,
    ErrMissingEmbeddingProvider,
    Message,
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


class _ChatProvider:
    def __init__(self, response: ChatResponse | None = None, error: Exception | None = None):
        self.response = response or ChatResponse(
            Message=Message(Role=RoleAssistant, Content="pong"),
        )
        self.error = error
        self.last_request: ChatRequest | None = None

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.last_request = request
        if self.error:
            raise self.error
        return self.response


class _EmbeddingProvider:
    def __init__(self, response: EmbeddingResponse | None = None, error: Exception | None = None):
        self.response = response or EmbeddingResponse(
            Vectors=[[1.0, 2.0, 3.0]],
        )
        self.error = error
        self.last_request: EmbeddingRequest | None = None

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.last_request = request
        if self.error:
            raise self.error
        return self.response


# --- Role constants ------------------------------------------------------------


def test_role_constants():
    assert RoleSystem == "system"
    assert RoleUser == "user"
    assert RoleAssistant == "assistant"


# --- ChatRequest validation ----------------------------------------------------


def test_chat_request_valid():
    r = ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="hi")])
    r.validate()


def test_chat_request_missing_model():
    r = ChatRequest(Messages=[Message(Role=RoleUser, Content="hi")])
    with pytest.raises(ErrInvalidChatRequest, match="model is required"):
        r.validate()


def test_chat_request_empty_model():
    r = ChatRequest(Model="  ", Messages=[Message(Role=RoleUser, Content="hi")])
    with pytest.raises(ErrInvalidChatRequest, match="model is required"):
        r.validate()


def test_chat_request_no_messages():
    r = ChatRequest(Model="model-a")
    with pytest.raises(ErrInvalidChatRequest, match="at least one message is required"):
        r.validate()


def test_chat_request_missing_role():
    r = ChatRequest(Model="model-a", Messages=[Message(Content="hi")])
    with pytest.raises(ErrInvalidChatRequest, match="message 0 role is required"):
        r.validate()


def test_chat_request_missing_content():
    r = ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser)])
    with pytest.raises(ErrInvalidChatRequest, match="message 0 content is required"):
        r.validate()


def test_chat_request_empty_content():
    r = ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="  ")])
    with pytest.raises(ErrInvalidChatRequest, match="message 0 content is required"):
        r.validate()


def test_chat_request_multi_message_validation():
    r = ChatRequest(
        Model="model-a",
        Messages=[
            Message(Role=RoleUser, Content="hi"),
            Message(Role="", Content="there"),
        ],
    )
    with pytest.raises(ErrInvalidChatRequest, match="message 1 role is required"):
        r.validate()


# --- ChatRequest clone ---------------------------------------------------------


def test_chat_request_clone_independent():
    r = ChatRequest(
        Model="model-a",
        Messages=[Message(Role=RoleUser, Content="hi")],
        Temperature=0.7,
        Metadata={"key": "val"},
    )
    c = r.clone()
    assert c.Model == r.Model
    assert c.Temperature == r.Temperature
    assert c.Metadata == r.Metadata
    assert len(c.Messages) == len(r.Messages)
    c.Messages[0].Content = "modified"
    assert r.Messages[0].Content == "hi"
    c.Metadata["key"] = "changed"
    assert r.Metadata["key"] == "val"


# --- EmbeddingRequest validation -----------------------------------------------


def test_embedding_request_valid():
    r = EmbeddingRequest(Model="embed-a", Input=["hello"])
    r.validate()


def test_embedding_request_missing_model():
    r = EmbeddingRequest(Input=["hello"])
    with pytest.raises(ErrInvalidEmbeddingRequest, match="model is required"):
        r.validate()


def test_embedding_request_no_input():
    r = EmbeddingRequest(Model="embed-a")
    with pytest.raises(ErrInvalidEmbeddingRequest, match="at least one input"):
        r.validate()


def test_embedding_request_empty_input():
    r = EmbeddingRequest(Model="embed-a", Input=["  "])
    with pytest.raises(ErrInvalidEmbeddingRequest, match="input 0 is empty"):
        r.validate()


def test_embedding_request_multi_input_validation():
    r = EmbeddingRequest(Model="embed-a", Input=["hello", ""])
    with pytest.raises(ErrInvalidEmbeddingRequest, match="input 1 is empty"):
        r.validate()


# --- EmbeddingRequest clone ----------------------------------------------------


def test_embedding_request_clone_independent():
    r = EmbeddingRequest(Model="embed-a", Input=["hello"], Metadata={"k": "v"})
    c = r.clone()
    c.Input.append("world")
    assert r.Input == ["hello"]
    c.Metadata["k"] = "changed"
    assert r.Metadata["k"] == "v"


# --- Client.chat ---------------------------------------------------------------


def test_client_chat_success():
    provider = _ChatProvider()
    client = new(chat_provider=provider)
    result = client.chat(ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="ping")]))
    assert result.Message.Content == "pong"


def test_client_chat_validation_error():
    client = new(chat_provider=_ChatProvider())
    with pytest.raises(ErrInvalidChatRequest):
        client.chat(ChatRequest(Model="model-a"))


def test_client_chat_missing_provider():
    client = new()
    with pytest.raises(ErrMissingChatProvider):
        client.chat(ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="hi")]))


def test_client_chat_clones_request():
    provider = _ChatProvider()
    r = ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="ping")])
    client = new(chat_provider=provider)
    client.chat(r)
    assert provider.last_request is not None
    assert provider.last_request is not r
    assert provider.last_request.Model == r.Model


def test_client_chat_clones_response():
    provider = _ChatProvider()
    client = new(chat_provider=provider)
    result = client.chat(ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="ping")]))
    result.Message.Content = "mutated"
    assert provider.response.Message.Content == "pong"


# --- Client.embed --------------------------------------------------------------


def test_client_embed_success():
    provider = _EmbeddingProvider()
    client = new(embedding_provider=provider)
    result = client.embed(EmbeddingRequest(Model="embed-a", Input=["hello"]))
    assert result.Vectors == [[1.0, 2.0, 3.0]]


def test_client_embed_validation_error():
    client = new(embedding_provider=_EmbeddingProvider())
    with pytest.raises(ErrInvalidEmbeddingRequest):
        client.embed(EmbeddingRequest(Model="embed-a"))


def test_client_embed_missing_provider():
    client = new()
    with pytest.raises(ErrMissingEmbeddingProvider):
        client.embed(EmbeddingRequest(Model="embed-a", Input=["hello"]))


def test_client_embed_clones_request():
    provider = _EmbeddingProvider()
    r = EmbeddingRequest(Model="embed-a", Input=["hello"])
    client = new(embedding_provider=provider)
    client.embed(r)
    assert provider.last_request is not None
    assert provider.last_request is not r


def test_client_embed_clones_response():
    provider = _EmbeddingProvider()
    client = new(embedding_provider=provider)
    result = client.embed(EmbeddingRequest(Model="embed-a", Input=["hello"]))
    result.Vectors.append([9.9])
    assert len(provider.response.Vectors) == 1


# --- short-lived convenience functions -----------------------------------------


def test_chat_shortcut():
    provider = _ChatProvider()
    result = chat(provider, ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="ping")]))
    assert result.Message.Content == "pong"


def test_embed_shortcut():
    provider = _EmbeddingProvider()
    result = embed(provider, EmbeddingRequest(Model="embed-a", Input=["hello"]))
    assert result.Vectors == [[1.0, 2.0, 3.0]]


# --- redact --------------------------------------------------------------------


def test_redact_secret_words():
    assert redact("api key sk-test secret") == "api key [REDACTED] [REDACTED]"


def test_redact_password():
    assert redact("my password is here") == "my [REDACTED] is here"


def test_redact_no_op():
    assert redact("hello world") == "hello world"


def test_redact_sk_prefix():
    assert redact("token sk-abc123 is here") == "token [REDACTED] is here"


# --- ChatResponse clone --------------------------------------------------------


def test_chat_response_clone_independent():
    r = ChatResponse(
        Message=Message(Role=RoleAssistant, Content="hello"),
        Usage=Usage(InputTokens=10, OutputTokens=5, TotalTokens=15),
    )
    c = r.clone()
    c.Message.Content = "changed"
    assert r.Message.Content == "hello"


# --- EmbeddingResponse clone ---------------------------------------------------


def test_embedding_response_clone_independent():
    r = EmbeddingResponse(Vectors=[[1.0, 2.0]])
    c = r.clone()
    c.Vectors[0].append(3.0)
    assert r.Vectors == [[1.0, 2.0]]


# --- convenience chat with missing provider ------------------------------------


def test_chat_shortcut_missing_provider():
    with pytest.raises(ErrMissingChatProvider):
        chat(None, ChatRequest(Model="model-a", Messages=[Message(Role=RoleUser, Content="hi")]))


def test_embed_shortcut_missing_provider():
    with pytest.raises(ErrMissingEmbeddingProvider):
        embed(None, EmbeddingRequest(Model="embed-a", Input=["hello"]))


# --- Usage dataclass -----------------------------------------------------------


def test_usage_defaults():
    u = Usage()
    assert u.InputTokens == 0
    assert u.OutputTokens == 0
    assert u.TotalTokens == 0