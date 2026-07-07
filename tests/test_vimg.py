"""Tests for vimg facade — image operations, captcha, and QR code."""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import cast

import pytest
from PIL import Image

from kniferpy.internal import imgx
from kniferpy.internal.imgx import ErrImageInvalidInput, ErrImageUnsupported
from kniferpy.vimg import (
    BarcodeFormat,
    BarcodeOutputFormat,
    CaptchaOption,
    GifCaptcha,
    LineCaptcha,
    MathGenerator,
    QRErrorCorrectionLevel,
    RandomGenerator,
    add_text_watermark,
    add_watermark,
    barcode_ascii,
    barcode_ascii_with_chars,
    barcode_base64_data,
    barcode_bytes,
    barcode_image,
    barcode_png,
    barcode_svg,
    can_decode_barcode_format,
    can_encode_barcode_format,
    compress_jpeg,
    convert_format,
    crop,
    crop_center,
    flip_horizontal,
    flip_vertical,
    gen_math_generator_with_options,
    gen_random_generator_with_options,
    grayscale,
    info,
    new_circle_captcha,
    new_circle_captcha_with,
    new_gif_captcha,
    new_gif_captcha_with,
    new_line_captcha,
    new_line_captcha_with,
    new_math_generator,
    new_math_generator_with,
    new_random_generator,
    new_random_generator_with_base,
    new_shear_captcha,
    new_shear_captcha_with,
    qr_code_ascii,
    qr_code_ascii_with_chars,
    qr_code_base64_data,
    qr_code_bytes,
    qr_code_image,
    qr_code_png,
    qr_code_svg,
    resize,
    rotate,
    rotate_90,
    rotate_180,
    rotate_270,
    supported_decode_barcode_formats,
    supported_encode_barcode_formats,
    thumbnail,
    verify_captcha_ignore_case,
    verify_ignore_case,
    with_background,
    with_barcode_background,
    with_barcode_character_set,
    with_barcode_colors,
    with_barcode_force_code_set,
    with_barcode_foreground,
    with_barcode_gs1_format,
    with_barcode_logo,
    with_barcode_logo_size,
    with_barcode_transparent_background,
    with_color_func,
    with_decode_also_inverted,
    with_decode_character_set,
    with_decode_formats,
    with_decode_pure_barcode,
    with_decode_try_harder,
    with_font_size,
    with_generator,
    with_generator_int_parser,
    with_generator_random_int,
    with_gif_delay,
    with_gif_repeat,
    with_interfere_count,
    with_qr_code_background,
    with_qr_code_colors,
    with_qr_code_error_correction,
    with_qr_code_foreground,
    with_qr_code_logo,
    with_qr_code_logo_ratio,
    with_qr_code_logo_size,
    with_qr_code_margin,
    with_qr_code_mask_pattern,
    with_qr_code_size,
    with_qr_code_transparent_background,
    with_qr_code_version,
    write_qr_code,
)


