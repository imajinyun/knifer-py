from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from kniferpy import vcodec, vjson, vstr, vurl

SCHEMA_VERSION = 1
DEFAULT_BASELINE_RATIO = 0.20


@dataclass(frozen=True)
class BenchResult:
    name: str
    iterations: int
    elapsed_seconds: float
    ops_per_second: float


@dataclass(frozen=True)
class BenchReport:
    schema_version: int
    iterations: int
    python_version: str
    platform: str
    results: list[BenchResult]


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


def run_benchmarks(iterations: int) -> BenchReport:
    benchmarks: list[tuple[str, Callable[[], None]]] = [
        ("json_path_lookup", _json_path_lookup),
        ("codec_round_trip", _codec_round_trip),
        ("url_normalize", _url_normalize),
        ("string_case_conversion", _string_case_conversion),
    ]
    results = [_bench(name, iterations, fn) for name, fn in benchmarks]
    return BenchReport(
        schema_version=SCHEMA_VERSION,
        iterations=iterations,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        results=results,
    )


def report_to_dict(report: BenchReport) -> dict[str, Any]:
    return asdict(report)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _baseline_results(data: dict[str, Any]) -> dict[str, float]:
    raw_results = data.get("results", data.get("benchmarks"))
    if not isinstance(raw_results, list):
        raise ValueError("benchmark baseline must contain a results or benchmarks list")

    results: dict[str, float] = {}
    for raw in raw_results:
        if not isinstance(raw, dict):
            raise ValueError("benchmark baseline entries must be JSON objects")
        name = raw.get("name")
        ops_per_second = raw.get("ops_per_second")
        if not isinstance(name, str) or not isinstance(ops_per_second, int | float):
            raise ValueError("benchmark baseline entries need name and ops_per_second")
        if ops_per_second <= 0:
            raise ValueError(f"benchmark baseline {name!r} must have positive ops_per_second")
        results[name] = float(ops_per_second)
    return results


def compare_with_baseline(
    report: BenchReport,
    baseline: dict[str, Any],
    min_baseline_ratio: float,
) -> list[str]:
    baseline_by_name = _baseline_results(baseline)
    current_by_name = {result.name: result for result in report.results}

    errors: list[str] = []
    for name in sorted(current_by_name.keys() - baseline_by_name.keys()):
        errors.append(f"benchmark {name!r} is missing from baseline")
    for name in sorted(baseline_by_name.keys() - current_by_name.keys()):
        errors.append(f"baseline benchmark {name!r} is not produced by the smoke suite")

    for name in sorted(current_by_name.keys() & baseline_by_name.keys()):
        minimum_ops = baseline_by_name[name] * min_baseline_ratio
        actual_ops = current_by_name[name].ops_per_second
        if actual_ops < minimum_ops:
            errors.append(
                f"benchmark {name!r} is below baseline: "
                f"{actual_ops:.2f} ops/s < {minimum_ops:.2f} ops/s"
            )
    return errors


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _ratio(value: str) -> float:
    parsed = float(value)
    if parsed <= 0 or parsed > 1:
        raise argparse.ArgumentTypeError("value must be in the range (0, 1]")
    return parsed


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run kniferpy benchmark smoke checks.")
    parser.add_argument(
        "--iterations",
        type=_positive_int,
        default=_positive_int(os.environ.get("BENCH_SMOKE_ITERS", "2000")),
        help="iterations per benchmark, defaults to BENCH_SMOKE_ITERS or 2000",
    )
    parser.add_argument("--output", type=Path, help="write benchmark JSON to this path")
    parser.add_argument("--baseline", type=Path, help="compare results with this JSON baseline")
    parser.add_argument(
        "--min-baseline-ratio",
        type=_ratio,
        default=_ratio(
            os.environ.get("BENCH_SMOKE_MIN_BASELINE_RATIO", str(DEFAULT_BASELINE_RATIO))
        ),
        help="minimum allowed current/baseline ops ratio; default is 0.20",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run_benchmarks(args.iterations)
    payload = report_to_dict(report)
    output = json.dumps(payload, indent=2, sort_keys=True)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")

    print(output)

    if args.baseline is not None:
        errors = compare_with_baseline(
            report,
            _load_json(args.baseline),
            args.min_baseline_ratio,
        )
        if errors:
            print("Benchmark baseline check failed:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
