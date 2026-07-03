import pytest

from kniferpy.vhan import (
    Client,
    ConvertRequest,
    ConvertResponse,
    ErrInputLimitExceeded,
    ErrInvalidConvertRequest,
    ErrInvalidInitialsRequest,
    ErrMissingProvider,
    InitialsRequest,
    InitialsResponse,
    Token,
    ToneStyle,
    ToneStyleDefault,
    ToneStyleMark,
    ToneStyleNumber,
    ToneStylePlain,
    convert,
    initials,
    new,
)


class _Provider:
    def __init__(self, convert_resp=None, convert_err=None, initials_resp=None, initials_err=None):
        self._convert_resp = convert_resp
        self._convert_err = convert_err
        self._initials_resp = initials_resp
        self._initials_err = initials_err
        self.last_convert: ConvertRequest | None = None
        self.last_initials: InitialsRequest | None = None

    def convert(self, request: ConvertRequest) -> ConvertResponse:
        self.last_convert = request
        if self._convert_err:
            raise self._convert_err
        if self._convert_resp:
            return self._convert_resp
        return ConvertResponse(Text=request.Text, Output="zhong guo")

    def initials(self, request: InitialsRequest) -> InitialsResponse:
        self.last_initials = request
        if self._initials_err:
            raise self._initials_err
        if self._initials_resp:
            return self._initials_resp
        return InitialsResponse(Text=request.Text, Output="zg", Initials=["z", "g"])


# --- ToneStyle constants -------------------------------------------------------


def test_tone_style_constants():
    assert ToneStyleDefault == ""
    assert ToneStylePlain == "plain"
    assert ToneStyleNumber == "number"
    assert ToneStyleMark == "mark"


# --- ConvertRequest validation -------------------------------------------------


def test_convert_request_valid():
    r = ConvertRequest(Text="中国")
    r.validate()


def test_convert_request_empty_text():
    r = ConvertRequest(Text="  ")
    with pytest.raises(ErrInvalidConvertRequest, match="text is required"):
        r.validate()


def test_convert_request_default_text():
    r = ConvertRequest()
    with pytest.raises(ErrInvalidConvertRequest, match="text is required"):
        r.validate()


def test_convert_request_nul_byte():
    r = ConvertRequest(Text="hello\x00world")
    with pytest.raises(ErrInvalidConvertRequest, match="nul byte"):
        r.validate()


def test_convert_request_negative_max_runes():
    r = ConvertRequest(Text="中国", MaxInputRunes=-1)
    with pytest.raises(ErrInvalidConvertRequest, match="non-negative"):
        r.validate()


def test_convert_request_exceeded_max_runes():
    r = ConvertRequest(Text="中国", MaxInputRunes=1)
    with pytest.raises(ErrInputLimitExceeded, match="max 1"):
        r.validate()


def test_convert_request_bad_tone_style():
    r = ConvertRequest(Text="中国", ToneStyle=ToneStyle("bad"))
    with pytest.raises(ErrInvalidConvertRequest, match="unsupported tone style"):
        r.validate()


def test_convert_request_valid_tone_styles():
    for style in [ToneStyleDefault, ToneStylePlain, ToneStyleNumber, ToneStyleMark]:
        r = ConvertRequest(Text="中国", ToneStyle=style)
        r.validate()


# --- ConvertRequest clone ------------------------------------------------------


def test_convert_request_clone_independent():
    r = ConvertRequest(
        Text="中国",
        Separator=" ",
        ToneStyle=ToneStyleNumber,
        Heteronym=True,
        MaxInputRunes=10,
        Metadata={"k": "v"},
    )
    c = r.clone()
    c.Text = "changed"
    c.Metadata["k"] = "changed"
    assert r.Text == "中国"
    assert r.Metadata["k"] == "v"


# --- InitialsRequest validation ------------------------------------------------


def test_initials_request_valid():
    r = InitialsRequest(Text="中国")
    r.validate()


def test_initials_request_empty_text():
    r = InitialsRequest(Text="  ")
    with pytest.raises(ErrInvalidInitialsRequest, match="text is required"):
        r.validate()


def test_initials_request_nul_byte():
    r = InitialsRequest(Text="a\x00b")
    with pytest.raises(ErrInvalidInitialsRequest, match="nul byte"):
        r.validate()


def test_initials_request_exceeded_max_runes():
    r = InitialsRequest(Text="中国", MaxInputRunes=1)
    with pytest.raises(ErrInputLimitExceeded, match="max 1"):
        r.validate()


