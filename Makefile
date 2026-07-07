.PHONY: install test test-cov lint format typecheck api-check taxonomy-check facade-check readme-smoke examples-smoke bench-smoke changelog build check clean

install:
	.venv/bin/poetry install --all-extras

test:
	.venv/bin/python -m pytest

test-cov:
	.venv/bin/python -m pytest --cov=kniferpy --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=95

lint:
	.venv/bin/python -m ruff check src tests

format:
	.venv/bin/python -m ruff format src tests

typecheck:
	.venv/bin/python -m mypy src tests

api-check:
	@if [ "$(UPDATE_API)" = "1" ]; then \
		.venv/bin/python scripts/check_api_snapshot.py --update; \
	else \
		.venv/bin/python scripts/check_api_snapshot.py; \
	fi

taxonomy-check:
	.venv/bin/python scripts/check_error_taxonomy.py

facade-check:
	.venv/bin/python scripts/check_facade_consistency.py

readme-smoke:
	.venv/bin/python scripts/check_readme_smoke.py

examples-smoke:
	.venv/bin/python examples/smoke.py

bench-smoke:
	.venv/bin/python scripts/benchmark_smoke.py

changelog:
	.venv/bin/python scripts/generate_changelog.py --check

build:
	.venv/bin/poetry build

check: lint typecheck api-check taxonomy-check facade-check readme-smoke examples-smoke bench-smoke test

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dist build
