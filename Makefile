.PHONY: install test test-core test-cov lint format typecheck api-check api-index taxonomy-check facade-check facade-status-check readme-smoke examples-smoke bench-smoke changelog build check-dist sbom-smoke security-audit min-deps-smoke release-workflow-check workflow-drift-check governance-summary release-ready check clean

BENCH_SMOKE_OUTPUT ?= tmp/benchmark-smoke.json
BENCH_SMOKE_BASELINE ?= api/benchmark-smoke-baseline.json

install:
	.venv/bin/poetry install --all-extras

test:
	.venv/bin/python -m pytest

test-core:
	.venv/bin/python scripts/run_core_tests.py

test-cov:
	.venv/bin/python -m pytest --cov=kniferpy --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=95

lint:
	.venv/bin/python -m ruff check src tests examples

format:
	.venv/bin/python -m ruff format src tests examples

typecheck:
	.venv/bin/python -m mypy src tests examples

api-check:
	@if [ "$(UPDATE_API)" = "1" ]; then \
		.venv/bin/python scripts/check_api_snapshot.py --update; \
	else \
		.venv/bin/python scripts/check_api_snapshot.py; \
	fi

api-index:
	.venv/bin/python scripts/check_api_snapshot.py --print-index

taxonomy-check:
	.venv/bin/python scripts/check_error_taxonomy.py

facade-check:
	.venv/bin/python scripts/check_facade_consistency.py

facade-status-check:
	.venv/bin/python scripts/check_facade_status.py

readme-smoke:
	.venv/bin/python scripts/check_readme_smoke.py

examples-smoke:
	.venv/bin/python examples/smoke.py

bench-smoke:
	@if [ "$(UPDATE_BENCH)" = "1" ]; then \
		.venv/bin/python scripts/benchmark_smoke.py --output $(BENCH_SMOKE_OUTPUT) --baseline $(BENCH_SMOKE_BASELINE) --update-baseline; \
	else \
		.venv/bin/python scripts/benchmark_smoke.py --output $(BENCH_SMOKE_OUTPUT) --baseline $(BENCH_SMOKE_BASELINE); \
	fi

changelog:
	.venv/bin/python scripts/generate_changelog.py --check

build:
	.venv/bin/poetry build

check-dist: build
	.venv/bin/python -m twine check dist/*

sbom-smoke:
	.venv/bin/python scripts/check_sbom_smoke.py

security-audit:
	.venv/bin/python scripts/check_security_audit.py

min-deps-smoke:
	.venv/bin/python scripts/check_min_deps_smoke.py

release-workflow-check:
	.venv/bin/python scripts/check_release_workflow.py

workflow-drift-check:
	.venv/bin/python scripts/check_workflow_drift.py

governance-summary:
	.venv/bin/python scripts/check_governance_summary.py

release-ready:
	.venv/bin/python scripts/check_release_ready.py

check: lint typecheck api-check taxonomy-check facade-check facade-status-check readme-smoke examples-smoke bench-smoke test

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dist build