# --- InitialsRequest clone -----------------------------------------------------


def test_initials_request_clone_independent():
    r = InitialsRequest(Text="中国", Separator="", MaxInputRunes=10, Metadata={"k": "v"})
    c = r.clone()
    c.Text = "changed"
    c.Metadata["k"] = "changed"
    assert r.Text == "中国"
    assert r.Metadata["k"] == "v"


# --- Client.convert ------------------------------------------------------------


def test_client_convert_success():
    provider = _Provider()
    client = new(provider=provider)
    result = client.convert(ConvertRequest(Text="中国"))
    assert result.Output == "zhong guo"


def test_client_convert_validation_error():
    client = new(provider=_Provider())
    with pytest.raises(ErrInvalidConvertRequest):
        client.convert(ConvertRequest())


def test_client_convert_missing_provider():
    client = new()
    with pytest.raises(ErrMissingProvider):
        client.convert(ConvertRequest(Text="中国"))


def test_client_convert_clones_request():
    provider = _Provider()
    r = ConvertRequest(Text="中国")
    client = new(provider=provider)
    client.convert(r)
    assert provider.last_convert is not None
    assert provider.last_convert is not r


def test_client_convert_clones_response():
    provider = _Provider()
    client = new(provider=provider)
    result = client.convert(ConvertRequest(Text="中国"))
    result.Output = "mutated"
    assert provider._convert_resp is None  # default response was used


# --- Client.initials -----------------------------------------------------------


def test_client_initials_success():
    provider = _Provider()
    client = new(provider=provider)
    result = client.initials(InitialsRequest(Text="中国"))
    assert result.Output == "zg"
    assert result.Initials == ["z", "g"]


def test_client_initials_validation_error():
    client = new(provider=_Provider())
    with pytest.raises(ErrInvalidInitialsRequest):
        client.initials(InitialsRequest())


def test_client_initials_missing_provider():
    client = new()
    with pytest.raises(ErrMissingProvider):
        client.initials(InitialsRequest(Text="中国"))


def test_client_initials_clones_request():
    provider = _Provider()
    r = InitialsRequest(Text="中国")
    client = new(provider=provider)
    client.initials(r)
    assert provider.last_initials is not None
    assert provider.last_initials is not r


def test_client_initials_clones_response():
    provider = _Provider()
    client = new(provider=provider)
    result = client.initials(InitialsRequest(Text="中国"))
    result.Initials.append("mutated")
    assert provider._initials_resp is None


# --- short-lived convenience functions -----------------------------------------


def test_convert_shortcut():
    provider = _Provider()
    result = convert(provider, ConvertRequest(Text="中国"))
    assert result.Output == "zhong guo"


def test_initials_shortcut():
    provider = _Provider()
    result = initials(provider, InitialsRequest(Text="中国"))
    assert result.Output == "zg"


# --- Error sentinel exposure ---------------------------------------------------


def test_convert_missing_provider_shortcut():
    with pytest.raises(ErrMissingProvider):
        convert(None, ConvertRequest(Text="中国"))


def test_initials_missing_provider_shortcut():
    with pytest.raises(ErrMissingProvider):
        initials(None, InitialsRequest(Text="中国"))


# --- Token dataclass -----------------------------------------------------------


def test_token_defaults():
    t = Token()
    assert t.Text == ""
    assert t.Syllables == []
    assert t.Metadata == {}


# --- ConvertResponse clone -----------------------------------------------------


def test_convert_response_clone_independent():
    r = ConvertResponse(
        Text="中国",
        Output="zhong guo",
        Tokens=[Token(Text="中国", Syllables=["zhong", "guo"])],
        Metadata={"k": "v"},
    )
    c = r.clone()
    c.Tokens[0].Syllables.append("extra")
    assert r.Tokens[0].Syllables == ["zhong", "guo"]
    c.Metadata["k"] = "changed"
    assert r.Metadata["k"] == "v"


# --- InitialsResponse clone ----------------------------------------------------


def test_initials_response_clone_independent():
    r = InitialsResponse(Text="中国", Output="zg", Initials=["z", "g"])
    c = r.clone()
    c.Initials.append("x")
    assert r.Initials == ["z", "g"]


# --- ToneStyle validation (all styles) -----------------------------------------


def test_all_tone_styles_valid():
    for style in [ToneStyleDefault, ToneStylePlain, ToneStyleNumber, ToneStyleMark]:
        ConvertRequest(Text="中国", ToneStyle=style).validate()