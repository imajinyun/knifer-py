from __future__ import annotations

import base64
import binascii
import codecs

# ── Base64 ───────────────────────────────────────────────────────────────────


def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def base64_encode_with_encoding(data: bytes, encoding: object | None = None) -> str:
    if encoding is not None:
        # Support Passing custom base64-like encodings (e.g., base64.urlsafe_b64encode)
        return (
            encoding(data).decode("ascii")
            if callable(encoding)
            else base64.b64encode(data).decode("ascii")
        )
    return base64_encode(data)


def base64_encode_str(value: str) -> str:
    return base64_encode(value.encode("utf-8"))


def base64_decode(value: str) -> bytes:
    return base64_decode_with_encoding(value)


def base64_decode_with_encoding(value: str, encoding: object | None = None) -> bytes:
    try:
        if encoding is not None and callable(encoding):
            raw = base64.b64decode(value)
            return raw
        return base64.b64decode(value, validate=True)
    except binascii.Error as e:
        raise ValueError(f"decode base64: {e}") from e


def base64_decode_str(value: str) -> str:
    return base64_decode(value).decode("utf-8")


def base64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def base64_url_decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value)
    except binascii.Error as e:
        raise ValueError(f"decode url-safe base64: {e}") from e


def base64_raw_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def base64_raw_url_decode(value: str) -> bytes:
    try:
        padding = 4 - len(value) % 4
        if padding != 4:
            value += "=" * padding
        return base64.b64decode(value, altchars=b"-_", validate=True)
    except binascii.Error as e:
        raise ValueError(f"decode raw url-safe base64: {e}") from e


# ── Hex ──────────────────────────────────────────────────────────────────────


def hex_encode(data: bytes) -> str:
    return binascii.hexlify(data).decode("ascii")


def hex_encode_str(value: str) -> str:
    return hex_encode(value.encode("utf-8"))


def hex_decode(value: str) -> bytes:
    try:
        return binascii.unhexlify(value)
    except binascii.Error as e:
        raise ValueError(f"decode hex: {e}") from e


def hex_decode_str(value: str) -> str:
    return hex_decode(value).decode("utf-8")


# ── Base32 ───────────────────────────────────────────────────────────────────


def base32_encode(data: bytes) -> str:
    return base64.b32encode(data).decode("ascii")


def base32_encode_with_encoding(data: bytes, encoding: str) -> str:
    if encoding == "hex":
        return base64.b32hexencode(data).decode("ascii")
    return base32_encode(data)


def base32_decode(value: str) -> bytes:
    return base32_decode_with_encoding(value, "std")


def base32_decode_with_encoding(value: str, encoding: str) -> bytes:
    try:
        padded = value.upper()
        padding = 8 - len(padded) % 8
        if padding != 8:
            padded += "=" * padding
        if encoding == "hex":
            return base64.b32hexdecode(padded)
        return base64.b32decode(padded)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"decode base32: {e}") from e


# ── Base58 ───────────────────────────────────────────────────────────────────

_BASE58_BITCOIN = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_FLICKR = "123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"


def _base58_alphabet_table(alphabet: str) -> str:
    if alphabet == "flickr":
        return _BASE58_FLICKR
    return _BASE58_BITCOIN


def base58_encode(data: bytes) -> str:
    return base58_encode_with_alphabet(data, "bitcoin")


def base58_encode_with_alphabet(data: bytes, alphabet: str) -> str:
    table = _base58_alphabet_table(alphabet)
    n = int.from_bytes(data, "big")
    if n == 0:
        return table[0] * len(data)

    encoded: list[str] = []
    while n > 0:
        n, rem = divmod(n, 58)
        encoded.append(table[rem])

    for b in data:
        if b != 0:
            break
        encoded.append(table[0])

    return "".join(reversed(encoded))


def base58_decode(value: str) -> bytes:
    return base58_decode_with_alphabet(value, "bitcoin")


