from __future__ import annotations

import pytest

from kniferpy import vtok
from kniferpy.verr import KniferError, ValidationError


class ExampleProvider:
    def tokenize(self, request: vtok.TokenizeRequest) -> vtok.TokenizeResponse:
        return vtok.TokenizeResponse(
            text=request.text,
            tokens=[
                vtok.Token(text="南京", start=0, end=2, position=0),
                vtok.Token(text="长江大桥", start=3, end=7, position=1),
            ],
        )

    def keywords(self, request: vtok.KeywordsRequest) -> vtok.KeywordsResponse:
        return vtok.KeywordsResponse(
            text=request.text,
            keywords=[
                vtok.Keyword(text="南京", score=0.9),
                vtok.Keyword(text="长江大桥", score=0.8),
            ],
        )


# --- Mode ----------------------------------------------------------------


def test_mode_defaults() -> None:
    assert vtok.Mode.DEFAULT == "default"
    assert vtok.Mode.PRECISE == "precise"
    assert vtok.Mode.SEARCH == "search"
    assert vtok.Mode.FULL == "full"


# --- TokenizeRequest validation -------------------------------------------


def test_tokenize_request_valid() -> None:
    req = vtok.TokenizeRequest(text="hello")
    req.validate()  # no exception


def test_tokenize_request_empty_text() -> None:
    with pytest.raises(ValidationError, match="text is required"):
        vtok.TokenizeRequest(text="").validate()


def test_tokenize_request_whitespace_only() -> None:
    with pytest.raises(ValidationError, match="text is required"):
        vtok.TokenizeRequest(text="   ").validate()


def test_tokenize_request_nul_byte() -> None:
    with pytest.raises(ValidationError, match="nul byte"):
        vtok.TokenizeRequest(text="ab\x00cd").validate()


def test_tokenize_request_negative_max_runes() -> None:
    with pytest.raises(ValidationError, match="max input runes"):
        vtok.TokenizeRequest(text="hello", max_input_runes=-1).validate()


def test_tokenize_request_exceeds_max_runes() -> None:
    with pytest.raises(ValidationError, match="input has"):
        vtok.TokenizeRequest(text="hello", max_input_runes=3).validate()


def test_tokenize_request_negative_max_tokens() -> None:
    with pytest.raises(ValidationError, match="max tokens"):
        vtok.TokenizeRequest(text="hello", max_tokens=-1).validate()


def test_tokenize_request_invalid_mode() -> None:
    with pytest.raises(ValidationError, match="unsupported mode"):
        vtok.TokenizeRequest(text="hello", mode="bogus").validate()


def test_tokenize_request_clone() -> None:
    req = vtok.TokenizeRequest(text="hello", mode=vtok.Mode.PRECISE)
    cloned = req.clone()
    cloned.text = "world"
    assert req.text == "hello"


# --- KeywordsRequest validation -------------------------------------------


def test_keywords_request_valid() -> None:
    req = vtok.KeywordsRequest(text="hello")
    req.validate()


def test_keywords_request_empty_text() -> None:
    with pytest.raises(ValidationError, match="text is required"):
        vtok.KeywordsRequest(text="").validate()


def test_keywords_request_negative_limit() -> None:
    with pytest.raises(ValidationError, match="limit must be"):
        vtok.KeywordsRequest(text="hello", limit=-1).validate()


def test_keywords_request_clone() -> None:
    req = vtok.KeywordsRequest(text="hello", limit=5)
    cloned = req.clone()
    cloned.limit = 10
    assert req.limit == 5


# --- Client with provider -------------------------------------------------


def test_client_tokenize() -> None:
    client = vtok.Client(provider=ExampleProvider())
    response = client.tokenize(vtok.TokenizeRequest(text="南京市长江大桥", mode=vtok.Mode.PRECISE))
    assert len(response.tokens) == 2
    assert response.tokens[0].text == "南京"
    assert response.tokens[1].text == "长江大桥"


def test_client_keywords() -> None:
    client = vtok.Client(provider=ExampleProvider())
    response = client.keywords(vtok.KeywordsRequest(text="南京市长江大桥", limit=2))
    assert len(response.keywords) == 2
    assert response.keywords[0].text == "南京"
    assert response.keywords[0].score == 0.9


def test_client_without_provider_raises() -> None:
    client = vtok.Client()
    with pytest.raises(KniferError, match="missing provider"):
        client.tokenize(vtok.TokenizeRequest(text="hello"))


def test_client_token_limit_exceeded() -> None:
    client = vtok.Client(provider=ExampleProvider())
    with pytest.raises(KniferError, match="provider returned"):
        client.tokenize(vtok.TokenizeRequest(text="南京市长江大桥", max_tokens=1))


def test_client_provider_is_protocol() -> None:
    assert isinstance(ExampleProvider(), vtok.Provider)
