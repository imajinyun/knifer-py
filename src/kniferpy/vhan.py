"""Chinese pinyin romanization.

Thin facade over kniferpy.internal.pinyinx, porting knifer-go's vhan surface.

Provides a provider-neutral pinyin client that converts Chinese text to
pinyin and extracts initials.
"""

from __future__ import annotations

from kniferpy.internal.pinyinx import (
    Client,
    ConvertRequest,
    ConvertResponse,
    ErrInputLimitExceeded,
    ErrInvalidConvertRequest,
    ErrInvalidInitialsRequest,
    ErrMissingProvider,
    InitialsRequest,
    InitialsResponse,
    Provider,
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

__all__ = [
    "Client",
    "ConvertRequest",
    "ConvertResponse",
    "ErrInputLimitExceeded",
    "ErrInvalidConvertRequest",
    "ErrInvalidInitialsRequest",
    "ErrMissingProvider",
    "InitialsRequest",
    "InitialsResponse",
    "Provider",
    "Token",
    "ToneStyle",
    "ToneStyleDefault",
    "ToneStyleMark",
    "ToneStyleNumber",
    "ToneStylePlain",
    "convert",
    "initials",
    "new",
]