def base58_decode_with_alphabet(value: str, alphabet: str) -> bytes:
    table = _base58_alphabet_table(alphabet)
    index = {c: i for i, c in enumerate(table)}

    n = 0
    for ch in value:
        if ch not in index:
            raise ValueError("decode base58: invalid alphabet character")
        n = n * 58 + index[ch]

    leading_zeros = 0
    for ch in value:
        if ch != table[0]:
            break
        leading_zeros += 1

    out = n.to_bytes((n.bit_length() + 7) // 8, "big") if n > 0 else b""
    return b"\x00" * leading_zeros + out


# ── Base62 ───────────────────────────────────────────────────────────────────

_BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def base62_encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    if n == 0:
        return _BASE62_ALPHABET[0] * len(data)

    encoded: list[str] = []
    while n > 0:
        n, rem = divmod(n, 62)
        encoded.append(_BASE62_ALPHABET[rem])

    for b in data:
        if b != 0:
            break
        encoded.append(_BASE62_ALPHABET[0])

    return "".join(reversed(encoded))


def base62_decode(value: str) -> bytes:
    index = {c: i for i, c in enumerate(_BASE62_ALPHABET)}

    n = 0
    for ch in value:
        if ch not in index:
            raise ValueError("decode base62: invalid alphabet character")
        n = n * 62 + index[ch]

    leading_zeros = 0
    for ch in value:
        if ch != _BASE62_ALPHABET[0]:
            break
        leading_zeros += 1

    out = n.to_bytes((n.bit_length() + 7) // 8, "big") if n > 0 else b""
    return b"\x00" * leading_zeros + out


# ── Morse ────────────────────────────────────────────────────────────────────

_MORSE_TABLE: dict[str, str] = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "'": ".----.",
    "!": "-.-.--",
    "/": "-..-.",
    "(": "-.--.",
    ")": "-.--.-",
    "&": ".-...",
    ":": "---...",
    ";": "-.-.-.",
    "=": "-...-",
    "+": ".-.-.",
    "-": "-....-",
    "_": "..--.-",
    '"': ".-..-.",
    "$": "...-..-",
    "@": ".--.-.",
}

_REVERSE_MORSE: dict[str, str] = {v: k for k, v in _MORSE_TABLE.items()}


def morse_encode(value: str) -> str:
    words = value.split()
    encoded_words: list[str] = []
    for word in words:
        codes: list[str] = []
        for ch in word:
            upper = ch.upper()
            if upper not in _MORSE_TABLE:
                raise ValueError("encode morse: invalid alphabet character")
            codes.append(_MORSE_TABLE[upper])
        encoded_words.append(" ".join(codes))
    return " / ".join(encoded_words)


def morse_decode(value: str) -> str:
    if not value.strip():
        return ""
    words = value.split("/")
    decoded_words: list[str] = []
    for word in words:
        letters = word.split()
        decoded: list[str] = []
        for letter in letters:
            if letter not in _REVERSE_MORSE:
                raise ValueError("decode morse: invalid alphabet character")
            decoded.append(_REVERSE_MORSE[letter])
        decoded_words.append("".join(decoded))
    return " ".join(decoded_words)


# ── ROT ──────────────────────────────────────────────────────────────────────


def rot13(value: str) -> str:
    return codecs.encode(value, "rot_13")


def rot47(value: str) -> str:
    result: list[str] = []
    for ch in value:
        cp = ord(ch)
        if 33 <= cp <= 126:
            result.append(chr(33 + ((cp - 33) + 47) % 94))
        else:
            result.append(ch)
    return "".join(result)


def rotn(value: str, n: int) -> str:
    n %= 26
    if n < 0:
        n += 26
    result: list[str] = []
    for ch in value:
        if "a" <= ch <= "z":
            result.append(chr(ord("a") + (ord(ch) - ord("a") + n) % 26))
        elif "A" <= ch <= "Z":
            result.append(chr(ord("A") + (ord(ch) - ord("A") + n) % 26))
        else:
            result.append(ch)
    return "".join(result)
