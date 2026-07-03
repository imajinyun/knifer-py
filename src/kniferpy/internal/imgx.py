"""Image manipulation, captcha, QR/barcode helpers.

Ports knifer-go's internal/imgx with Python-idiomatic mappings:

- Go image.Image -> PIL.Image.Image
- Go io.Reader/Writer -> bytes/bytes-like objects
- Go functional options -> callable configurators

Errors use kniferpy.verr types with codes knifer.imgx.<reason>.
"""

from __future__ import annotations

import base64
import copy
import io
import math
import os
import random
import secrets
import string
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Optional, Sequence

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

from kniferpy.verr import KniferError

# --- constants ----------------------------------------------------------------

FONT_WIDTH = 5
FONT_HEIGHT = 7
_SUPPORTED_FORMATS = frozenset({"png", "jpeg", "gif"})

# 5x7 bitmap font glyphs (matching Go font.go)
_GLYPHS: dict[int, list[int]] = {
    ord(" "): [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    ord("+"): [0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00],
    ord("-"): [0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00],
    ord("*"): [0x00, 0x0A, 0x04, 0x1F, 0x04, 0x0A, 0x00],
    ord("="): [0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00],
    ord("?"): [0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04],
    ord("."): [0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x06],
    ord("0"): [0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E],
    ord("1"): [0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E],
    ord("2"): [0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F],
    ord("3"): [0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E],
    ord("4"): [0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02],
    ord("5"): [0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E],
    ord("6"): [0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E],
    ord("7"): [0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08],
    ord("8"): [0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E],
    ord("9"): [0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C],
    ord("A"): [0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
    ord("B"): [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E],
    ord("C"): [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E],
    ord("D"): [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E],
    ord("E"): [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F],
    ord("F"): [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10],
    ord("G"): [0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F],
    ord("H"): [0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
    ord("I"): [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E],
    ord("J"): [0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C],
    ord("K"): [0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11],
    ord("L"): [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F],
    ord("M"): [0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11],
    ord("N"): [0x11, 0x11, 0x19, 0x15, 0x13, 0x11, 0x11],
    ord("O"): [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    ord("P"): [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10],
    ord("Q"): [0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D],
    ord("R"): [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11],
    ord("S"): [0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E],
    ord("T"): [0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04],
    ord("U"): [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    ord("V"): [0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04],
    ord("W"): [0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A],
    ord("X"): [0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11],
    ord("Y"): [0x11, 0x11, 0x11, 0x0A, 0x04, 0x04, 0x04],
    ord("Z"): [0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F],
}


def _get_glyph(ch: int) -> list[int]:
    if ord("a") <= ch <= ord("z"):
        ch = ch - ord("a") + ord("A")
    return _GLYPHS.get(ch, _GLYPHS[ord("?")])


# --- errors -------------------------------------------------------------------


class ErrImageInvalidInput(KniferError):
    pass


class ErrImageUnsupported(KniferError):
    pass


class ErrImageInternal(KniferError):
    pass


# --- helpers ------------------------------------------------------------------


def _normalize_format(fmt: str) -> str:
    normalized = fmt.strip().lower()
    if normalized == "jpg":
        normalized = "jpeg"
    if normalized not in _SUPPORTED_FORMATS:
        raise ErrImageUnsupported(f"image: unsupported format {fmt!r}")
    return normalized


def _decode_any(data: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception as e:
        raise ErrImageInvalidInput("image: decode failed") from e


def _decode_config_any(data: bytes) -> tuple[int, int, str]:
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format.lower() if img.format else "png"
        return img.width, img.height, fmt
    except Exception as e:
        raise ErrImageInvalidInput("image: decode config failed") from e


def _encode_any(img: Image.Image, fmt: str) -> bytes:
    buf = io.BytesIO()
    try:
        save_fmt = "JPEG" if fmt == "jpeg" else fmt.upper()
        if fmt == "jpeg" and img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            bg.save(buf, format=save_fmt)
        else:
            img.save(buf, format=save_fmt)
    except Exception as e:
        raise ErrImageInternal(f"image: {fmt} encode failed") from e
    return buf.getvalue()


def _fit_long_edge(width: int, height: int, max_edge: int) -> tuple[int, int]:
    if width >= height:
        new_w = max_edge
        new_h = max((height * new_w) // width, 1)
        return new_w, new_h
    new_h = max_edge
    new_w = max((width * new_h) // height, 1)
    return new_w, new_h


def _blend_color(
    base: tuple[int, int, int, int], overlay: tuple[int, int, int, int], opacity: float
) -> tuple[int, int, int, int]:
    oa = overlay[3] * opacity
    inv = 1.0 - oa / 255.0
    return (
        int(base[0] * inv + overlay[0] * oa / 255.0 + 0.5),
        int(base[1] * inv + overlay[1] * oa / 255.0 + 0.5),
        int(base[2] * inv + overlay[2] * oa / 255.0 + 0.5),
        int(base[3] * inv + 255 * oa / 255.0 + 0.5),
    )


# --- image operations ---------------------------------------------------------


def thumbnail(data: bytes, max_edge: int, fmt: str) -> bytes:
    if max_edge <= 0:
        raise ErrImageInvalidInput("image: maxEdge must be positive")
    normalized = _normalize_format(fmt)
    img = _decode_any(data)
    w, h = img.size
    if w == 0 or h == 0:
        raise ErrImageInvalidInput("image: empty source image")
    if w > max_edge or h > max_edge:
        new_w, new_h = _fit_long_edge(w, h, max_edge)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return _encode_any(img, normalized)


def convert_format(data: bytes, fmt: str) -> bytes:
    normalized = _normalize_format(fmt)
    img = _decode_any(data)
    return _encode_any(img, normalized)


def info(data: bytes) -> tuple[int, int, str]:
    return _decode_config_any(data)


def resize(img: Image.Image, width: int, height: int) -> Image.Image:
    if width <= 0 or height <= 0:
        raise ErrImageInvalidInput("image: resize dimensions must be positive")
    if img.width == 0 or img.height == 0:
        raise ErrImageInvalidInput("image: empty source image")
    return img.resize((width, height), Image.Resampling.NEAREST)


def crop(img: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
    if width <= 0 or height <= 0:
        raise ErrImageInvalidInput("image: crop dimensions must be positive")
    if x < 0 or y < 0 or x + width > img.width or y + height > img.height:
        raise ErrImageInvalidInput("image: crop rectangle outside image bounds")
    return img.crop((x, y, x + width, y + height))


def crop_center(img: Image.Image, width: int, height: int) -> Image.Image:
    x = (img.width - width) // 2
    y = (img.height - height) // 2
    return crop(img, x, y, width, height)


def flip_horizontal(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def flip_vertical(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def rotate_90(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.ROTATE_270)


def rotate_180(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.ROTATE_180)


def rotate_270(img: Image.Image) -> Image.Image:
    return img.transpose(Image.Transpose.ROTATE_90)


def rotate(img: Image.Image, angle: float, background: tuple[int, int, int, int]) -> Image.Image:
    if math.isnan(angle) or math.isinf(angle):
        raise ErrImageInvalidInput("image: rotate angle must be finite")
    if img.width == 0 or img.height == 0:
        raise ErrImageInvalidInput("image: empty source image")

    normalized = angle % 360
    if normalized < 0:
        normalized += 360

    if abs(normalized) < 1e-9 or abs(normalized - 360) < 1e-9:
        return img.copy()
    if abs(normalized - 90) < 1e-9:
        return rotate_90(img)
    if abs(normalized - 180) < 1e-9:
        return rotate_180(img)
    if abs(normalized - 270) < 1e-9:
        return rotate_270(img)

    return img.rotate(-normalized, expand=True, fillcolor=background, resample=Image.Resampling.NEAREST)


def grayscale(img: Image.Image) -> Image.Image:
    if img.mode == "RGBA":
        r, g, b, a = img.split()
        gray = Image.merge("RGB", (r, g, b)).convert("L")
        return Image.merge("RGBA", (gray, gray, gray, a))
    return img.convert("LA" if img.mode == "RGBA" else "L").convert(img.mode)


def compress_jpeg(img: Image.Image, quality: int) -> bytes:
    if quality < 1 or quality > 100:
        raise ErrImageInvalidInput("image: jpeg quality must be between 1 and 100")
    buf = io.BytesIO()
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        bg.save(buf, format="JPEG", quality=quality)
    else:
        img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _normalize_pixel(px: float | tuple[int, ...] | None) -> tuple[int, int, int, int]:
    if px is None:
        return (0, 0, 0, 255)
    if isinstance(px, (int, float)):
        v = int(px)
        return (v, v, v, 255)
    if len(px) == 3:
        return (int(px[0]), int(px[1]), int(px[2]), 255)
    return (int(px[0]), int(px[1]), int(px[2]), int(px[3]))


def add_watermark(
    img: Image.Image, watermark: Image.Image, x: int, y: int, opacity: float
) -> Image.Image:
    if opacity < 0 or opacity > 1 or math.isnan(opacity):
        raise ErrImageInvalidInput("image: watermark opacity must be between 0 and 1")
    dst = img.copy()
    wm = watermark.convert("RGBA")
    w, h = wm.size
    for wy in range(h):
        for wx in range(w):
            dx, dy = x + wx, y + wy
            if dx < 0 or dy < 0 or dx >= dst.width or dy >= dst.height:
                continue
            base_px = _normalize_pixel(dst.getpixel((dx, dy)))
            overlay_px = _normalize_pixel(wm.getpixel((wx, wy)))
            dst.putpixel((dx, dy), _blend_color(base_px, overlay_px, opacity))
    return dst


def add_text_watermark(
    img: Image.Image,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int, int],
    scale: int,
    opacity: float,
) -> Image.Image:
    if not text:
        raise ErrImageInvalidInput("image: empty watermark text")
    if scale <= 0:
        raise ErrImageInvalidInput("image: text watermark scale must be positive")
    if opacity < 0 or opacity > 1 or math.isnan(opacity):
        raise ErrImageInvalidInput("image: text watermark opacity must be between 0 and 1")

    dst = img.copy()
    char_w = FONT_WIDTH * scale + scale
    for i, ch in enumerate(text.encode("ascii", errors="replace")):
        _draw_watermark_char(dst, ch, x + i * char_w, y, scale, color, opacity)
    return dst


def _draw_watermark_char(
    img: Image.Image,
    ch: int,
    x: int,
    y: int,
    scale: int,
    color: tuple[int, int, int, int],
    opacity: float,
) -> None:
    glyph = _get_glyph(ch)
    for row in range(FONT_HEIGHT):
        for col in range(FONT_WIDTH):
            if glyph[row] & (1 << (FONT_WIDTH - 1 - col)) == 0:
                continue
            for sy in range(scale):
                for sx in range(scale):
                    px, py = x + col * scale + sx, y + row * scale + sy
                    if 0 <= px < img.width and 0 <= py < img.height:
                        base_px = _normalize_pixel(img.getpixel((px, py)))
                        img.putpixel((px, py), _blend_color(base_px, color, opacity))


# --- captcha ------------------------------------------------------------------

BASE_CHAR_NUMBER_UC = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
MATH_OPERATORS = "+-*"


class CodeGenerator:
    def gen(self) -> str:
        raise NotImplementedError

    def verify(self, code: str, user_input: str) -> bool:
        raise NotImplementedError


class RandomGenerator(CodeGenerator):
    def __init__(self, base: str = BASE_CHAR_NUMBER_UC, length: int = 5) -> None:
        self.base = base
        self.length = max(length, 4)

    def gen(self) -> str:
        return "".join(secrets.choice(self.base) for _ in range(self.length))

    def verify(self, code: str, user_input: str) -> bool:
        if not user_input.strip():
            return False
        return code.strip().lower() == user_input.strip().lower()


class MathGenerator(CodeGenerator):
    def __init__(
        self,
        number_length: int = 2,
        result_has_negative: bool = True,
    ) -> None:
        self.number_length = max(number_length, 1)
        self.result_has_negative = result_has_negative

    def _limit(self) -> int:
        return int(10**self.number_length)

    def gen(self) -> str:
        limit = self._limit()
        op = random.choice(MATH_OPERATORS)
        a = secrets.randbelow(limit)
        if not self.result_has_negative and op == "-":
            b = secrets.randbelow(a + 1) if a > 0 else 0
        else:
            b = secrets.randbelow(limit)
        n1 = str(a).ljust(self.number_length)
        n2 = str(b).ljust(self.number_length)
        return f"{n1}{op}{n2}="

    def verify(self, code: str, user_input: str) -> bool:
        try:
            got = int(user_input.strip())
        except (ValueError, TypeError):
            return False
        expected = self._eval_expr(code)
        return expected is not None and got == expected

    @staticmethod
    def _eval_expr(expr: str) -> int | None:
        s = expr.strip().rstrip("=").strip()
        for op in "+-*":
            idx = s.find(op)
            if idx > 0:
                try:
                    a = int(s[:idx].strip())
                    b = int(s[idx + 1 :].strip())
                except (ValueError, TypeError):
                    return None
                if op == "+":
                    return a + b
                if op == "-":
                    return a - b
                return a * b
        return None


def verify_ignore_case(code: str, user_input: str) -> bool:
    return code.strip().lower() == user_input.strip().lower()


# --- captcha options ----------------------------------------------------------

CaptchaOption = Callable[["_CaptchaConfig"], None]
WriteOption = Callable[["_WriteConfig"], None]
GeneratorOption = Callable[["_GeneratorConfig"], None]


class _CaptchaConfig:
    def __init__(self) -> None:
        self.generator: CodeGenerator | None = None
        self.background: tuple[int, int, int, int] | None = None
        self.font_size: float = 0.0
        self.interfere_count: int = 0
        self.set_interfere: bool = False
        self.gif_repeat: int = 0
        self.set_gif_repeat: bool = False
        self.gif_delay: int = 10
        self.set_gif_delay: bool = False
        self.random_int: Callable[[int], int] | None = None
        self.color_func: Callable[[], tuple[int, int, int]] | None = None


class _WriteConfig:
    def __init__(self) -> None:
        self.file_perm: int = 0o644
        self.dir_perm: int = 0o750
        self.overwrite: bool = True
        self.create_parents: bool = True


class _GeneratorConfig:
    def __init__(self) -> None:
        self.random_int: Callable[[int], int] = lambda m: secrets.randbelow(m) if m > 0 else 0
        self.parse_int: Callable[[str], int] = int


def with_generator(generator: CodeGenerator) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.generator = generator

    return _apply


def with_background(background: tuple[int, int, int, int]) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.background = background

    return _apply


def with_font_size(font_size: float) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.font_size = font_size

    return _apply


def with_interfere_count(count: int) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.interfere_count = count
        c.set_interfere = True

    return _apply


def with_gif_repeat(repeat: int) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.gif_repeat = repeat
        c.set_gif_repeat = True

    return _apply


def with_gif_delay(delay: int) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.gif_delay = delay
        c.set_gif_delay = True

    return _apply


def with_random_int(random_int: Callable[[int], int]) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.random_int = random_int

    return _apply


def with_color_func(color_func: Callable[[], tuple[int, int, int]]) -> CaptchaOption:
    def _apply(c: _CaptchaConfig) -> None:
        c.color_func = color_func

    return _apply


def with_file_perm(perm: int) -> WriteOption:
    def _apply(c: _WriteConfig) -> None:
        c.file_perm = perm

    return _apply


def with_dir_perm(perm: int) -> WriteOption:
    def _apply(c: _WriteConfig) -> None:
        c.dir_perm = perm

    return _apply


def with_overwrite(overwrite: bool) -> WriteOption:
    def _apply(c: _WriteConfig) -> None:
        c.overwrite = overwrite

    return _apply


def with_create_parents(create: bool) -> WriteOption:
    def _apply(c: _WriteConfig) -> None:
        c.create_parents = create

    return _apply


def with_generator_random_int(random_int: Callable[[int], int]) -> GeneratorOption:
    def _apply(c: _GeneratorConfig) -> None:
        if random_int is not None:
            c.random_int = random_int

    return _apply


def with_generator_int_parser(parser: Callable[[str], int]) -> GeneratorOption:
    def _apply(c: _GeneratorConfig) -> None:
        if parser is not None:
            c.parse_int = parser

    return _apply


# --- abstract captcha ---------------------------------------------------------


class AbstractCaptcha:
    def __init__(self) -> None:
        self.width: int = 160
        self.height: int = 60
        self.interfere_count: int = 0
        self.font_size: float = 0.75
        self.background: tuple[int, int, int, int] | None = None
        self._generator: CodeGenerator | None = None
        self._random_int: Callable[[int], int] | None = None
        self._color_func: Callable[[], tuple[int, int, int]] | None = None
        self._code: str = ""
        self._img_bytes: bytes | None = None

    @property
    def code(self) -> str:
        if not self._code:
            self.create_code()
        return self._code

    def verify(self, user_input: str) -> bool:
        return self._ensure_generator().verify(self.code, user_input)

    def image_bytes(self) -> bytes:
        if self._img_bytes is None:
            self.create_code()
        return self._img_bytes or b""

    def image_base64(self) -> str:
        return base64.b64encode(self.image_bytes()).decode()

    def image_base64_data(self) -> str:
        return "data:image/png;base64," + self.image_base64()

    def write(self, w: io.IOBase) -> None:
        b = self.image_bytes()
        if not b:
            raise ErrImageInvalidInput("captcha: empty image, call create_code first")
        w.write(b)

    def write_to_file(self, path: str, opts: Sequence[WriteOption] | None = None) -> None:
        b = self.image_bytes()
        if not b:
            raise ErrImageInvalidInput("captcha: empty image, call create_code first")
        cfg = _apply_write_options(opts or [])
        if cfg.create_parents:
            os.makedirs(os.path.dirname(os.path.abspath(path)), cfg.dir_perm, exist_ok=True)
        flag = "wb" if cfg.overwrite else "xb"
        try:
            with open(path, flag) as f:
                f.write(b)
            os.chmod(path, cfg.file_perm)
        except FileExistsError:
            raise ErrImageInvalidInput("captcha: file already exists") from None

    def create_code(self) -> None:
        raise NotImplementedError

    def _ensure_generator(self) -> CodeGenerator:
        if self._generator is None:
            self._generator = RandomGenerator(length=5)
        return self._generator

    def _bg(self) -> tuple[int, int, int, int]:
        return self.background or (255, 255, 255, 255)

    def _rand_int(self, max_val: int) -> int:
        if max_val <= 0:
            return 0
        if self._random_int is not None:
            v = self._random_int(max_val)
            if v < 0:
                return 0
            if v >= max_val:
                return v % max_val
            return v
        return secrets.randbelow(max_val) if max_val > 0 else 0

    def _rand_int_range(self, min_val: int, max_val: int) -> int:
        if max_val <= min_val:
            return min_val
        return min_val + self._rand_int(max_val - min_val)

    def _rand_color(self) -> tuple[int, int, int]:
        if self._color_func is not None:
            return self._color_func()
        return (
            secrets.randbelow(256),
            secrets.randbelow(256),
            secrets.randbelow(256),
        )

    def _generate_code(self) -> None:
        self._code = self._ensure_generator().gen()

    def _set_image_bytes(self, b: bytes) -> None:
        self._img_bytes = b

    def _apply_options(self, opts: Sequence[CaptchaOption]) -> _CaptchaConfig:
        cfg = _CaptchaConfig()
        for opt in opts or []:
            if opt is not None:
                opt(cfg)
        if cfg.generator is not None:
            self._generator = cfg.generator
            self._code = ""
            self._img_bytes = None
        if cfg.background is not None:
            self.background = cfg.background
        if cfg.font_size > 0:
            self.font_size = cfg.font_size
        if cfg.set_interfere:
            self.interfere_count = cfg.interfere_count
        if cfg.random_int is not None:
            self._random_int = cfg.random_int
        if cfg.color_func is not None:
            self._color_func = cfg.color_func
        return cfg


def _apply_write_options(opts: Sequence[WriteOption]) -> _WriteConfig:
    cfg = _WriteConfig()
    for opt in opts or []:
        if opt is not None:
            opt(cfg)
    return cfg


def _apply_generator_options(opts: Sequence[GeneratorOption]) -> _GeneratorConfig:
    cfg = _GeneratorConfig()
    for opt in opts or []:
        if opt is not None:
            opt(cfg)
    return cfg


# --- draw helpers -------------------------------------------------------------


def _draw_char(
    img: Image.Image,
    ch: int,
    x: int,
    y: int,
    scale: int,
    color: tuple[int, int, int],
) -> None:
    glyph = _get_glyph(ch)
    for row in range(FONT_HEIGHT):
        for col in range(FONT_WIDTH):
            if glyph[row] & (1 << (FONT_WIDTH - 1 - col)) != 0:
                for sy in range(scale):
                    for sx in range(scale):
                        px, py = x + col * scale + sx, y + row * scale + sy
                        if 0 <= px < img.width and 0 <= py < img.height:
                            img.putpixel((px, py), color)


def _draw_string(
    img: Image.Image,
    code: str,
    w: int,
    h: int,
    scale: int,
    color_func: Callable[[], tuple[int, int, int]],
) -> None:
    char_w = FONT_WIDTH * scale + scale
    total_w = char_w * len(code)
    start_x = (w - total_w) // 2
    char_h = FONT_HEIGHT * scale
    start_y = (h - char_h) // 2
    for i, ch in enumerate(code.encode("ascii", errors="replace")):
        c = color_func()
        _draw_char(img, ch, start_x + i * char_w, start_y, scale, c)


def _compute_scale(height: int) -> int:
    return max(height // (FONT_HEIGHT + 4), 1)


def _draw_line(
    img: Image.Image,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
) -> None:
    # Bresenham's algorithm
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        if 0 <= x0 < img.width and 0 <= y0 < img.height:
            img.putpixel((x0, y0), color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def _draw_oval(
    img: Image.Image,
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    color: tuple[int, int, int],
) -> None:
    if rx <= 0 or ry <= 0:
        return
    steps = max(2 * max(rx, ry), 20)
    for i in range(steps):
        angle = 2 * math.pi * i / steps
        px = cx + int(rx * math.cos(angle))
        py = cy + int(ry * math.sin(angle))
        if 0 <= px < img.width and 0 <= py < img.height:
            img.putpixel((px, py), color)


def _draw_thick_line(
    img: Image.Image,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    thickness: int,
    color: tuple[int, int, int],
) -> None:
    dx = float(x2 - x1)
    dy = float(y2 - y1)
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return
    scale = thickness / (2 * length)
    ddx = -scale * dy
    ddy = scale * dx
    xp = [x1 + int(ddx), x1 - int(ddx), x2 - int(ddx), x2 + int(ddx)]
    yp = [y1 + int(ddy), y1 - int(ddy), y2 - int(ddy), y2 + int(ddy)]
    _fill_polygon(img, xp, yp, color)


def _fill_polygon(
    img: Image.Image,
    xp: list[int],
    yp: list[int],
    color: tuple[int, int, int],
) -> None:
    if len(xp) < 3:
        return
    min_y = min(yp)
    max_y = max(yp)
    n = len(xp)
    for y in range(min_y, max_y + 1):
        node_x: list[int] = []
        j = n - 1
        for i_inner in range(n):
            if (yp[i_inner] < y <= yp[j]) or (yp[j] < y <= yp[i_inner]):
                node_x.append(
                    xp[i_inner]
                    + int(float(y - yp[i_inner]) / float(yp[j] - yp[i_inner]) * float(xp[j] - xp[i_inner]))
                )
            j = i_inner
        node_x.sort()
        for i_inner in range(0, len(node_x) - 1, 2):
            for x in range(node_x[i_inner], node_x[i_inner + 1] + 1):
                if 0 <= x < img.width and 0 <= y < img.height:
                    img.putpixel((x, y), color)


def _shear_x(img: Image.Image, bg: tuple[int, int, int, int], period: int) -> None:
    w = img.width
    h = img.height
    if period <= 0:
        period = w
    for y in range(h):
        d = int((period // 2) * math.sin(y / period + 2 * math.pi * 0.5))
        for x in range(w - 1, -1, -1):
            src_x = x - d
            if 0 <= src_x < w:
                px = _normalize_pixel(img.getpixel((src_x, y)))
                img.putpixel((x, y), px[:3])
            else:
                img.putpixel((x, y), bg[:3])


def _shear_y(img: Image.Image, bg: tuple[int, int, int, int], period: int) -> None:
    w = img.width
    h = img.height
    if period <= 0:
        period = h
    for x in range(w):
        d = int((period // 2) * math.sin(x / period + 2 * math.pi * 7.0 / 20.0))
        for y in range(h - 1, -1, -1):
            src_y = y - d
            if 0 <= src_y < h:
                px = _normalize_pixel(img.getpixel((x, src_y)))
                img.putpixel((x, y), px[:3])
            else:
                img.putpixel((x, y), bg[:3])


# --- line captcha -------------------------------------------------------------


class LineCaptcha(AbstractCaptcha):
    def __init__(self) -> None:
        super().__init__()
        self.interfere_count = 150

    def create_code(self) -> None:
        self._generate_code()
        img = Image.new("RGB", (self.width, self.height), self._bg()[:3])
        for _ in range(self.interfere_count):
            xs = self._rand_int(self.width)
            ys = self._rand_int(self.height)
            xe = xs + self._rand_int(max(self.width // 8, 1))
            ye = ys + self._rand_int(max(self.height // 8, 1))
            _draw_line(img, xs, ys, xe, ye, self._rand_color())
        _draw_string(img, self._code, self.width, self.height, _compute_scale(self.height), self._rand_color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self._set_image_bytes(buf.getvalue())


# --- circle captcha -----------------------------------------------------------


class CircleCaptcha(AbstractCaptcha):
    def __init__(self) -> None:
        super().__init__()
        self.interfere_count = 15

    def create_code(self) -> None:
        self._generate_code()
        img = Image.new("RGB", (self.width, self.height), self._bg()[:3])
        half = self.height // 2
        for _ in range(self.interfere_count):
            cx = self._rand_int(self.width)
            cy = self._rand_int(self.height)
            rx = self._rand_int(max(half, 1))
            ry = self._rand_int(max(half, 1))
            _draw_oval(img, cx, cy, rx, ry, self._rand_color())
        _draw_string(img, self._code, self.width, self.height, _compute_scale(self.height), self._rand_color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self._set_image_bytes(buf.getvalue())


# --- shear captcha ------------------------------------------------------------


class ShearCaptcha(AbstractCaptcha):
    def __init__(self) -> None:
        super().__init__()
        self.interfere_count = 4

    def create_code(self) -> None:
        self._generate_code()
        img = Image.new("RGB", (self.width, self.height), self._bg()[:3])
        _draw_string(img, self._code, self.width, self.height, _compute_scale(self.height), self._rand_color)

        period_x = self._rand_int_range(self.width // 4, self.width) or self.width
        _shear_x(img, self._bg(), period_x)
        period_y = self._rand_int_range(self.height // 4, self.height) or self.height
        _shear_y(img, self._bg(), period_y)

        thickness = self.interfere_count or 4
        _draw_thick_line(
            img,
            0,
            self._rand_int(self.height) + 1,
            self.width,
            self._rand_int(self.height) + 1,
            thickness,
            self._rand_color(),
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self._set_image_bytes(buf.getvalue())


# --- GIF captcha --------------------------------------------------------------


class GifCaptcha(AbstractCaptcha):
    def __init__(self) -> None:
        super().__init__()
        self.interfere_count = 10
        self.repeat = 0
        self.delay = 10

    def create_code(self) -> None:
        self._generate_code()
        frames: list[Image.Image] = []
        half = self.height // 2
        for hi in range(len(self._code)):
            rgba = Image.new("RGB", (self.width, self.height), self._bg()[:3])
            for _ in range(self.interfere_count):
                cx = self._rand_int(self.width)
                cy = self._rand_int(self.height)
                rx = self._rand_int(max(half, 1))
                ry = self._rand_int(max(half, 1))
                _draw_oval(rgba, cx, cy, rx, ry, self._rand_color())
            _draw_code_frame(rgba, self._code, hi, self.width, self.height, self._rand_color)
            frames.append(rgba)

        buf = io.BytesIO()
        frames[0].save(
            buf,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=self.delay * 10,
            loop=self.repeat,
            disposal=2,
        )
        self._set_image_bytes(buf.getvalue())

    def image_base64_data(self) -> str:
        if self._img_bytes is None:
            self.create_code()
        return "data:image/gif;base64," + self.image_base64()


def _pale_color_component() -> int:
    return 160 + secrets.randbelow(80)


def _draw_code_frame(
    img: Image.Image,
    code: str,
    highlight: int,
    w: int,
    h: int,
    color_func: Callable[[], tuple[int, int, int]],
) -> None:
    scale = _compute_scale(h)
    char_w = FONT_WIDTH * scale + scale
    total_w = char_w * len(code)
    start_x = (w - total_w) // 2
    char_h = FONT_HEIGHT * scale
    start_y = (h - char_h) // 2
    for i, ch in enumerate(code.encode("ascii", errors="replace")):
        if i == highlight:
            c = color_func()
        else:
            c = (_pale_color_component(), _pale_color_component(), _pale_color_component())
        _draw_char(img, ch, start_x + i * char_w, start_y, scale, c)


# --- captcha factories --------------------------------------------------------


def new_line_captcha(width: int, height: int, opts: Sequence[CaptchaOption] | None = None) -> LineCaptcha:
    c = LineCaptcha()
    c.width = width
    c.height = height
    c._generator = RandomGenerator(length=5)
    c._apply_options(opts or [])
    return c


def new_circle_captcha(width: int, height: int, opts: Sequence[CaptchaOption] | None = None) -> CircleCaptcha:
    c = CircleCaptcha()
    c.width = width
    c.height = height
    c._generator = RandomGenerator(length=5)
    c._apply_options(opts or [])
    return c


def new_shear_captcha(width: int, height: int, opts: Sequence[CaptchaOption] | None = None) -> ShearCaptcha:
    c = ShearCaptcha()
    c.width = width
    c.height = height
    c._generator = RandomGenerator(length=5)
    c._apply_options(opts or [])
    return c


def new_gif_captcha(width: int, height: int, opts: Sequence[CaptchaOption] | None = None) -> GifCaptcha:
    c = GifCaptcha()
    c.width = width
    c.height = height
    c._generator = RandomGenerator(length=5)
    cfg = c._apply_options(opts or [])
    if cfg.set_gif_repeat:
        c.repeat = cfg.gif_repeat
    if cfg.set_gif_delay:
        c.delay = cfg.gif_delay
    return c


# --- QR code / barcode (simplified, using qrcode package) ---------------------


class BarcodeFormat(IntEnum):
    UNKNOWN = 0
    AZTEC = 1
    CODABAR = 2
    CODE_39 = 3
    CODE_93 = 4
    CODE_128 = 5
    DATA_MATRIX = 6
    EAN_8 = 7
    EAN_13 = 8
    ITF = 9
    MAXICODE = 10
    PDF_417 = 11
    QR_CODE = 12
    RSS_14 = 13
    RSS_EXPANDED = 14
    UPC_A = 15
    UPC_E = 16


class BarcodeOutputFormat(IntEnum):
    UNKNOWN = 0
    PNG = 1
    SVG = 2
    ASCII = 3
    BASE64_DATA = 4


class QRErrorCorrectionLevel(IntEnum):
    UNKNOWN = 0
    LOW = 1
    MEDIUM = 2
    QUARTILE = 3
    HIGH = 4


_QR_EC_MAP = {
    QRErrorCorrectionLevel.LOW: "L",
    QRErrorCorrectionLevel.MEDIUM: "M",
    QRErrorCorrectionLevel.QUARTILE: "Q",
    QRErrorCorrectionLevel.HIGH: "H",
}


@dataclass
class DecodeResult:
    text: str
    format: BarcodeFormat
    raw_bytes: bytes = field(default_factory=bytes)
    metadata: dict[str, Any] = field(default_factory=dict)


# --- barcode options ----------------------------------------------------------

BarcodeOption = Callable[[list[Any]], None]  # modifies [size, margin, fg, bg, ...]
QRCodeOption = BarcodeOption


def with_barcode_size(width: int, height: int) -> BarcodeOption:
    def _apply(cfg: list[Any]) -> None:
        if width <= 0 or height <= 0:
            raise ErrImageInvalidInput("image: barcode size must be positive")
        cfg[0] = width
        cfg[1] = height

    return _apply


def with_qr_code_size(size: int) -> QRCodeOption:
    return with_barcode_size(size, size)


def with_barcode_margin(margin: int) -> BarcodeOption:
    def _apply(cfg: list[Any]) -> None:
        if margin < 0:
            raise ErrImageInvalidInput("image: barcode margin must be non-negative")
        cfg[2] = margin

    return _apply


def with_qr_code_margin(margin: int) -> QRCodeOption:
    return with_barcode_margin(margin)


def with_barcode_foreground(fg: tuple[int, int, int]) -> BarcodeOption:
    def _apply(cfg: list[Any]) -> None:
        cfg[3] = fg

    return _apply


def with_qr_code_foreground(fg: tuple[int, int, int]) -> QRCodeOption:
    return with_barcode_foreground(fg)


def with_barcode_background(bg: tuple[int, int, int]) -> BarcodeOption:
    def _apply(cfg: list[Any]) -> None:
        cfg[4] = bg

    return _apply


def with_qr_code_background(bg: tuple[int, int, int]) -> QRCodeOption:
    return with_barcode_background(bg)


def with_qr_code_error_correction(level: QRErrorCorrectionLevel) -> QRCodeOption:
    def _apply(cfg: list[Any]) -> None:
        if level not in _QR_EC_MAP:
            raise ErrImageInvalidInput("image: invalid qr error correction level")
        cfg[5] = level

    return _apply


def with_qr_code_version(version: int) -> QRCodeOption:
    def _apply(cfg: list[Any]) -> None:
        if version < 1 or version > 40:
            raise ErrImageInvalidInput("image: qr version must be between 1 and 40")
        cfg[6] = version

    return _apply


def _default_barcode_config() -> list[Any]:
    return [256, 256, 4, (0, 0, 0), (255, 255, 255), QRErrorCorrectionLevel.LOW, -1]


def _apply_barcode_options(opts: Sequence[BarcodeOption]) -> list[Any]:
    cfg = _default_barcode_config()
    for opt in opts or []:
        if opt is not None:
            opt(cfg)
    return cfg


# --- QR code generation (using qrcode) ----------------------------------------


def qr_code_image(content: str, opts: Sequence[QRCodeOption] | None = None) -> Image.Image:
    try:
        import qrcode  # type: ignore[import-untyped]
    except ImportError:
        raise ErrImageUnsupported("image: qrcode package not installed")

    cfg = _apply_barcode_options(opts or [])
    width, height, margin, fg, bg, ec_level, version = cfg

    qr = qrcode.QRCode(
        version=version if version > 0 else None,
        error_correction={
            QRErrorCorrectionLevel.LOW: qrcode.constants.ERROR_CORRECT_L,
            QRErrorCorrectionLevel.MEDIUM: qrcode.constants.ERROR_CORRECT_M,
            QRErrorCorrectionLevel.QUARTILE: qrcode.constants.ERROR_CORRECT_Q,
            QRErrorCorrectionLevel.HIGH: qrcode.constants.ERROR_CORRECT_H,
        }.get(ec_level, qrcode.constants.ERROR_CORRECT_L),
        box_size=10,
        border=margin // 2 + 1,
    )
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color=_rgb_to_hex(fg), back_color=_rgb_to_hex(bg))
    return img.resize((width, height), Image.Resampling.NEAREST)  # type: ignore[no-any-return]


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def qr_code_png(content: str, opts: Sequence[QRCodeOption] | None = None) -> bytes:
    img = qr_code_image(content, opts)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def qr_code_base64_data(content: str, opts: Sequence[QRCodeOption] | None = None) -> str:
    png_bytes = qr_code_png(content, opts)
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode()


def write_qr_code(w: io.BytesIO, content: str, opts: Sequence[QRCodeOption] | None = None) -> None:
    img = qr_code_image(content, opts)
    img.save(w, format="PNG")


def qr_code_svg(content: str, opts: Sequence[QRCodeOption] | None = None) -> str:
    img = qr_code_image(content, opts)
    import xml.etree.ElementTree as ET

    svg = ET.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        viewBox=f"0 0 {img.width} {img.height}",
        width=str(img.width),
        height=str(img.height),
    )
    ET.SubElement(svg, "rect", width="100%", height="100%", fill=_rgb_to_hex((255, 255, 255)))
    for y in range(img.height):
        for x in range(img.width):
            px = _normalize_pixel(img.getpixel((x, y)))
            if px[0] < 128:
                ET.SubElement(svg, "rect", x=str(x), y=str(y), width="1", height="1", fill="black")
    return ET.tostring(svg, encoding="unicode")


def qr_code_ascii(content: str, opts: Sequence[QRCodeOption] | None = None) -> str:
    return qr_code_ascii_with_chars(content, "██", "  ", opts)


def qr_code_ascii_with_chars(
    content: str,
    set_string: str,
    unset_string: str,
    opts: Sequence[QRCodeOption] | None = None,
) -> str:
    img = qr_code_image(content, opts)
    lines: list[str] = []
    for y in range(img.height):
        line = ""
        for x in range(img.width):
            px = _normalize_pixel(img.getpixel((x, y)))
            is_dark = px[0] < 128
            line += set_string if is_dark else unset_string
        lines.append(line)
    return "\n".join(lines)


def supported_encode_barcode_formats() -> list[BarcodeFormat]:
    return [BarcodeFormat.QR_CODE]


def can_encode_barcode_format(fmt: BarcodeFormat) -> bool:
    return fmt == BarcodeFormat.QR_CODE


def supported_decode_barcode_formats() -> list[BarcodeFormat]:
    return [BarcodeFormat.QR_CODE]


def can_decode_barcode_format(fmt: BarcodeFormat) -> bool:
    return fmt == BarcodeFormat.QR_CODE