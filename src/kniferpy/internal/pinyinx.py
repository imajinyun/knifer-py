"""Chinese pinyin romanization.

Ports knifer-go's internal/pinyin with Python-idiomatic mappings:

- Go context.Context -> explicit context passing
- Go interface Provider -> Python Protocol
- Go functional options -> keyword arguments
- Go error sentinels -> kniferpy.verr KniferError

Errors use kniferpy.verr types with codes knifer.pinyin.<reason>.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from kniferpy.verr import KniferError

# --- errors --------------------------------------------------------------------


class ErrInvalidConvertRequest(KniferError):
    pass


class ErrInvalidInitialsRequest(KniferError):
    pass


class ErrInputLimitExceeded(KniferError):
    pass


class ErrMissingProvider(KniferError):
    pass


# --- tone style ----------------------------------------------------------------

ToneStyle = str

ToneStyleDefault: ToneStyle = ""
ToneStylePlain: ToneStyle = "plain"
ToneStyleNumber: ToneStyle = "number"
ToneStyleMark: ToneStyle = "mark"

_VALID_TONE_STYLES = frozenset({ToneStyleDefault, ToneStylePlain, ToneStyleNumber, ToneStyleMark})


# --- types ---------------------------------------------------------------------


@dataclass
class Token:
    Text: str = ""
    Syllables: list[str] = field(default_factory=list)
    Metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ConvertRequest:
    Text: str = ""
    Separator: str = ""
    ToneStyle: str = ToneStyleDefault
    Heteronym: bool = False
    MaxInputRunes: int = 0
    Metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        _validate_text(self.Text, self.MaxInputRunes, ErrInvalidConvertRequest)
        if self.ToneStyle not in _VALID_TONE_STYLES:
            raise ErrInvalidConvertRequest(f"unsupported tone style {self.ToneStyle!r}")

    def clone(self) -> ConvertRequest:
        return ConvertRequest(
            Text=self.Text,
            Separator=self.Separator,
            ToneStyle=self.ToneStyle,
            Heteronym=self.Heteronym,
            MaxInputRunes=self.MaxInputRunes,
            Metadata=dict(self.Metadata),
        )


@dataclass
class ConvertResponse:
    Text: str = ""
    Output: str = ""
    Tokens: list[Token] = field(default_factory=list)
    Metadata: dict[str, str] = field(default_factory=dict)

    def clone(self) -> ConvertResponse:
        return ConvertResponse(
            Text=self.Text,
            Output=self.Output,
            Tokens=[
                Token(
                    Text=t.Text,
                    Syllables=list(t.Syllables),
                    Metadata=dict(t.Metadata),
                )
                for t in self.Tokens
            ],
            Metadata=dict(self.Metadata),
        )


@dataclass
class InitialsRequest:
    Text: str = ""
    Separator: str = ""
    MaxInputRunes: int = 0
    Metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        _validate_text(self.Text, self.MaxInputRunes, ErrInvalidInitialsRequest)

    def clone(self) -> InitialsRequest:
        return InitialsRequest(
            Text=self.Text,
            Separator=self.Separator,
            MaxInputRunes=self.MaxInputRunes,
            Metadata=dict(self.Metadata),
        )


@dataclass
class InitialsResponse:
    Text: str = ""
    Output: str = ""
    Initials: list[str] = field(default_factory=list)
    Metadata: dict[str, str] = field(default_factory=dict)

    def clone(self) -> InitialsResponse:
        return InitialsResponse(
            Text=self.Text,
            Output=self.Output,
            Initials=list(self.Initials),
            Metadata=dict(self.Metadata),
        )


# --- validation helpers --------------------------------------------------------


def _validate_text(text: str, max_runes: int, sentinel: type[KniferError]) -> None:
    if not text.strip():
        raise sentinel("text is required")
    if "\x00" in text:
        raise sentinel("text contains nul byte")
    if max_runes < 0:
        raise sentinel("max input runes must be non-negative")
    if max_runes > 0 and len(text) > max_runes:
        raise ErrInputLimitExceeded(f"input has {len(text)} runes, max {max_runes}")


# --- provider interface --------------------------------------------------------


class Provider(Protocol):
    def convert(self, request: ConvertRequest) -> ConvertResponse: ...

    def initials(self, request: InitialsRequest) -> InitialsResponse: ...


# --- client --------------------------------------------------------------------


class Client:
    def __init__(self, provider: Provider | None = None):
        self._provider = provider

    def convert(self, request: ConvertRequest) -> ConvertResponse:
        request.validate()
        if self._provider is None:
            raise ErrMissingProvider("no provider configured")
        response = self._provider.convert(request.clone())
        return response.clone()

    def initials(self, request: InitialsRequest) -> InitialsResponse:
        request.validate()
        if self._provider is None:
            raise ErrMissingProvider("no provider configured")
        response = self._provider.initials(request.clone())
        return response.clone()


def new(provider: Provider | None = None) -> Client:
    return Client(provider=provider)


def convert(provider: Provider, request: ConvertRequest) -> ConvertResponse:
    return new(provider=provider).convert(request)


def initials(provider: Provider, request: InitialsRequest) -> InitialsResponse:
    return new(provider=provider).initials(request)
