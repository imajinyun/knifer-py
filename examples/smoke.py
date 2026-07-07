from __future__ import annotations

import tempfile
from pathlib import Path

from kniferpy import vcrypto, vfile, vhttp, vjson, vurl


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.json"
        vfile.write_text_atomic(path, '{"service": {"name": "kniferpy"}}')
        data = vjson.read_obj(path, max_bytes=1024)

    assert vjson.get_str(data, "service.name") == "kniferpy"
    assert vurl.redact_userinfo("https://user:secret@example.com/path") == (
        "https://***@example.com/path"
    )
    assert vhttp.is_ok(200)
    assert vcrypto.verify_sha256_hex("kniferpy", vcrypto.sha256_hex("kniferpy"))


if __name__ == "__main__":
    main()