def _make_png(width: int, height: int) -> bytes:
    img = Image.new("RGBA", (width, height))
    for y in range(height):
        for x in range(width):
            img.putpixel((x, y), (x % 256, y % 256, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --- image operations ---------------------------------------------------------


class TestInfo:
    def test_info_png(self) -> None:
        data = _make_png(32, 16)
        w, h, fmt = info(data)
        assert w == 32
        assert h == 16
        assert fmt == "png"

    def test_info_jpeg(self) -> None:
        img = Image.new("RGB", (10, 8), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        w, h, fmt = info(buf.getvalue())
        assert w == 10
        assert h == 8
        assert fmt == "jpeg"

    def test_info_invalid_data(self) -> None:
        with pytest.raises(ErrImageInvalidInput):
            info(b"not an image")


class TestThumbnail:
    def test_thumbnail_downscale(self) -> None:
        data = _make_png(200, 200)
        result = thumbnail(data, 32, "png")
        img = Image.open(io.BytesIO(result))
        assert img.width <= 32 and img.height <= 32

    def test_thumbnail_smaller_unchanged(self) -> None:
        data = _make_png(16, 16)
        result = thumbnail(data, 64, "png")
        img = Image.open(io.BytesIO(result))
        assert img.width == 16 and img.height == 16

    def test_thumbnail_jpeg_output(self) -> None:
        data = _make_png(100, 100)
        result = thumbnail(data, 32, "jpeg")
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"
        assert img.width <= 32

    def test_thumbnail_portrait_downscale(self) -> None:
        data = _make_png(20, 100)
        result = thumbnail(data, 40, "png")
        img = Image.open(io.BytesIO(result))
        assert img.height == 40
        assert img.width == 8

    def test_thumbnail_invalid_max_edge(self) -> None:
        data = _make_png(32, 32)
        with pytest.raises(ErrImageInvalidInput):
            thumbnail(data, 0, "png")

    def test_thumbnail_unsupported_format(self) -> None:
        data = _make_png(32, 32)
        with pytest.raises(ErrImageUnsupported):
            thumbnail(data, 32, "bmp")


class TestConvertFormat:
    def test_png_to_jpeg(self) -> None:
        data = _make_png(16, 16)
        result = convert_format(data, "jpeg")
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"

    def test_jpeg_to_png(self) -> None:
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result = convert_format(buf.getvalue(), "png")
        out = Image.open(io.BytesIO(result))
        assert out.format == "PNG"

    def test_convert_invalid_data(self) -> None:
        with pytest.raises(ErrImageInvalidInput):
            convert_format(b"not an image", "png")


class TestResize:
    def test_resize(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = resize(img, 50, 40)
        assert result.width == 50
        assert result.height == 40

    def test_resize_invalid(self) -> None:
        img = Image.new("RGB", (10, 10))
        with pytest.raises(ErrImageInvalidInput):
            resize(img, 0, 10)


class TestCrop:
    def test_crop(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = crop(img, 10, 10, 30, 20)
        assert result.width == 30
        assert result.height == 20

    def test_crop_out_of_bounds(self) -> None:
        img = Image.new("RGB", (10, 10))
        with pytest.raises(ErrImageInvalidInput):
            crop(img, 5, 5, 10, 10)

    def test_crop_center(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = crop_center(img, 50, 40)
        assert result.width == 50
        assert result.height == 40


class TestFlip:
    def test_flip_horizontal(self) -> None:
        img = Image.new("RGB", (10, 10))
        result = flip_horizontal(img)
        assert result.width == 10 and result.height == 10

    def test_flip_vertical(self) -> None:
        img = Image.new("RGB", (10, 10))
        result = flip_vertical(img)
        assert result.width == 10 and result.height == 10


class TestRotate:
    def test_rotate_90(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = rotate_90(img)
        assert result.width == 80
        assert result.height == 100

    def test_rotate_180(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = rotate_180(img)
        assert result.width == 100
        assert result.height == 80

    def test_rotate_270(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = rotate_270(img)
        assert result.width == 80
        assert result.height == 100

    def test_rotate_arbitrary(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = rotate(img, 45.0, (255, 255, 255, 255))
        assert result.width > 0 and result.height > 0

    def test_rotate_zero(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = rotate(img, 0.0, (255, 255, 255, 255))
        assert result.width == 100
        assert result.height == 80

    def test_rotate_negative_and_invalid_angle(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = rotate(img, -90.0, (255, 255, 255, 255))
        assert result.width == 80 and result.height == 100
        with pytest.raises(ErrImageInvalidInput):
            rotate(img, float("nan"), (255, 255, 255, 255))


class TestGrayscale:
    def test_grayscale(self) -> None:
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        result = grayscale(img)
        assert result.width == 10 and result.height == 10

    def test_grayscale_rgba_preserves_alpha(self) -> None:
        img = Image.new("RGBA", (2, 2), (255, 0, 0, 128))
        result = grayscale(img)
        assert result.mode == "RGBA"
        pixel = cast(tuple[int, ...], result.getpixel((0, 0)))
        assert pixel[3] == 128


class TestCompressJPEG:
    def test_compress_jpeg(self) -> None:
        img = Image.new("RGB", (20, 20), (255, 0, 0))
        result = compress_jpeg(img, 50)
        assert len(result) > 0

    def test_compress_jpeg_invalid_quality(self) -> None:
        img = Image.new("RGB", (10, 10))
        with pytest.raises(ErrImageInvalidInput):
            compress_jpeg(img, 0)
        with pytest.raises(ErrImageInvalidInput):
            compress_jpeg(img, 101)


class TestWatermark:
    def test_add_watermark(self) -> None:
        img = Image.new("RGBA", (50, 50), (255, 255, 255, 255))
        wm = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        result = add_watermark(img, wm, 5, 5, 0.5)
        assert result.width == 50 and result.height == 50

    def test_add_watermark_invalid_opacity(self) -> None:
        img = Image.new("RGBA", (10, 10))
        wm = Image.new("RGBA", (5, 5))
        with pytest.raises(ErrImageInvalidInput):
            add_watermark(img, wm, 0, 0, 1.5)

    def test_add_watermark_out_of_bounds_and_grayscale_base(self) -> None:
        img = Image.new("L", (4, 4), 100)
        wm = Image.new("RGBA", (3, 3), (255, 0, 0, 128))
        result = add_watermark(img.convert("RGBA"), wm, -1, -1, 0.5)
        assert result.size == (4, 4)

    def test_add_text_watermark(self) -> None:
        img = Image.new("RGBA", (100, 50), (255, 255, 255, 255))
        result = add_text_watermark(img, "ABC", 10, 10, (255, 0, 0, 255), 2, 0.8)
        assert result.width == 100 and result.height == 50

    def test_add_text_watermark_empty(self) -> None:
        img = Image.new("RGBA", (10, 10))
        with pytest.raises(ErrImageInvalidInput):
            add_text_watermark(img, "", 0, 0, (0, 0, 0, 255), 1, 0.5)

    def test_add_text_watermark_invalid_scale_and_opacity(self) -> None:
        img = Image.new("RGBA", (10, 10))
        with pytest.raises(ErrImageInvalidInput):
            add_text_watermark(img, "A", 0, 0, (0, 0, 0, 255), 0, 0.5)
        with pytest.raises(ErrImageInvalidInput):
            add_text_watermark(img, "A", 0, 0, (0, 0, 0, 255), 1, float("nan"))


# --- captcha generators -------------------------------------------------------


class TestRandomGenerator:
    def test_gen(self) -> None:
        gen = RandomGenerator(length=6)
        code = gen.gen()
        assert len(code) == 6

    def test_verify(self) -> None:
        gen = RandomGenerator(length=4)
        code = gen.gen()
        assert gen.verify(code, code)
        assert gen.verify(code, code.lower())
        assert not gen.verify(code, "")
        assert not gen.verify(code, "wrong")

    def test_min_length_and_custom_charset(self) -> None:
        gen = RandomGenerator(length=1, charset="A")
        assert gen.length == 4
        assert gen.gen() == "AAAA"


class TestMathGenerator:
    def test_gen(self) -> None:
        gen = MathGenerator(number_length=2)
        expr = gen.gen()
        assert "=" in expr
        assert any(op in expr for op in "+-*")

    def test_verify(self) -> None:
        gen = MathGenerator(number_length=1)
        code = gen.gen()  # e.g., "3+4="
        expected = gen._eval_expr(code)
        if expected is not None:
            assert gen.verify(code, str(expected))
            assert not gen.verify(code, "999")

    def test_eval_expr_invalid_and_verify_bad_input(self) -> None:
        assert MathGenerator._eval_expr("bad") is None
        assert MathGenerator._eval_expr("1+x=") is None
        gen = MathGenerator(number_length=1)
        assert not gen.verify("1+1=", "bad")


class TestVerifyIgnoreCase:
    def test_match(self) -> None:
        assert verify_ignore_case("ABC", "abc")
        assert verify_ignore_case("  abc  ", "ABC")

    def test_mismatch(self) -> None:
        assert not verify_ignore_case("ABC", "ABD")


# --- captcha types ------------------------------------------------------------


class TestLineCaptcha:
    def test_create(self) -> None:
        c = new_line_captcha(160, 60)
        assert c.code
        assert len(c.code) == 5
        assert c.image_bytes()
        assert c.verify(c.code)

    def test_with_options(self) -> None:
        c = new_line_captcha(
            160,
            60,
            [with_generator(RandomGenerator(length=4)), with_interfere_count(50)],
        )
        assert len(c.code) == 4
        assert c.image_bytes()

    def test_verify(self) -> None:
        c = new_line_captcha(160, 60)
        assert c.verify(c.code)
        assert not c.verify("wrong")

    def test_write_to_file(self) -> None:
        c = new_line_captcha(160, 60)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            c.write_to_file(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_image_base64(self) -> None:
        c = new_line_captcha(160, 60)
        b64 = c.image_base64()
        assert len(b64) > 0
        data = c.image_base64_data()
        assert data.startswith("data:image/png;base64,")

    def test_write_and_write_to_file_options(self, tmp_path: Path) -> None:
        c = new_line_captcha(
            80,
            30,
            [
                imgx.with_random_int(lambda max_val: max_val + 2),
                with_color_func(lambda: (1, 2, 3)),
                with_font_size(2.0),
                with_interfere_count(-1),
            ],
        )
        buf = io.BytesIO()
        c.write(buf)
        assert buf.getvalue()
        path = tmp_path / "captcha.png"
        c.write_to_file(
            str(path),
            [
                imgx.with_file_perm(0o600),
                imgx.with_dir_perm(0o700),
                imgx.with_create_parents(True),
                imgx.with_overwrite(False),
            ],
        )
        with pytest.raises(ErrImageInvalidInput):
            c.write_to_file(str(path), [imgx.with_overwrite(False)])


def test_abstract_captcha_empty_write_paths() -> None:
    c = imgx.AbstractCaptcha()
    c._img_bytes = b""
    with pytest.raises(ErrImageInvalidInput):
        c.write(io.BytesIO())
    with pytest.raises(ErrImageInvalidInput):
        c.write_to_file("/tmp/unused.png")
    with pytest.raises(NotImplementedError):
        c.create_code()
    assert c._rand_int(0) == 0
    c._random_int = lambda max_val: -1
    assert c._rand_int(10) == 0
    c._random_int = lambda max_val: max_val + 1
    assert c._rand_int(10) == 1
    assert c._rand_int_range(5, 5) == 5
    c._color_func = lambda: (9, 8, 7)
    assert c._rand_color() == (9, 8, 7)


class TestCircleCaptcha:
    def test_create(self) -> None:
        c = new_circle_captcha(160, 60)
        assert c.code
        assert len(c.code) == 5
        assert c.image_bytes()
        assert c.verify(c.code)

    def test_with_options(self) -> None:
        c = new_circle_captcha(160, 60, [with_interfere_count(25)])
        assert c.code
        assert c.image_bytes()


class TestShearCaptcha:
    def test_create(self) -> None:
        c = new_shear_captcha(160, 60)
        assert c.code
        assert len(c.code) == 5
        assert c.image_bytes()
        assert c.verify(c.code)

    def test_with_options(self) -> None:
        c = new_shear_captcha(160, 60, [with_background((200, 200, 200, 255))])
        assert c.code
        assert c.image_bytes()


class TestGifCaptcha:
    def test_create(self) -> None:
        c = new_gif_captcha(160, 60)
        assert c.code
        assert len(c.code) == 5
        assert c.image_bytes()
        assert c.verify(c.code)

    def test_image_base64_data(self) -> None:
        c = new_gif_captcha(160, 60)
        data = c.image_base64_data()
        assert data.startswith("data:image/gif;base64,")

    def test_with_options(self) -> None:
        c = new_gif_captcha(160, 60, [with_gif_repeat(5), with_gif_delay(20)])
        assert c.code
        assert c.image_bytes()
        assert c.repeat == 5
        assert c.delay == 20


# --- QR code ------------------------------------------------------------------


class TestQRCode:
    def test_qr_code_image(self) -> None:
        img = qr_code_image("https://example.com")
        assert img.width > 0 and img.height > 0

    def test_qr_code_png(self) -> None:
        png = qr_code_png("test")
        assert len(png) > 0

    def test_qr_code_base64_data(self) -> None:
        data = qr_code_base64_data("test")
        assert data.startswith("data:image/png;base64,")

    def test_write_qr_code(self) -> None:
        buf = io.BytesIO()
        write_qr_code(buf, "hello")
        assert buf.tell() > 0

    def test_qr_code_svg(self) -> None:
        svg = qr_code_svg("test")
        assert "<svg" in svg

    def test_qr_code_ascii(self) -> None:
        ascii_str = qr_code_ascii("test")
        assert len(ascii_str) > 0

    def test_qr_code_ascii_with_chars(self) -> None:
        ascii_str = qr_code_ascii_with_chars("test", "#", ".")
        assert "#" in ascii_str or "." in ascii_str

    def test_qr_code_bytes_output_formats(self) -> None:
        png = qr_code_bytes("test", BarcodeOutputFormat.PNG)
        svg = qr_code_bytes("test", BarcodeOutputFormat.SVG)
        ascii_bytes = qr_code_bytes("test", BarcodeOutputFormat.ASCII)
        base64_data = qr_code_bytes("test", BarcodeOutputFormat.BASE64_DATA)
        fallback = qr_code_bytes("test", BarcodeOutputFormat.UNKNOWN)

        assert png.startswith(b"\x89PNG")
        assert b"<svg" in svg
        assert ascii_bytes
        assert base64_data.startswith(b"data:image/png;base64,")
        assert fallback.startswith(b"\x89PNG")

    def test_with_size(self) -> None:
        img = qr_code_image("test", [with_qr_code_size(128)])
        assert img.width == 128 and img.height == 128

    def test_with_margin(self) -> None:
        img = qr_code_image("test", [with_qr_code_margin(10)])
        assert img.width > 0

    def test_with_error_correction(self) -> None:
        img = qr_code_image("test", [with_qr_code_error_correction(QRErrorCorrectionLevel.HIGH)])
        assert img.width > 0

    def test_with_version(self) -> None:
        img = qr_code_image("test", [with_qr_code_version(5)])
        assert img.width > 0

    def test_with_colors(self) -> None:
        img = qr_code_image(
            "test",
            [with_barcode_foreground((0, 0, 255)), with_barcode_background((255, 255, 200))],
        )
        assert img.width > 0

    def test_invalid_qr_options_raise(self) -> None:
        with pytest.raises(ErrImageInvalidInput):
            qr_code_image("test", [with_qr_code_size(0)])
        with pytest.raises(ErrImageInvalidInput):
            qr_code_image("test", [with_qr_code_margin(-1)])
        with pytest.raises(ErrImageInvalidInput):
            qr_code_image("test", [with_qr_code_error_correction(QRErrorCorrectionLevel.UNKNOWN)])
        with pytest.raises(ErrImageInvalidInput):
            qr_code_image("test", [with_qr_code_version(41)])


class TestBarcodeFormat:
    def test_supported_encode(self) -> None:
        formats = supported_encode_barcode_formats()
        assert BarcodeFormat.QR_CODE in formats

    def test_can_encode(self) -> None:
        assert can_encode_barcode_format(BarcodeFormat.QR_CODE)
        assert not can_encode_barcode_format(BarcodeFormat.CODE_128)

    def test_supported_decode(self) -> None:
        formats = supported_decode_barcode_formats()
        assert BarcodeFormat.QR_CODE in formats

    def test_can_decode(self) -> None:
        assert can_decode_barcode_format(BarcodeFormat.QR_CODE)
        assert not can_decode_barcode_format(BarcodeFormat.CODE_128)


# --- focused edge coverage ----------------------------------------------------


def test_internal_helpers_and_error_paths() -> None:
    assert imgx._normalize_format("jpg") == "jpeg"
    assert imgx._fit_long_edge(200, 100, 50) == (50, 25)
    assert imgx._fit_long_edge(100, 200, 50) == (25, 50)
    assert imgx._normalize_pixel(None) == (0, 0, 0, 255)
    assert imgx._normalize_pixel(12.9) == (12, 12, 12, 255)
    assert imgx._normalize_pixel((1, 2, 3)) == (1, 2, 3, 255)
    assert imgx._normalize_pixel((1, 2, 3, 4)) == (1, 2, 3, 4)
    assert imgx._get_glyph(ord("a")) == imgx._get_glyph(ord("A"))
    assert imgx._get_glyph(ord("\n")) == imgx._get_glyph(ord("?"))
    assert imgx._blend_color((255, 255, 255, 255), (0, 0, 0, 255), 0.5)[0] < 255

    with pytest.raises(ErrImageInvalidInput):
        info(b"not-image")
    with pytest.raises(ErrImageInvalidInput):
        convert_format(b"not-image", "png")
    with pytest.raises(ErrImageUnsupported):
        convert_format(_make_png(4, 4), "bmp")
    with pytest.raises(ErrImageInvalidInput):
        rotate(Image.new("RGB", (2, 2)), float("nan"), (0, 0, 0, 0))
    with pytest.raises(ErrImageInvalidInput):
        rotate(Image.new("RGB", (2, 2)), float("inf"), (0, 0, 0, 0))
    with pytest.raises(ErrImageInvalidInput):
        crop(Image.new("RGB", (2, 2)), 0, 0, 0, 1)
    with pytest.raises(ErrImageInvalidInput):
        add_text_watermark(Image.new("RGBA", (10, 10)), "A", 0, 0, (0, 0, 0, 255), 0, 1)
    with pytest.raises(ErrImageInvalidInput):
        add_text_watermark(Image.new("RGBA", (10, 10)), "A", 0, 0, (0, 0, 0, 255), 1, -0.1)


def test_rotate_negative_and_rgba_grayscale_jpeg() -> None:
    img = Image.new("RGBA", (4, 2), (255, 0, 0, 128))

    assert rotate(img, -90, (0, 0, 0, 0)).size == (2, 4)
    assert grayscale(img).mode == "RGBA"
    assert Image.open(io.BytesIO(compress_jpeg(img, 80))).format == "JPEG"


def test_watermark_outside_bounds_and_text_unknown_char() -> None:
    base = Image.new("RGBA", (5, 5), (255, 255, 255, 255))
    wm = Image.new("RGBA", (3, 3), (0, 0, 0, 255))

    result = add_watermark(base, wm, -2, -2, 1.0)
    assert result.size == base.size
    text = add_text_watermark(base, "\u2603", 0, 0, (0, 0, 0, 255), 1, 1.0)
    assert text.size == base.size


def test_generators_convenience_and_edge_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    random_gen = new_random_generator()
    assert len(random_gen.gen()) == 5
    assert new_random_generator_with_base("A").gen() == "AAAAA"
    opt_gen = gen_random_generator_with_options(base="B", random_int=lambda n: 0)
    assert opt_gen.base == "B"

    math_gen = new_math_generator()
    assert isinstance(math_gen, MathGenerator)
    assert new_math_generator_with((1, 2), (3, 4))._num1_range == (1, 2)
    opt_math = gen_math_generator_with_options(
        (1, 2),
        (3, 4),
        int_parser=int,
        random_int=lambda n: 0,
    )
    assert opt_math._num2_range == (3, 4)
    assert MathGenerator._eval_expr("bad") is None
    assert MathGenerator._eval_expr("1+x=") is None
    assert not MathGenerator().verify("1+1=", "bad")
    assert verify_captcha_ignore_case("ABC", "abc")


def test_captcha_constructors_and_write_options(tmp_path: Path) -> None:
    line = new_line_captcha_with(80, 30, 4, 2)
    circle = new_circle_captcha_with(80, 30, 4, 2)
    shear = new_shear_captcha_with(80, 30, 4, 2)
    gif = new_gif_captcha_with(80, 30, 4)
    custom = new_line_captcha(
        80,
        30,
        [
            with_font_size(12),
            with_color_func(lambda: (1, 2, 3)),
            cast(CaptchaOption, with_generator_int_parser(int)),
            cast(CaptchaOption, with_generator_random_int(lambda n: 0)),
        ],
    )

    assert isinstance(line, LineCaptcha)
    assert len(line.code) == 4
    assert len(circle.code) == 4
    assert len(shear.code) == 4
    assert isinstance(gif, GifCaptcha)
    assert len(gif.code) == 4
    assert custom.image_bytes()
    target = tmp_path / "nested" / "captcha.png"
    custom.write_to_file(str(target))
    assert target.exists()


def test_qr_and_barcode_option_builders() -> None:
    logo = Image.new("RGB", (4, 4), (255, 255, 255))
    qr_options = [
        with_qr_code_size(64),
        with_qr_code_margin(2),
        with_qr_code_error_correction(QRErrorCorrectionLevel.LOW),
        with_qr_code_version(2),
        with_qr_code_foreground((0, 0, 0)),
        with_qr_code_background((255, 255, 255)),
    ]
    extended_options = [
        with_qr_code_colors((0, 0, 0), (255, 255, 255)),
        with_qr_code_logo(logo),
        with_qr_code_logo_ratio(0.2),
        with_qr_code_logo_size(8),
        with_qr_code_mask_pattern(1),
        with_qr_code_transparent_background(True),
        with_barcode_character_set("utf-8"),
        with_barcode_colors((0, 0, 0), (255, 255, 255)),
        with_barcode_force_code_set(True),
        with_barcode_gs1_format(True),
        with_barcode_logo(logo),
        with_barcode_logo_size(0.2),
        with_barcode_transparent_background(True),
    ]

    img = qr_code_image("test", qr_options)
    assert img.width > 0
    assert barcode_image("test", BarcodeFormat.QR_CODE, qr_options).width > 0
    assert len(barcode_png("test", BarcodeFormat.QR_CODE, qr_options)) > 0
    assert "<svg" in barcode_svg("test", BarcodeFormat.QR_CODE, qr_options)
    assert barcode_ascii("test", BarcodeFormat.QR_CODE, qr_options)
    assert barcode_ascii_with_chars("test", BarcodeFormat.QR_CODE, "#", ".", qr_options)
    assert barcode_base64_data("test", BarcodeFormat.QR_CODE, qr_options).startswith(
        "data:image/png"
    )
    assert len(barcode_bytes("test", BarcodeFormat.QR_CODE, qr_options)) > 0
    out = io.BytesIO()
    imgx.write_barcode(out, "test", BarcodeFormat.QR_CODE, qr_options)
    assert out.tell() > 0
    with pytest.raises(ErrImageUnsupported):
        barcode_image("test", BarcodeFormat.CODE_128)

    cfg: list[object] = []
    for opt in extended_options:
        opt(cfg)
    assert cfg[7] == "utf-8"
    assert cfg[9] is True
    assert cfg[10] is True
    assert cfg[11] is logo
    assert cfg[12] == 0.2
    assert cfg[13] is True
    assert cfg[14] == 8
    assert cfg[15] == 1


def test_decode_option_builders_and_decode_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg: list[object] = []
    for opt in (
        with_decode_also_inverted(True),
        with_decode_character_set("utf-8"),
        with_decode_formats([BarcodeFormat.QR_CODE]),
        with_decode_pure_barcode(True),
        with_decode_try_harder(True),
    ):
        opt(cfg)

    assert cfg[16] is True
    assert cfg[17] == "utf-8"
    assert cfg[18] == [BarcodeFormat.QR_CODE]
    assert cfg[19] is True
    assert cfg[20] is True
    assert imgx.decode_qr_code(_make_png(4, 4)) == []
    assert imgx.decode_barcode(_make_png(4, 4)) == []
    assert imgx.decode_barcode_image(Image.new("RGB", (4, 4))) == []
    result = imgx.DecodeResult(text="x", format=BarcodeFormat.QR_CODE, raw_bytes=b"x")
    assert isinstance(result, imgx.DecodeResult)
