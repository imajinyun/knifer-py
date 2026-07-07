from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts import benchmark_smoke


def test_benchmark_smoke_writes_output_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "benchmark.json"

    assert benchmark_smoke.main(["--iterations", "1", "--output", str(output)]) == 0

    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out)
    file_payload = json.loads(output.read_text(encoding="utf-8"))
    assert file_payload == stdout_payload
    assert file_payload["schema_version"] == 1
    assert {result["name"] for result in file_payload["results"]} == {
        "codec_round_trip",
        "json_path_lookup",
        "string_case_conversion",
        "url_normalize",
    }


def test_compare_with_baseline_accepts_loose_ratio() -> None:
    report = benchmark_smoke.BenchReport(
        schema_version=1,
        iterations=1,
        python_version="3.11.0",
        platform="test",
        results=[
            benchmark_smoke.BenchResult(
                name="json_path_lookup",
                iterations=1,
                elapsed_seconds=1.0,
                ops_per_second=25.0,
            )
        ],
    )
    baseline = {"results": [{"name": "json_path_lookup", "ops_per_second": 100.0}]}

    assert benchmark_smoke.compare_with_baseline(report, baseline, min_baseline_ratio=0.20) == []


def test_compare_with_baseline_reports_missing_and_slow_results() -> None:
    report = benchmark_smoke.BenchReport(
        schema_version=1,
        iterations=1,
        python_version="3.11.0",
        platform="test",
        results=[
            benchmark_smoke.BenchResult(
                name="json_path_lookup",
                iterations=1,
                elapsed_seconds=1.0,
                ops_per_second=10.0,
            ),
            benchmark_smoke.BenchResult(
                name="new_case",
                iterations=1,
                elapsed_seconds=1.0,
                ops_per_second=100.0,
            ),
        ],
    )
    baseline = {
        "results": [
            {"name": "json_path_lookup", "ops_per_second": 100.0},
            {"name": "removed_case", "ops_per_second": 100.0},
        ]
    }

    errors = benchmark_smoke.compare_with_baseline(report, baseline, min_baseline_ratio=0.20)

    assert "benchmark 'new_case' is missing from baseline" in errors
    assert "baseline benchmark 'removed_case' is not produced by the smoke suite" in errors
    assert any(
        error.startswith("benchmark 'json_path_lookup' is below baseline") for error in errors
    )


def test_baseline_summary_reports_current_baseline_and_ratio() -> None:
    report = benchmark_smoke.BenchReport(
        schema_version=1,
        iterations=1,
        python_version="3.11.0",
        platform="test",
        results=[
            benchmark_smoke.BenchResult(
                name="json_path_lookup",
                iterations=1,
                elapsed_seconds=1.0,
                ops_per_second=50.0,
            ),
            benchmark_smoke.BenchResult(
                name="new_case",
                iterations=1,
                elapsed_seconds=1.0,
                ops_per_second=25.0,
            ),
        ],
    )
    baseline = {
        "results": [
            {"name": "json_path_lookup", "ops_per_second": 100.0},
            {"name": "removed_case", "ops_per_second": 75.0},
        ]
    }

    summary = benchmark_smoke.baseline_summary(report, baseline)

    assert summary == [
        "Benchmark baseline summary:",
        "- json_path_lookup: current=50.00 ops/s baseline=100.00 ops/s ratio=0.50",
        "- new_case: current=25.00 ops/s baseline=missing",
        "- removed_case: current=missing baseline=75.00 ops/s",
    ]


def test_write_baseline_keeps_stable_sorted_payload(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    report = benchmark_smoke.BenchReport(
        schema_version=1,
        iterations=10,
        python_version="3.11.0",
        platform="test",
        results=[
            benchmark_smoke.BenchResult(
                name="url_normalize",
                iterations=10,
                elapsed_seconds=0.5,
                ops_per_second=20.0,
            ),
            benchmark_smoke.BenchResult(
                name="codec_round_trip",
                iterations=10,
                elapsed_seconds=0.25,
                ops_per_second=40.0,
            ),
        ],
    )

    benchmark_smoke.write_baseline(path, report)

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "results": [
            {"name": "codec_round_trip", "ops_per_second": 40.0},
            {"name": "url_normalize", "ops_per_second": 20.0},
        ],
        "schema_version": 1,
    }


def test_update_baseline_mode_writes_selected_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "benchmark.json"
    baseline = tmp_path / "baseline.json"

    assert (
        benchmark_smoke.main(
            [
                "--iterations",
                "1",
                "--output",
                str(output),
                "--baseline",
                str(baseline),
                "--update-baseline",
            ]
        )
        == 0
    )

    captured = capsys.readouterr()
    assert f"updated benchmark baseline: {baseline}" in captured.out
    payload = json.loads(baseline.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert sorted(result["name"] for result in payload["results"]) == [
        "codec_round_trip",
        "json_path_lookup",
        "string_case_conversion",
        "url_normalize",
    ]
