"""Tests for vimg facade — image operations, captcha, and QR code."""

from __future__ import annotations

import io
import os
import tempfile

import pytest

from PIL import Image

from kniferpy.vimg import (
    BarcodeFormat,
    BarcodeOutputFormat,
    CircleCaptcha,
    DecodeResult,
    GifCaptcha,
    LineCaptcha,
    MathGenerator,
    QRCodeOption,
    QRErrorCorrectionLevel,
    RandomGenerator,
    ShearCaptcha,
    add_text_watermark,
    add_watermark,
    can_decode_barcode_format,
    can_encode_barcode_format,
    compress_jpeg,
    convert_format,
    crop,
    crop_center,
    flip_horizontal,
    flip_vertical,
    grayscale,
    info,
    new_circle_captcha,
    new_gif_captcha,
    new_line_captcha,
    new_shear_captcha,
    qr_code_ascii,
    qr_code_ascii_with_chars,
    qr_code_base64_data,
    qr_code_image,
    qr_code_png,
    qr_code_svg,
    resize,
    rotate,
    rotate_180,
    rotate_270,
    rotate_90,
    supported_decode_barcode_formats,
    supported_encode_barcode_formats,
    thumbnail,
    verify_ignore_case,
    with_background,
    with_barcode_background,
    with_barcode_foreground,
    with_barcode_margin,
    with_barcode_size,
    with_generator,
    with_gif_delay,
    with_gif_repeat,
    with_interfere_count,
    with_qr_code_error_correction,
    with_qr_code_margin,
    with_qr_code_size,
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

    def test_thumbnail_invalid_max_edge(self) -> None:
        data = _make_png(32, 32)
        with pytest.raises(Exception):
            thumbnail(data, 0, "png")

    def test_thumbnail_unsupported_format(self) -> None:
        data = _make_png(32, 32)
        with pytest.raises(Exception):
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


class TestResize:
    def test_resize(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = resize(img, 50, 40)
        assert result.width == 50
        assert result.height == 40

    def test_resize_invalid(self) -> None:
        img = Image.new("RGB", (10, 10))
        with pytest.raises(Exception):
            resize(img, 0, 10)


class TestCrop:
    def test_crop(self) -> None:
        img = Image.new("RGB", (100, 80))
        result = crop(img, 10, 10, 30, 20)
        assert result.width == 30
        assert result.height == 20

    def test_crop_out_of_bounds(self) -> None:
        img = Image.new("RGB", (10, 10))
        with pytest.raises(Exception):
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


class TestGrayscale:
    def test_grayscale(self) -> None:
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        result = grayscale(img)
        assert result.width == 10 and result.height == 10


class TestCompressJPEG:
    def test_compress_jpeg(self) -> None:
        img = Image.new("RGB", (20, 20), (255, 0, 0))
        result = compress_jpeg(img, 50)
        assert len(result) > 0

    def test_compress_jpeg_invalid_quality(self) -> None:
        img = Image.new("RGB", (10, 10))
        with pytest.raises(Exception):
            compress_jpeg(img, 0)
        with pytest.raises(Exception):
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
        with pytest.raises(Exception):
            add_watermark(img, wm, 0, 0, 1.5)

    def test_add_text_watermark(self) -> None:
        img = Image.new("RGBA", (100, 50), (255, 255, 255, 255))
        result = add_text_watermark(img, "ABC", 10, 10, (255, 0, 0, 255), 2, 0.8)
        assert result.width == 100 and result.height == 50

    def test_add_text_watermark_empty(self) -> None:
        img = Image.new("RGBA", (10, 10))
        with pytest.raises(Exception):
            add_text_watermark(img, "", 0, 0, (0, 0, 0, 255), 1, 0.5)


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
        c = new_line_captcha(160, 60, [with_generator(RandomGenerator(length=4)), with_interfere_count(50)])
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