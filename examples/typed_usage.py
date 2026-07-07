from __future__ import annotations

from pathlib import Path
from typing import Any, assert_type

from kniferpy import vcodec, vcrypto, vfile, vhttp, vjson, vurl


def json_and_file_usage(path: Path) -> None:
    vfile.write_text_atomic(path, '{"name": "kniferpy", "count": 3}')
    data = vjson.read_obj(path, max_bytes=4096)

    assert_type(data, dict[str, Any])
    assert_type(vjson.get_str(data, "name"), str | None)
    assert_type(vjson.get_int(data, "count"), int | None)


def http_and_url_usage() -> None:
    redacted = vurl.redact_userinfo("https://user:secret@example.com/path")
    assert_type(redacted, str)
    assert_type(vhttp.is_ok(204), bool)
    assert_type(vhttp.HTTPResponse(_body=b"hello").bytes(), bytes)
    assert_type(vhttp.HTTPResponse(_body=b"hello").body(), str)


def crypto_and_codec_usage() -> None:
    digest = vcrypto.sha256_hex("kniferpy")
    assert_type(digest, str)
    assert_type(vcrypto.verify_sha256_hex("kniferpy", digest), bool)
    encoded = vcodec.base64_encode_str("kniferpy")
    assert_type(encoded, str)
    assert_type(vcodec.base64_decode_str(encoded), str)
