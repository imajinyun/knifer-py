from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass

from kniferpy import vcodec, vjson, vstr, vurl


@dataclass(frozen=True)
class BenchResult:
    name: str
    iterations: int
    elapsed_seconds: float
    ops_per_second: float


def _bench(name: str, iterations: int, fn: Callable[[], None]) -> BenchResult:
    started = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - started
    if elapsed <= 0:
        raise RuntimeError(f"benchmark {name!r} produced a non-positive duration")
    return BenchResult(
        name=name,
        iterations=iterations,
        elapsed_seconds=elapsed,
        ops_per_second=iterations / elapsed,
    )


def _json_path_lookup() -> None:
    data = {"service": {"name": "kniferpy", "limits": {"max": 42}}}
    if vjson.get_str(data, "service.name") != "kniferpy":
        raise AssertionError("json path lookup failed")
    if vjson.get_int(data, "service.limits.max") != 42:
        raise AssertionError("json integer lookup failed")


def _codec_round_trip() -> None:
    payload = b"kniferpy" * 16
    if vcodec.base64_decode(vcodec.base64_encode(payload)) != payload:
        raise AssertionError("base64 round trip failed")


def _url_normalize() -> None:
    normalized = vurl.normalize_query("https://example.com/path?z=9&a=1&b=2")
    if normalized != "https://example.com/path?a=1&b=2&z=9":
        raise AssertionError("url query normalization failed")


def _string_case_conversion() -> None:
    if vstr.to_snake_case("KniferPyHTTPClient") != "knifer_py_http_client":
        raise AssertionError("snake case conversion failed")


def main() -> int:
    iterations = int(os.environ.get("BENCH_SMOKE_ITERS", "2000"))
    if iterations <= 0:
        raise ValueError("BENCH_SMOKE_ITERS must be positive")

    benchmarks: list[tuple[str, Callable[[], None]]] = [
        ("json_path_lookup", _json_path_lookup),
        ("codec_round_trip", _codec_round_trip),
        ("url_normalize", _url_normalize),
        ("string_case_conversion", _string_case_conversion),
    ]
    results = [_bench(name, iterations, fn) for name, fn in benchmarks]
    print(json.dumps([result.__dict__ for result in results], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
